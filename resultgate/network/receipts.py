"""Local receipt adapter contract, NOT any partner's webhook protocol.
Operator provisions keys out of band; keys are never stored. No HTTP listener or payments.
"""
import hashlib
import hmac
import json
import secrets
import time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .registry import Registry, sha, atomic

class Receipt(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,100}$')
    referral_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    outcome_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,100}$')
    kind: Literal['task', 'subscription', 'transaction']
    status: Literal['succeeded', 'failed', 'cancelled', 'refunded', 'disputed']
    value_micros: int = Field(ge=0, le=10**15)
    currency: Literal['USD']
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

class Receipts:
    def __init__(self, registry: Registry):
        self.registry = registry
        self.store = registry.store
        self.db = registry.db
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS network_referrals(id TEXT PRIMARY KEY, data TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS network_receipts(provider_id TEXT, event_id TEXT, body_hash TEXT, created REAL,
          PRIMARY KEY(provider_id,event_id));
        CREATE TABLE IF NOT EXISTS network_outcomes(provider_id TEXT, outcome_hash TEXT, referral_id TEXT, created REAL,
          PRIMARY KEY(provider_id,outcome_hash));
        ''')
        self.purge()

    def purge(self):
        cutoff = time.time()-30*86400
        self.db.execute('DELETE FROM network_referrals WHERE created<?',(cutoff,))
        self.db.execute('DELETE FROM network_receipts WHERE created<?',(cutoff,))
        self.db.execute('DELETE FROM network_outcomes WHERE created<?',(cutoff,))

    @atomic
    def refer(self, provider_id, request_sha256, kind, rule, amount, expires, internal=True):
        """Local operator freezes mutually agreed commercial rule and creates referral.
        Rule must be reviewed against written terms. No MCP caller controls this method.
        """
        self.purge()
        p = self.registry.get(provider_id); a = p['agreement']
        if p['state'] != 'approved' or not a or not a['operator_approved']:
            raise ValueError('approved provider and agreement required')
        if kind not in {'task','subscription','transaction'} or rule not in {'fixed','basis_points'}:
            raise ValueError('unsupported outcome or rule')
        if type(amount) is not int or not 0 < amount <= (10000 if rule == 'basis_points' else 10**12):
            raise ValueError('invalid agreed amount')
        if type(expires) not in {int,float} or not time.time() < expires <= time.time()+30*86400:
            raise ValueError('bounded agreement expiry required')
        if (kind,rule,amount) != (a['kind'],a['rule'],a['amount']):
            raise ValueError('commission rule differs from accepted terms')
        rid = secrets.token_hex(16)
        r = dict(id=rid, provider_id=provider_id, request_sha256=sha(request_sha256),
                 agreement_sha256=a['sha256'], kind=kind, rule=rule, amount=amount,
                 expires=expires, internal=bool(internal), independent_evidence=None,
                 acceptance_evidence=None, state='routed', commission_micros=0,
                 outcome_hash=None, evidence_sha256=None, payments_enabled=False)
        self.db.execute('INSERT INTO network_referrals VALUES(?,?,?)', (rid,json.dumps(r),time.time()))
        return r

    def get(self, rid):
        self.purge()
        row = self.db.execute('SELECT data FROM network_referrals WHERE id=?', (rid,)).fetchone()
        if not row: raise ValueError('unknown referral')
        return json.loads(row[0])

    def save(self, r):
        self.db.execute('UPDATE network_referrals SET data=? WHERE id=?', (json.dumps(r),r['id']))

    @atomic
    def attest(self, rid, acceptance_sha256, independent_sha256=None):
        """Operator review of result acceptance, distinct from provider success claim."""
        with self.store.lock:
            r = self.get(rid)
            if r['state'] != 'completed': raise ValueError('successful provider receipt required')
            r['acceptance_evidence'] = sha(acceptance_sha256)
            if independent_sha256:
                if r['internal']: raise ValueError('internal tests cannot become independent')
                r['independent_evidence'] = sha(independent_sha256)
            r['state'] = 'verified'
            self.save(r)
            return r

    def ingest(self, provider_id, body, timestamp, signature, *, key):
        """HMAC-SHA256(timestamp+'.'+raw body); 5min window, unique provider/event/outcome.
        Generic locally tested contract only. Caller must bind a provider key outside user inputs.
        """
        if not isinstance(key, bytes) or len(key)<32 or type(timestamp) is not int or abs(time.time()-timestamp)>300:
            raise ValueError('invalid key or timestamp')
        if not isinstance(body,bytes) or len(body)>8192:
            raise ValueError('bounded raw body required')
        expected=hmac.digest(key,str(timestamp).encode()+b'.'+body,'sha256').hex()
        if not isinstance(signature,str) or not hmac.compare_digest(expected,signature):
            raise ValueError('invalid signature')
        def unique(pairs):
            d={}
            for k,v in pairs:
                if k in d: raise ValueError('duplicate JSON key')
                d[k]=v
            return d
        receipt=Receipt.model_validate(json.loads(body,object_pairs_hook=unique)).model_dump()
        with self.store.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                r=self.get(receipt['referral_id'])
                if r['provider_id']!=provider_id or r['kind']!=receipt['kind']:
                    raise ValueError('provider/outcome binding mismatch')
                bh=hashlib.sha256(body).hexdigest()
                event_hash=self.store.digest(receipt['event_id'])
                prior=self.db.execute('SELECT body_hash FROM network_receipts WHERE provider_id=? AND event_id=?',
                                      (provider_id,event_hash)).fetchone()
                if prior:
                    if prior[0]!=bh: raise ValueError('conflicting event replay')
                else:
                    oh=self.store.digest(receipt['outcome_id'])
                    existing=self.db.execute('SELECT referral_id FROM network_outcomes WHERE provider_id=? AND outcome_hash=?',
                                             (provider_id,oh)).fetchone()
                    if existing and existing[0]!=r['id']: raise ValueError('outcome already attributed')
                    if r['outcome_hash'] not in (None,oh): raise ValueError('one outcome per referral')
                    self.db.execute('INSERT OR IGNORE INTO network_outcomes VALUES(?,?,?,?)',(provider_id,oh,r['id'],time.time()))
                    self.db.execute('INSERT INTO network_receipts VALUES(?,?,?,?)',(provider_id,event_hash,bh,time.time()))
                    if r['state'] in {'failed','cancelled','refunded','disputed'}:
                        raise ValueError('blocked outcome requires manual reconciliation')
                    if receipt['status']=='succeeded':
                        if r['state']!='routed': raise ValueError('success already recorded')
                        r.update(state='completed',value_micros=receipt['value_micros'],
                                 evidence_sha256=receipt['evidence_sha256'],outcome_hash=oh)
                    else:
                        r.update(state=receipt['status'],commission_micros=0,outcome_hash=oh)
                    self.save(r)
                    self.db.execute('INSERT INTO network_audit VALUES(?,?,?)',(r['id'],r['state'],time.time()))
                self.db.execute('COMMIT')
                return r
            except Exception:
                self.db.execute('ROLLBACK'); raise

    @atomic
    def assess(self, rid):
        with self.store.lock:
            r=self.get(rid); p=self.registry.get(r['provider_id']); a=p['agreement']
            if (r['state'] not in {'verified','commission_eligible'} or time.time()>r['expires']
                or p['state']!='approved' or not a or not a['operator_approved']
                or a['sha256']!=r['agreement_sha256'] or not r['acceptance_evidence']
                or (not r['internal'] and not r['independent_evidence'])):
                raise ValueError('no eligible evidence/agreement')
            r['commission_micros']=(r['amount'] if r['rule']=='fixed' else r['amount']*r['value_micros']//10000)
            r['state']='commission_eligible'
            r['mode']='simulation' if r['internal'] else 'operator_attested'
            self.save(r)
            return r

    @atomic
    def delete(self, rid):
        """Operator deletion; minimal keyed dedup tombstones retained for at most 30 days.
        No raw task/customer/outcome identifiers ever stored. See retention policy.
        """
        with self.store.lock:
            self.db.execute('DELETE FROM network_referrals WHERE id=?',(rid,))
            self.db.execute('DELETE FROM network_audit WHERE id=?',(rid,))

    def summary(self):
        self.purge()
        rows=[json.loads(row[0]) for row in self.db.execute('SELECT data FROM network_referrals')]
        def cohort(r):
            return 'internal' if r['internal'] else ('independent_verified' if r['independent_evidence'] else 'external_unverified')
        return {'referrals_by_cohort': {c:sum(cohort(r)==c for r in rows) for c in ['internal','external_unverified','independent_verified']},
                'eligible_simulations':sum(r['state']=='commission_eligible' and r['internal'] for r in rows),
                'eligible_operator_attested':sum(r['state']=='commission_eligible' and not r['internal'] for r in rows),
                'revenue_usd':0,'payments_enabled':False}
