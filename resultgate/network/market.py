"""Local simulation core for a future shared market. No transport, execution or payments.
Only the trusted local operator may construct MarketOperator; never expose it over MCP/HTTP.
"""
import hashlib
import json
import re
import secrets
import time
from .registry import Registry, atomic, sha

TRANSITIONS = {
    'matched': ('discovered', 'operator'), 'offered': ('matched', 'provider'),
    'accepted': ('offered', 'requester'), 'delegated': ('accepted', 'operator'),
    'executing': ('delegated', 'provider'), 'completed': ('executing', 'provider'),
    'verified': ('completed', 'operator'), 'transaction_proven': ('verified', 'provider'),
    'commission_eligible': ('transaction_proven', 'operator'),
}
TERMINAL = {'failed', 'cancelled', 'refunded', 'disputed'}
REQUESTS_PER_MINUTE = 120

class RequestBudgetExceeded(ValueError):
    """Authenticated tenant exhausted its shared UTC-minute request allowance."""


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', value):
        raise ValueError('bounded opaque identifier required')
    return value

class Market:
    """Token-scoped durable records; administrative methods are deliberately separate.

    All records are simulation. No assertion here proves a real transaction or legal entitlement.
    Uses an existing Registry/Store, never fetches provider endpoints or task bodies.
    """
    def __init__(self, registry: Registry):
        self.registry = registry
        self.store = registry.store
        self.db = registry.db
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS market_credentials(token_hash TEXT PRIMARY KEY, tenant_hash TEXT,
          role TEXT, provider_id TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS market_tasks(id TEXT PRIMARY KEY, tenant_hash TEXT,
          request_hash TEXT, spec_hash TEXT, data TEXT, created REAL, UNIQUE(tenant_hash,request_hash));
        CREATE TABLE IF NOT EXISTS market_outcomes(provider_id TEXT, outcome_hash TEXT, task_id TEXT, created REAL,
          PRIMARY KEY(provider_id,outcome_hash));
        CREATE TABLE IF NOT EXISTS market_request_budgets(tenant_hash TEXT, role TEXT, minute INTEGER,
          used INTEGER NOT NULL, PRIMARY KEY(tenant_hash,role,minute));
        CREATE TABLE IF NOT EXISTS market_events(task_id TEXT, event_hash TEXT, payload_hash TEXT,
          state TEXT, created REAL, PRIMARY KEY(task_id,event_hash));
        ''')

    def _auth(self, token):
        if not isinstance(token, str) or not re.fullmatch(r'[a-f0-9]{64}', token):
            raise ValueError('unauthorized')
        row = self.db.execute('SELECT tenant_hash,role,provider_id FROM market_credentials WHERE token_hash=? AND created>=?',
                              (self.store.digest(token), time.time()-30*86400)).fetchone()
        if not row: raise ValueError('unauthorized')
        return dict(tenant_hash=row[0], role=row[1], provider_id=row[2])

    @atomic
    def consume_request(self, token):
        """Shared local HTTP quota across processes/credentials; never a money budget.

        Fixed UTC-minute windows permit boundary bursts. Authenticated attempts count
        even if their operation later fails. No task body, token or IP is retained.
        The separate process-local gateway bound protects anonymous ingress only.
        """
        actor = self._auth(token)
        minute = int(time.time() // 60)
        self.db.execute('DELETE FROM market_request_budgets WHERE minute<?', (minute-1,))
        key = (actor['tenant_hash'], actor['role'], minute)
        self.db.execute('INSERT OR IGNORE INTO market_request_budgets VALUES(?,?,?,0)', key)
        used = self.db.execute('SELECT used FROM market_request_budgets WHERE tenant_hash=? AND role=? AND minute=?', key).fetchone()[0]
        if used >= REQUESTS_PER_MINUTE:
            raise RequestBudgetExceeded('tenant request budget exhausted')
        self.db.execute('UPDATE market_request_budgets SET used=used+1 WHERE tenant_hash=? AND role=? AND minute=?', key)
        return {'remaining_requests': REQUESTS_PER_MINUTE-used-1, 'window_seconds': 60}

    def _load(self, task_id):
        identifier(task_id)
        row = self.db.execute('SELECT data FROM market_tasks WHERE id=? AND created>=?',
                              (task_id, time.time()-30*86400)).fetchone()
        if not row: raise ValueError('unknown or inaccessible task')
        task = json.loads(row[0])
        if task.get('deleted'): raise ValueError('unknown or inaccessible task')
        return task

    @staticmethod
    def _authorize(actor, task):
        if actor['role'] == 'requester' and actor['tenant_hash'] == task['tenant_hash']: return
        if actor['role'] == 'provider' and actor['provider_id'] == task['provider_id']: return
        raise ValueError('unknown or inaccessible task')

    @staticmethod
    def _public(task, role=None):
        hidden={'tenant_hash','request_hash'}
        if role=='provider' and not task.get('data_send_consent'):
            hidden.update({'task_sha256','success_criteria_sha256'})
        return {k: v for k, v in task.items() if k not in hidden}

    def get(self, token, task_id):
        actor = self._auth(token); task = self._load(task_id); self._authorize(actor, task)
        return self._public(task,actor['role'])

    @atomic
    def create(self, token, request_id, task_sha256, success_criteria_sha256):
        actor = self._auth(token)
        if actor['role'] != 'requester': raise ValueError('requester required')
        request_hash = self.store.digest(identifier(request_id))
        spec_hash = hashlib.sha256((sha(task_sha256)+sha(success_criteria_sha256)).encode()).hexdigest()
        prior = self.db.execute('SELECT spec_hash,data,created FROM market_tasks WHERE tenant_hash=? AND request_hash=?',
                                (actor['tenant_hash'], request_hash)).fetchone()
        if prior:
            if prior[2] < time.time()-30*86400: raise ValueError('expired request; purge required before reuse')
            if prior[0] != spec_hash: raise ValueError('idempotency conflict')
            old = json.loads(prior[1])
            if old.get('deleted'): raise ValueError('deleted request; do not replay')
            return dict(self._public(old), duplicate=True)
        if self.db.execute('SELECT count(*) FROM market_tasks WHERE tenant_hash=?',(actor['tenant_hash'],)).fetchone()[0]>=1000:
            raise ValueError('tenant simulation capacity reached')
        if self.db.execute('SELECT count(*) FROM market_tasks').fetchone()[0] >= 10000:
            raise ValueError('simulation capacity reached')
        t = dict(id=secrets.token_hex(16), tenant_hash=actor['tenant_hash'], request_hash=request_hash,
                 state='discovered', provider_id=None, task_sha256=task_sha256,
                 success_criteria_sha256=success_criteria_sha256, mode='simulation',
                 external_dispatch=False, payments_enabled=False, actual_commission_micros=0,
                 simulated_commission_micros=0, agreement_sha256=None)
        self.db.execute('INSERT INTO market_tasks VALUES(?,?,?,?,?,?)',
                        (t['id'], actor['tenant_hash'], request_hash, spec_hash, json.dumps(t), time.time()))
        return dict(self._public(t), duplicate=False)

    @atomic
    def advance(self, token, task_id, event_id, state, *, evidence_sha256=None,
                consent_to_send=False, max_cost_micros=0, simulated_value_micros=0, simulated_transaction_id_sha256=None):
        actor = self._auth(token); t = self._load(task_id); self._authorize(actor,t)
        result=self._advance(t, actor['role'], event_id, state, evidence_sha256=evidence_sha256,
                             consent_to_send=consent_to_send, max_cost_micros=max_cost_micros,
                             simulated_value_micros=simulated_value_micros,
                             simulated_transaction_id_sha256=simulated_transaction_id_sha256)
        return self._public(result,actor['role'])

    def _advance(self, t, role, event_id, state, *, evidence_sha256=None, consent_to_send=False,
                 max_cost_micros=0, simulated_value_micros=0, simulated_transaction_id_sha256=None):
        identifier(event_id)
        if type(max_cost_micros) is not int or max_cost_micros != 0:
            raise ValueError('only zero-cost simulation supported; no spending authorization')
        if type(consent_to_send) is not bool or type(simulated_value_micros) is not int or not 0 <= simulated_value_micros <= 10**15:
            raise ValueError('invalid consent or simulated amount')
        if evidence_sha256 is not None: sha(evidence_sha256)
        if simulated_transaction_id_sha256 is not None: sha(simulated_transaction_id_sha256)
        payload = dict(state=state, role=role, evidence=evidence_sha256, consent=consent_to_send,
                       max_cost=max_cost_micros, value=simulated_value_micros, transaction=simulated_transaction_id_sha256)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        event_hash = self.store.digest(event_id)
        prior = self.db.execute('SELECT payload_hash FROM market_events WHERE task_id=? AND event_hash=?',
                               (t['id'],event_hash)).fetchone()
        if prior:
            if prior[0] != digest: raise ValueError('event replay conflict')
            return dict(self._public(t), duplicate=True)
        if t['state'] in TERMINAL: raise ValueError('terminal task requires separate reviewed reconciliation')
        if state in {'failed','cancelled'}:
            if t['state'] in {'completed','verified','transaction_proven','commission_eligible'}:
                raise ValueError('completed work requires refund or dispute')
            if state == 'failed' and role not in {'provider','operator'}: raise ValueError('provider/operator required')
        elif state in {'refunded','disputed'}:
            if role != 'operator' or t['state'] not in {'completed','verified','transaction_proven','commission_eligible'}:
                raise ValueError('operator-reviewed outcome reversal required')
            if evidence_sha256 is None: raise ValueError('reversal evidence required')
        else:
            expected = TRANSITIONS.get(state)
            if expected != (t['state'], role): raise ValueError('unauthorized or invalid transition')
            if state in {'offered','completed','verified','transaction_proven'} and evidence_sha256 is None:
                raise ValueError('evidence commitment required')
            if state == 'accepted' and not consent_to_send: raise ValueError('explicit data-send consent required')
            if state == 'transaction_proven' and (simulated_value_micros <= 0 or simulated_transaction_id_sha256 is None):
                raise ValueError('positive simulated transaction and canonical transaction identity commitment required')
        if t['provider_id']:
            provider = self.registry.get(t['provider_id'])
            if state not in TERMINAL and provider['state'] != 'approved': raise ValueError('provider no longer approved')
        if state == 'accepted': t['data_send_consent'] = True
        if state == 'offered': t['offer_sha256'] = evidence_sha256
        if state == 'completed': t['result_sha256'] = evidence_sha256
        if state == 'verified': t['verification_sha256'] = evidence_sha256
        if state == 'transaction_proven':
            outcome=self.db.execute('SELECT task_id FROM market_outcomes WHERE provider_id=? AND outcome_hash=?',
                                    (t['provider_id'],simulated_transaction_id_sha256)).fetchone()
            if outcome and outcome[0]!=t['id']: raise ValueError('simulated transaction already attributed')
            self.db.execute('INSERT OR IGNORE INTO market_outcomes VALUES(?,?,?,?)',
                            (t['provider_id'],simulated_transaction_id_sha256,t['id'],time.time()))
            t['simulated_transaction_id_sha256'] = simulated_transaction_id_sha256
            t['simulated_transaction_evidence_sha256'] = evidence_sha256
            t['simulated_value_micros'] = simulated_value_micros
        if state == 'commission_eligible':
            a = provider.get('agreement') or {}
            if not a.get('operator_approved') or not a.get('provider_accepted') or a.get('sha256') != t['agreement_sha256']:
                raise ValueError('unchanged separately accepted agreement required')
            t['simulated_commission_micros'] = a['amount'] if a['rule']=='fixed' else a['amount']*t['simulated_value_micros']//10000
        if state in TERMINAL: t['simulated_commission_micros'] = 0
        t['state'] = state
        self.db.execute('UPDATE market_tasks SET data=? WHERE id=?',(json.dumps(t),t['id']))
        self.db.execute('INSERT INTO market_events VALUES(?,?,?,?,?)',(t['id'],event_hash,digest,state,time.time()))
        return dict(self._public(t), duplicate=False)

    @atomic
    def delete(self, token, task_id):
        actor=self._auth(token); t=self._load(task_id); self._authorize(actor,t)
        if actor['role']!='requester': raise ValueError('requester deletion required')
        tombstone={'id':t['id'],'deleted':True,'mode':'simulation'}
        self.db.execute('UPDATE market_tasks SET data=? WHERE id=?',(json.dumps(tombstone),task_id))
        self.db.execute('DELETE FROM market_events WHERE task_id=?',(task_id,))
        return {'deleted':True,'dedup_retention_days':30}

class MarketOperator:
    """Trusted LOCAL administration, not a remote authorization mechanism or MCP tool."""
    def __init__(self, market):
        self.market=market; self.store=market.store; self.db=market.db

    @atomic
    def issue_credential(self, tenant_id, role='requester', provider_id=None):
        identifier(tenant_id)
        if role not in {'requester','provider'}: raise ValueError('unsupported role')
        if role=='provider':
            p=self.market.registry.get(identifier(provider_id))
            if p['state']!='approved': raise ValueError('reviewed provider required')
        elif provider_id is not None: raise ValueError('requester cannot claim provider')
        if self.db.execute('SELECT count(*) FROM market_credentials').fetchone()[0]>=1000:
            raise ValueError('credential capacity reached')
        token=secrets.token_hex(32)
        self.db.execute('INSERT INTO market_credentials VALUES(?,?,?,?,?)',
                        (self.store.digest(token),self.store.digest(tenant_id),role,provider_id,time.time()))
        return token

    @atomic
    def revoke(self, token):
        self.db.execute('DELETE FROM market_credentials WHERE token_hash=?',(self.store.digest(token),))

    @atomic
    def match(self, task_id, provider_id, event_id):
        t=self.market._load(task_id); p=self.market.registry.get(identifier(provider_id))
        if p['state']!='approved': raise ValueError('reviewed provider required')
        if t['provider_id'] not in (None,provider_id): raise ValueError('provider binding is immutable')
        if t['provider_id'] is not None:
            return self.market._advance(t,'operator',event_id,'matched')
        t['provider_id']=provider_id
        t['agreement_sha256']=(p.get('agreement') or {}).get('sha256')
        return self.market._advance(t,'operator',event_id,'matched')

    @atomic
    def advance(self, task_id, event_id, state, *, evidence_sha256=None):
        return self.market._advance(self.market._load(task_id),'operator',event_id,state,evidence_sha256=evidence_sha256)

    @atomic
    def purge(self):
        """Explicit 30-day simulation retention; idempotency is guaranteed only within this window."""
        cutoff=time.time()-30*86400
        self.db.execute('DELETE FROM market_request_budgets WHERE minute<?',(int(time.time()//60)-1,))
        self.db.execute('DELETE FROM market_events WHERE task_id IN (SELECT id FROM market_tasks WHERE created<?)',(cutoff,))
        self.db.execute('DELETE FROM market_tasks WHERE created<?',(cutoff,))
        self.db.execute('DELETE FROM market_credentials WHERE created<?',(cutoff,))
        self.db.execute('DELETE FROM market_outcomes WHERE created<?',(cutoff,))
