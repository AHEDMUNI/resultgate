"""Operator-only, durable double-entry SIMULATION. No payment SDK or real receivable."""
import json
import time
from .registry import atomic


class SettlementSandbox:
    """Evaluate routes A/B against eligible simulated market tasks, never real money.

    Route A records only hypothetical commission. Route B models fees deducted
    from the provider share. It is not a Stripe/x402 integration or legal ledger.
    Filesystem owner is trusted; never expose this class through HTTP or MCP.
    """
    def __init__(self, market):
        self.market = market
        self.store = market.store
        self.db = market.db
        self.db.execute('''CREATE TABLE IF NOT EXISTS settlement_simulations(
            task_id TEXT, kind TEXT, route TEXT, fee_micros INTEGER,
            postings TEXT, created REAL, PRIMARY KEY(task_id,kind))''')

    @atomic
    def accrue(self, task_id, *, route='direct', fee_micros=0):
        if route not in {'direct', 'marketplace'} or type(fee_micros) is not int or fee_micros < 0:
            raise ValueError('explicit supported simulation economics required')
        if route == 'direct' and fee_micros:
            raise ValueError('direct route does not process customer payment')
        task = self.market._load(task_id)
        if task.get('mode') != 'simulation' or task.get('payments_enabled') is not False or task.get('actual_commission_micros') != 0:
            raise ValueError('simulation-only ledger')
        if task['state'] != 'commission_eligible':
            raise ValueError('eligible simulated transaction required')
        provider = self.market.registry.get(task['provider_id'])
        agreement = provider.get('agreement') or {}
        if (provider['state'] != 'approved' or not agreement.get('operator_approved')
                or not agreement.get('provider_accepted') or agreement.get('sha256') != task['agreement_sha256']):
            raise ValueError('current unchanged accepted agreement required')
        value = task['simulated_value_micros']
        commission = task['simulated_commission_micros']
        expected = agreement['amount'] if agreement['rule'] == 'fixed' else agreement['amount'] * value // 10000
        if type(commission) is not int or commission <= 0 or commission != expected:
            raise ValueError('invalid simulated commission')
        if route == 'marketplace' and fee_micros + commission > value:
            raise ValueError('fees and commission exceed transaction')
        prior = self.db.execute("SELECT route,fee_micros FROM settlement_simulations WHERE task_id=? AND kind='accrual'", (task_id,)).fetchone()
        if prior:
            if prior != (route, fee_micros):
                raise ValueError('simulation economics replay conflict')
            return {'duplicate': True, 'mode': 'simulation'}
        if self.db.execute('SELECT count(*) FROM settlement_simulations').fetchone()[0] >= 20000:
            raise ValueError('sandbox capacity reached')
        if route == 'direct':
            postings = {'hypothetical_commission_receivable': commission, 'hypothetical_commission_income': -commission}
        else:
            postings = {'hypothetical_customer_clearing': value,
                        'hypothetical_provider_payable': -(value - commission - fee_micros),
                        'hypothetical_commission_income': -commission,
                        'hypothetical_processor_payable': -fee_micros}
        self.db.execute('INSERT INTO settlement_simulations VALUES(?,?,?,?,?,?)',
                        (task_id, 'accrual', route, fee_micros, json.dumps(postings, sort_keys=True), time.time()))
        return {'duplicate': False, 'mode': 'simulation'}

    @atomic
    def reverse(self, task_id):
        task = self.market._load(task_id)
        if task['state'] not in {'refunded', 'disputed', 'cancelled', 'failed'}:
            raise ValueError('reviewed reversal state required')
        prior = self.db.execute("SELECT route,fee_micros,postings FROM settlement_simulations WHERE task_id=? AND kind='accrual'", (task_id,)).fetchone()
        if not prior:
            raise ValueError('no simulation to reverse')
        reversed_postings = {k: -v for k, v in json.loads(prior[2]).items()}
        cursor = self.db.execute('INSERT OR IGNORE INTO settlement_simulations VALUES(?,?,?,?,?,?)',
                                (task_id, 'reversal', prior[0], prior[1], json.dumps(reversed_postings, sort_keys=True), time.time()))
        return {'duplicate': cursor.rowcount == 0, 'mode': 'simulation'}

    @atomic
    def report(self):
        """Aggregate only; current blocked eligibility is separate from historical postings."""
        totals = {}
        rows = self.db.execute('SELECT task_id,kind,postings FROM settlement_simulations').fetchall()
        for _, _, raw in rows:
            for account, amount in json.loads(raw).items():
                totals[account] = totals.get(account, 0) + amount
        pending_review = 0
        reversed_ids = {tid for tid, kind, _ in rows if kind == 'reversal'}
        for tid, kind, _ in rows:
            if kind != 'accrual' or tid in reversed_ids:
                continue
            try:
                t = self.market._load(tid)
                p = self.market.registry.get(t['provider_id'])
                a = p.get('agreement') or {}
                valid = (t['state'] == 'commission_eligible' and p['state'] == 'approved'
                         and a.get('sha256') == t['agreement_sha256']
                         and a.get('provider_accepted') and a.get('operator_approved'))
            except ValueError:
                valid = False
            pending_review += not valid
        return {'mode': 'simulation', 'currency': 'USD', 'unit': 'microUSD',
                'postings': totals, 'balanced': sum(totals.values()) == 0,
                'unreconciled_or_blocked': pending_review, 'entries': len(rows),
                'payments_enabled': False, 'real_debt_created': False, 'revenue_verified': False,
                'warning': 'Hypothetical allocations only. Refund simulation reverses all postings; actual processor fees may not be refundable.'}

    @atomic
    def purge(self):
        """Local 30-day sandbox retention; not adequate for production accounting."""
        self.db.execute('DELETE FROM settlement_simulations WHERE task_id IN '
                        '(SELECT task_id FROM settlement_simulations WHERE kind=? AND created<?)',
                        ('accrual', time.time() - 30 * 86400))
