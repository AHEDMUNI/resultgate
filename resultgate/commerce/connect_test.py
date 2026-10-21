"""Local operator-only Connect sandbox. No public endpoints or live switch.

Account links are credentials: deliver only to the authenticated provider, never log.
Processor objects are reduced to IDs/status/amounts; no identity/card data is stored.
"""
import json
import re
import time
from urllib.parse import urlsplit
from .core import CommerceOperator, fee, hashed


class ConnectTest:
    def __init__(self, commerce, stripe):
        self.c, self.stripe, self.db = commerce, stripe, commerce.db
        self.db.execute('CREATE TABLE IF NOT EXISTS commerce_test_operations (key TEXT PRIMARY KEY, digest TEXT, created REAL, result TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS commerce_test_accounts (provider TEXT PRIMARY KEY, account TEXT UNIQUE)')
        self.db.execute('CREATE TABLE IF NOT EXISTS commerce_test_account_imports (provider TEXT PRIMARY KEY, account TEXT UNIQUE)')
        self.db.execute('CREATE TABLE IF NOT EXISTS commerce_test_reports (digest TEXT PRIMARY KEY, created REAL, data TEXT)')

    def object(self, resource, object_id, prefix):
        if not isinstance(object_id, str) or not re.fullmatch(prefix+r'_[A-Za-z0-9]+', object_id):
            raise ValueError('invalid Stripe object ID')
        obj = self.stripe.request('GET', '/v1/'+resource+'/'+object_id)
        if obj.get('id') != object_id or obj.get('livemode') is True or (resource != 'refunds' and obj.get('livemode') is not False):
            raise ValueError('matching test object required')
        return obj

    def operation(self, key, payload, call):
        digest = hashed(payload)
        # Persist before network I/O: ambiguous timeouts cannot reset the retry window.
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO commerce_test_operations VALUES(?,?,?,NULL)', (key,digest,time.time()))
        row = self.db.execute('SELECT digest,created,result FROM commerce_test_operations WHERE key=?',(key,)).fetchone()
        if row[0] != digest: raise ValueError('operation key conflict')
        if row[2] is not None: return json.loads(row[2])
        if time.time()-row[1] > 23*3600:
            raise ValueError('ambiguous operation expired; inspect Stripe before retry, never use a new key')
        result = call()
        with self.db:
            self.db.execute('UPDATE commerce_test_operations SET result=? WHERE key=?',(json.dumps(result),key))
        return result

    def create_account(self, provider_id):
        p = self.c.load('providers',provider_id)
        if p['live_agreement'] or p['mode'] != 'test': raise ValueError('sandbox application required')
        row = self.db.execute('SELECT account FROM commerce_test_accounts WHERE provider=?',(provider_id,)).fetchone()
        if row: return {'account':row[0],'mode':'test'}
        if p['account']: raise ValueError('provider already bound; do not replace account')
        key = 'rg-connect-test-'+provider_id
        payload = {'type':'express','country':'US','capabilities[card_payments][requested]':'true',
                   'capabilities[transfers][requested]':'true','metadata[resultgate_provider]':provider_id}
        def create():
            a = self.stripe.request('POST','/v1/accounts',payload,key)
            if not re.fullmatch(r'acct_[A-Za-z0-9]+',a.get('id','')) or a.get('country') != 'US':
                raise ValueError('unexpected connected account')
            # Accounts v1 does not expose livemode; test-only key fixes the namespace.
            return {'account':a['id'],'mode':'test'}
        result = self.operation(key,payload,create)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO commerce_test_accounts VALUES(?,?)',(provider_id,result['account']))
        return result

    def adopt_account(self, provider_id, account_id):
        """Explicit local operator binding of an existing sandbox account; no creation."""
        p = self.c.load('providers', provider_id)
        if p['mode'] != 'test' or p['live_agreement'] or not re.fullmatch(r'acct_[A-Za-z0-9]+', account_id):
            raise ValueError('test provider and account required')
        a = self.stripe.request('GET', '/v1/accounts/'+account_id)
        if (a.get('id') != account_id or a.get('country') != 'US' or a.get('type') != 'express'
            or a.get('metadata',{}).get('resultgate_provider') not in (None, provider_id)):
            raise ValueError('existing account binding conflict')
        existing = self.db.execute('SELECT provider,account FROM commerce_test_accounts WHERE provider=? OR account=?', (provider_id,account_id)).fetchall()
        if any(row != (provider_id,account_id) for row in existing) or p['account'] not in (None,account_id):
            raise ValueError('account already assigned; no replacement allowed')
        providers = self.db.execute('SELECT data FROM commerce_providers WHERE id<>?', (provider_id,)).fetchall()
        if any(json.loads(row[0]).get('account') == account_id for row in providers):
            raise ValueError('account already assigned to another provider')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO commerce_test_accounts VALUES(?,?)',(provider_id,account_id))
            self.db.execute('INSERT OR IGNORE INTO commerce_test_account_imports VALUES(?,?)',(provider_id,account_id))
        return {'account':account_id,'mode':'test','imported':True,'approved':False}

    def account(self, provider_id):
        self.c.load('providers',provider_id)
        row = self.db.execute('SELECT account FROM commerce_test_accounts WHERE provider=?',(provider_id,)).fetchone()
        if not row: raise ValueError('create sandbox account first')
        a = self.stripe.request('GET','/v1/accounts/'+row[0])
        imported = self.db.execute('SELECT 1 FROM commerce_test_account_imports WHERE provider=? AND account=?',(provider_id,row[0])).fetchone()
        marker = a.get('metadata',{}).get('resultgate_provider')
        if a.get('id') != row[0] or a.get('country') != 'US' or (marker != provider_id and not (imported and marker is None)):
            raise ValueError('account binding mismatch')
        return a

    def onboarding_link(self, provider_id):
        a = self.account(provider_id)
        result = self.stripe.request('POST','/v1/account_links',{'account':a['id'],'type':'account_onboarding',
            'return_url':self.stripe.origin+'/commerce/return','refresh_url':self.stripe.origin+'/commerce/cancel'})
        u = urlsplit(result.get('url',''))
        if u.scheme != 'https' or u.netloc != 'connect.stripe.com' or result.get('expires_at',0) <= time.time():
            raise ValueError('invalid onboarding link')
        return {'url':result['url'],'expires_at':result['expires_at'],'mode':'test',
                'note':'Private single-use URL. Return is not approval; operator must refresh status. Expired links require regeneration.'}

    def review(self, provider_id, evidence_sha):
        a = self.account(provider_id)
        ready = (a.get('details_submitted') is True and a.get('charges_enabled') is True
                 and a.get('payouts_enabled') is True and a.get('capabilities',{}).get('transfers') == 'active'
                 and not a.get('requirements',{}).get('disabled_reason'))
        if not ready: raise ValueError('Stripe sandbox requirements incomplete')
        return CommerceOperator(self.c).review_provider(provider_id,a['id'],evidence_sha)

    def payment(self, order_id):
        o = self.c.load('orders',order_id)
        row = self.db.execute('SELECT id,gross,refunded FROM commerce_payments WHERE order_id=?',(order_id,)).fetchone()
        if not row: raise ValueError('signed payment confirmation required first')
        pi = self.object('payment_intents',row[0],'pi')
        if (pi.get('status') != 'succeeded' or pi.get('amount') != o['amount'] or pi.get('currency') != 'usd'
            or pi.get('metadata',{}).get('order_id') != order_id
            or pi.get('transfer_data',{}).get('destination') != o['account']
            or pi.get('application_fee_amount') != o['fee']):
            raise ValueError('payment binding mismatch')
        ch = self.object('charges',pi.get('latest_charge'),'ch')
        if (ch.get('payment_intent') != pi['id'] or ch.get('amount') != o['amount']
            or ch.get('currency') != 'usd' or ch.get('paid') is not True or ch.get('captured') is not True):
            raise ValueError('charge binding mismatch')
        return o,row,pi,ch

    def refund(self, order_id, cumulative_cents):
        # Cumulative target, not increment: repeated requests cannot refund twice.
        fee(cumulative_cents)
        if cumulative_cents <= 0: raise ValueError('positive refund target required')
        o,row,pi,ch = self.payment(order_id)
        if cumulative_cents > o['amount'] or ch.get('disputed'): raise ValueError('refund requires manual dispute review')
        key = 'rg-refund-test-'+order_id+'-'+str(cumulative_cents)
        def issue():
            current = ch['amount_refunded']
            if cumulative_cents <= current: return {'mode':'test','already_refunded':True,'target_cents':cumulative_cents}
            pending = self.db.execute('SELECT key,result FROM commerce_test_operations WHERE key LIKE ? AND key<>?',('rg-refund-test-'+order_id+'-%',key)).fetchall()
            for _, result in pending:
                if result is None: raise ValueError('earlier refund outcome unknown; reconcile first')
                previous = json.loads(result)
                if previous.get('refund_id'):
                    r = self.object('refunds',previous['refund_id'],'re')
                    if r.get('status') != 'succeeded': raise ValueError('prior refund not successful; manual reconciliation required')
            r = self.stripe.request('POST','/v1/refunds',{'payment_intent':pi['id'],
                'amount':str(cumulative_cents-current),'reverse_transfer':'true','refund_application_fee':'true'},key)
            if (r.get('livemode') is True or r.get('payment_intent') != pi['id']
                or r.get('amount') != cumulative_cents-current or r.get('currency') != 'usd'
                or not re.fullmatch(r're_[A-Za-z0-9]+',r.get('id',''))):
                raise ValueError('refund response mismatch; reconcile before retry')
            return {'refund_id':r['id'],'status':r['status'],'mode':'test','target_cents':cumulative_cents}
        # Freeze original refund delta across ambiguous network retries.
        previous = self.db.execute('SELECT result FROM commerce_test_operations WHERE key=?',(key,)).fetchone()
        if previous and previous[0] is None:
            raise ValueError('ambiguous refund; reconcile Stripe result before retry')
        return self.operation(key,{'order':order_id,'target':cumulative_cents},issue)

    def reconcile(self, order_id):
        o,row,pi,ch = self.payment(order_id)
        app = self.object('application_fees',ch.get('application_fee'),'fee')
        transfer = self.object('transfers',ch.get('transfer'),'tr')
        bt = self.stripe.request('GET','/v1/balance_transactions/'+self.valid_balance(ch.get('balance_transaction')))
        if (app.get('charge') != ch['id'] or app.get('account') != o['account'] or app.get('currency') != 'usd'
            or transfer.get('source_transaction') != ch['id'] or transfer.get('destination') != o['account']
            or transfer.get('currency') != 'usd' or bt.get('source') != ch['id'] or bt.get('currency') != 'usd'
            or bt.get('id') != ch['balance_transaction']):
            raise ValueError('settlement object binding mismatch')
        for value in (ch['amount_refunded'],app['amount'],app['amount_refunded'],transfer['amount'],transfer['amount_reversed']): fee(value)
        net_fee = app['amount']-app['amount_refunded']
        findings = []
        for ok, label in ((app['amount']==o['fee'],'original_application_fee'),
                          (row[2]==ch['amount_refunded'],'refund_webhook_sync'),
                          (net_fee==o['commission_cents'],'commission_rounding_or_adjustment'),
                          (transfer['amount']==o['amount'],'transfer_gross'),
                          (transfer['amount_reversed']==ch['amount_refunded'],'transfer_reversal'),
                          (not ch.get('disputed'),'dispute_requires_review')):
            if not ok: findings.append(label)
        for (raw,) in self.db.execute('SELECT result FROM commerce_test_operations WHERE key LIKE ?',('rg-refund-test-'+order_id+'-%',)):
            if raw is None: findings.append('ambiguous_refund'); continue
            r = json.loads(raw)
            if r.get('refund_id') and self.object('refunds',r['refund_id'],'re').get('status') != 'succeeded': findings.append('refund_not_succeeded')
        report = {'mode':'test','order_id':order_id,'payment_intent':pi['id'],'charge':ch['id'],
            'application_fee':app['id'],'transfer':transfer['id'],'balance_transaction':bt['id'],
            'gross_cents':o['amount'],'refunded_cents':ch['amount_refunded'],'net_commission_cents':net_fee,
            'provider_net_before_costs_cents':transfer['amount']-transfer['amount_reversed']-net_fee,
            'original_charge_processing_fee_cents':bt['fee'],'balance_status':bt['status'],
            'matched':not findings,'findings':findings,'bank_payout_verified':False,'settlement_confirmed':False,
            'real_revenue_cents':0,'note':'Stripe test object reconciliation only; no bank payout or complete net-profit proof.'}
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO commerce_test_reports VALUES(?,?,?)',(hashed(report),time.time(),json.dumps(report)))
        return report

    @staticmethod
    def valid_balance(value):
        if not isinstance(value,str) or not re.fullmatch(r'txn_[A-Za-z0-9]+',value): raise ValueError('invalid balance ID')
        return value
