"""Persisted at-most-once dispatch and evidence-gated eligibility. Never moves money."""
import hashlib
import json
import re
import secrets
import time
from .providers import validate, verify, GrobidAdapter
from .store import Store
from resultgate.brokerage.transport import ProviderFailure

def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def evidence(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value): raise ValueError('evidence SHA256 required')
    return value

class Delegator:
    def __init__(self,directory=None,allow_network=False,internal=False,adapter=None):
        self.store=Store(directory)
        self.allow_network=allow_network
        self.cohort='internal' if internal else 'external_unverified'
        self.adapter=adapter or GrobidAdapter()
    def plan(self,spec,request_id):
        task=validate(spec)
        if not isinstance(request_id,str) or not re.fullmatch('[A-Za-z0-9_-]{1,128}',request_id): raise ValueError('opaque request ID required')
        self.store.purge()
        digest=self.store.digest(canonical(task.model_dump()))
        key=self.store.digest(request_id)
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                row=self.store.db.execute('SELECT id FROM tasks WHERE request_hash=?',(key,)).fetchone()
                if row:
                    existing=self.store.get(row[0])
                    if existing['spec_hash']!=digest: raise ValueError('request ID conflict')
                    self.store.db.execute('COMMIT');return existing
                if self.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0]>=10000: raise ValueError('retention capacity reached')
                obj={'id':secrets.token_hex(16),'provider':'grobid_demo','state':'discovered','cohort':self.cohort,
                     'spec_hash':digest,'result_hash':None,'result_accepted':False,'acceptance_evidence':None,
                     'referral_documented':True,'commission_mode':None,'commission_micros':0,'error':None}
                self.store.db.execute('INSERT INTO tasks VALUES (?,?,?,?)',(obj['id'],key,canonical(obj),time.time()))
                self.store.event(obj,'discovered');self.store.event(obj,'routed')
                self.store.db.execute('COMMIT');return obj
            except Exception:
                self.store.db.execute('ROLLBACK');raise
    def status(self,task_id):
        self.store.purge()
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                obj=self.store.get(task_id)
                if obj['state'] in {'dispatching','cancel_requested'} and time.time()>obj.get('deadline',0):
                    self.store.event(obj,'outcome_unknown')
                self.store.db.execute('COMMIT');return obj
            except Exception:
                self.store.db.execute('ROLLBACK');raise
    def execute(self,task_id,spec,consent=False):
        if not self.allow_network or consent is not True: raise ValueError('operator and caller disclosure consent required')
        parsed=validate(spec)
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                obj=self.store.get(task_id)
                if obj['spec_hash']!=self.store.digest(canonical(parsed.model_dump())): raise ValueError('task changed after routing')
                if obj['state']!='routed':
                    self.store.db.execute('COMMIT');return {'task':obj,'duplicate':True,'result':None}
                obj['deadline']=time.time()+60
                self.store.event(obj,'dispatching')
                self.store.db.execute('COMMIT')
            except Exception:
                self.store.db.execute('ROLLBACK');raise
        result=None; failure=None
        try:
            result=self.adapter.execute(parsed)
            passed=verify(parsed,result)
        except ProviderFailure as exc: failure=exc.code
        except Exception: failure='adapter_error'
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                obj=self.store.get(task_id)
                if obj['state']=='cancel_requested':
                    self.store.event(obj,'cancelled');result=None
                elif obj['state']!='dispatching': result=None
                elif failure:
                    obj['error']=failure
                    self.store.event(obj,'outcome_unknown' if failure in {'timeout','connection_error'} else 'failed')
                elif time.time()>obj['deadline']:
                    self.store.event(obj,'outcome_unknown');result=None
                else:
                    # Synchronous provider gives no early ack. These events are observed retrospectively.
                    for state in ['accepted','executing','completed']: self.store.event(obj,state)
                    obj['result_hash']=hashlib.sha256(canonical(result).encode()).hexdigest()
                    obj['criteria_passed']=passed
                    self.store.event(obj,'verified' if passed else 'failed')
                self.store.db.execute('COMMIT')
            except Exception:
                self.store.db.execute('ROLLBACK');raise
        return {'task':obj,'duplicate':False,'result':result}
    def block(self,task_id,reason):
        if reason not in {'cancelled','disputed','refunded'}: raise ValueError('unsupported block reason')
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                obj=self.store.get(task_id)
                if obj['state'] in {'cancelled','disputed','refunded'}: raise ValueError('already blocked; operator reconciliation required')
                state='cancel_requested' if reason=='cancelled' and obj['state']=='dispatching' else reason
                self.store.event(obj,state)
                self.store.db.execute("UPDATE commissions SET status='void' WHERE task_id=?",(task_id,))
                self.store.db.execute('COMMIT');return obj
            except Exception:
                self.store.db.execute('ROLLBACK');raise
    # The following methods are trusted local operator APIs, NEVER exposed as MCP tools.
    def attest_independent(self,task_id,proof):
        evidence(proof)
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                obj=self.store.get(task_id)
                if obj['cohort']=='internal': raise ValueError('internal tests cannot become independent use')
                obj['cohort']='independent_verified';obj['cohort_evidence']=proof;self.store.save(obj)
                self.store.db.execute('COMMIT')
            except Exception:
                self.store.db.execute('ROLLBACK');raise
    def accept_result(self,task_id,result_hash,proof):
        evidence(proof)
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                obj=self.store.get(task_id)
                if obj['state'] not in {'verified','commission_eligible'} or obj['result_hash']!=result_hash: raise ValueError('verified result mismatch')
                obj['result_accepted']=True;obj['acceptance_evidence']=proof;self.store.save(obj)
                self.store.db.execute('COMMIT')
            except Exception:
                self.store.db.execute('ROLLBACK');raise
    def agreement(self,agreement_id,provider,mode,kind,amount,provider_acceptance_sha,expires):
        evidence(provider_acceptance_sha)
        if not re.fullmatch('[A-Za-z0-9_-]{1,80}',agreement_id): raise ValueError('opaque agreement ID required')
        if mode not in {'simulation','operator_attested'} or provider not in {'grobid_demo','claix_a2a'}:
            raise ValueError('unsupported agreement')
        if mode=='operator_attested' and provider=='grobid_demo':
            raise ValueError('demo-only provider cannot have a commercial agreement in this pilot')
        if kind not in {'fixed','basis_points'} or type(amount) is not int or not 0<amount<=1000000000 or (kind=='basis_points' and amount>10000): raise ValueError('invalid commission terms')
        if type(expires) not in (int,float) or not time.time()<expires<=time.time()+30*86400: raise ValueError('invalid expiry')
        data={'id':agreement_id,'provider':provider,'mode':mode,'kind':kind,'amount':amount,
              'provider_acceptance_sha':provider_acceptance_sha,'expires':expires,'currency':'USD','simulated_provider_acceptance':mode=='simulation'}
        with self.store.lock:
            self.store.db.execute('INSERT INTO agreements VALUES (?,?,?)',(agreement_id,canonical(data),time.time()))
    def assess_commission(self,task_id,agreement_id,value_micros=0):
        if type(value_micros) is not int or not 0<=value_micros<=1000000000000: raise ValueError('invalid task value')
        with self.store.lock:
            self.store.db.execute('BEGIN IMMEDIATE')
            try:
                obj=self.store.get(task_id)
                row=self.store.db.execute('SELECT data FROM agreements WHERE id=?',(agreement_id,)).fetchone()
                if not row: raise ValueError('no provider agreement')
                terms=json.loads(row[0])
                if terms['expires']<=time.time() or terms['provider']!=obj['provider']: raise ValueError('agreement invalid for this task')
                if obj['state'] not in {'verified','commission_eligible'} or not obj.get('criteria_passed') or not obj['result_accepted'] or not obj['acceptance_evidence'] or not obj['referral_documented']: raise ValueError('eligibility evidence incomplete or blocked')
                if terms['mode']=='simulation' and obj['cohort']!='internal': raise ValueError('simulation requires internal cohort')
                if terms['mode']=='operator_attested' and (obj['cohort']!='independent_verified' or not obj.get('cohort_evidence')): raise ValueError('independent evidence required')
                amount=terms['amount'] if terms['kind']=='fixed' else value_micros*terms['amount']//10000
                if amount<=0: raise ValueError('positive commission base required')
                old=self.store.db.execute('SELECT amount_micros,mode,status FROM commissions WHERE task_id=?',(task_id,)).fetchone()
                if old:
                    if old!=(amount,terms['mode'],'eligible') or obj.get('agreement_id')!=agreement_id or obj.get('value_micros')!=value_micros: raise ValueError('commission conflict')
                else:
                    self.store.db.execute('INSERT INTO commissions VALUES (?,?,?,?)',(task_id,amount,terms['mode'],'eligible'))
                    obj.update(commission_mode=terms['mode'],commission_micros=amount,agreement_id=agreement_id,value_micros=value_micros)
                    self.store.event(obj,'commission_eligible')
                self.store.db.execute('COMMIT');return obj
            except Exception:
                self.store.db.execute('ROLLBACK');raise
