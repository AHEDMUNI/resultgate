import hashlib
import hmac
import json
import tempfile
import time
import unittest
from resultgate.network.registry import Registry, Submission
from resultgate.network.receipts import Receipts

DATA=dict(name='Fixture',description='Internal fixture only',capabilities=['citation_structuring'],
          protocol='api',endpoint='https://provider.example.com/api',auth='none',requirements='none',pricing='free fixture',limits='one task')
PROOF='a'*64
KEY=b'x'*32

class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.r=Registry(self.temp.name)
        self.s=self.r.submit(DATA); self.pid=self.s['provider']['id']; self.token=self.s['management_token']
        self.c=Receipts(self.r)
    def tearDown(self):
        self.r.db.close(); self.temp.cleanup()
    def approved(self,kind="task",rule="fixed",amount=1000000):
        self.r.review(self.pid,self.s['provider']['challenge'],PROOF,True)
        a=self.r.propose_terms(self.pid,'SIMULATION ONLY: fixed USD 1 per accepted successful task, no payment.',kind,rule,amount)
        self.r.accept_terms(self.pid,self.token,a['sha256'],True)
        self.r.approve_agreement(self.pid,PROOF)
    def referral(self, **kw):
        return self.c.refer(self.pid,PROOF,kw.get('kind','task'),kw.get('rule','fixed'),kw.get('amount',1000000),time.time()+300,kw.get('internal',True))
    def send(self,r,status='succeeded',event='evt1',outcome='out1',**kw):
        d=dict(event_id=event,referral_id=r['id'],outcome_id=outcome,kind=r['kind'],status=status,value_micros=10000000,currency='USD',evidence_sha256=PROOF)
        d.update(kw); body=json.dumps(d).encode(); ts=int(time.time())
        sig=hmac.digest(KEY,str(ts).encode()+b'.'+body,'sha256').hex()
        return self.c.ingest(self.pid,body,ts,sig,key=KEY)
    def test_submission_never_verified(self):
        self.assertEqual(self.r.discover(),[])
        self.assertFalse(self.s['provider']['executable'])
        with self.assertRaises(ValueError): Submission.model_validate(dict(DATA,verified=True))
    def test_endpoint_safety(self):
        for endpoint in ['http://host.com','https://127.0.0.1','https://[::1]','https://a.local/x','https://user:pass@a.com','https://a.com/?key=x','https://a.com:99','https://2130706433','https://a.com/%2e','https://a.com/#x']:
            with self.subTest(endpoint=endpoint),self.assertRaises(ValueError): Submission.model_validate(dict(DATA,endpoint=endpoint))
    def test_operator_review_required(self):
        with self.assertRaises(ValueError):self.r.review(self.pid,'wrong',PROOF,True)
        self.r.review(self.pid,self.s['provider']['challenge'],PROOF,True)
        self.assertEqual(len(self.r.discover('citation_structuring')),1)
        self.assertFalse(self.r.discover()[0]['executable'])
    def test_owner_not_operator(self):
        with self.assertRaises(ValueError):self.r.update(self.pid,'wrong',DATA)
        with self.assertRaises(ValueError):self.r.approve_agreement(self.pid,PROOF)
        self.assertNotIn(self.token,json.dumps(self.r.get(self.pid)))
    def test_exact_terms(self):
        a=self.r.propose_terms(self.pid,'SIMULATION ONLY: no commercial agreement or payment','task','fixed',1000000)
        for digest,consent in [(PROOF,True),(a['sha256'],False)]:
            with self.assertRaises(ValueError):self.r.accept_terms(self.pid,self.token,digest,consent)
        self.r.accept_terms(self.pid,self.token,a['sha256'],True)
        self.assertFalse(self.r.get(self.pid)['agreement']['operator_approved'])
    def test_update_invalidates_everything(self):
        self.approved(); self.r.update(self.pid,self.token,dict(DATA,endpoint='https://other.example.com'))
        self.assertEqual(self.r.discover(),[]); self.assertIsNone(self.r.get(self.pid)['agreement'])
    def test_suspend_delete(self):
        self.approved(); self.r.suspend(self.pid,self.token);self.assertEqual(self.r.discover(),[])
        self.r.delete(self.pid,self.token)
        with self.assertRaises(ValueError):self.r.get(self.pid)
    def test_restart(self):
        self.approved(); r2=Registry(self.temp.name)
        self.assertEqual(len(r2.discover()),1); r2.authorize(self.pid,self.token);r2.db.close()
    def test_success_dedup_simulation(self):
        self.approved();r=self.referral();self.send(r);self.send(r)
        self.c.attest(r['id'],PROOF);a=self.c.assess(r['id']);b=self.c.assess(r['id'])
        self.assertEqual(a,b);self.assertEqual(a['commission_micros'],1000000);self.assertEqual(a['mode'],'simulation')
        self.assertFalse(a['payments_enabled'])
    def test_percentage_subscription(self):
        self.approved('subscription','basis_points',2500);r=self.referral(kind='subscription',rule='basis_points',amount=2500)
        self.send(r);self.c.attest(r['id'],PROOF);self.assertEqual(self.c.assess(r['id'])['commission_micros'],2500000)
    def test_no_agreement(self):
        with self.assertRaises(ValueError):self.referral()
    def test_no_customer_acceptance(self):
        self.approved();r=self.referral();self.send(r)
        with self.assertRaises(ValueError):self.c.assess(r['id'])
    def test_no_independent_evidence(self):
        self.approved();r=self.referral(internal=False);self.send(r);self.c.attest(r['id'],PROOF)
        with self.assertRaises(ValueError):self.c.assess(r['id'])
    def test_internal_cannot_promote(self):
        self.approved();r=self.referral();self.send(r)
        with self.assertRaises(ValueError):self.c.attest(r['id'],PROOF,PROOF)
    def test_failed_never_eligible(self):
        self.approved();r=self.referral();self.send(r,'failed')
        with self.assertRaises(ValueError):self.c.attest(r['id'],PROOF)
        with self.assertRaises(ValueError):self.send(r,event='retry')
    def test_reversals(self):
        self.approved()
        for status in ['refunded','cancelled','disputed']:
            r=self.referral();self.send(r,event='success'+status,outcome=status)
            self.c.attest(r['id'],PROOF);self.c.assess(r['id'])
            self.send(r,status,event=status,outcome=status)
            self.assertEqual(self.c.get(r['id'])['commission_micros'],0)
            with self.assertRaises(ValueError):self.c.assess(r['id'])
    def test_forged_and_old_signatures(self):
        for ts in [int(time.time()),int(time.time())-600]:
            with self.assertRaises(ValueError):self.c.ingest(self.pid,b'{}',ts,'a'*64,key=KEY)
    def test_event_conflict_and_outcome_reuse(self):
        self.approved();r=self.referral();self.send(r)
        with self.assertRaises(ValueError):self.send(r,value_micros=1)
        with self.assertRaises(ValueError):self.send(self.referral(),event='second')
    def test_changed_agreement_blocks(self):
        self.approved();r=self.referral();self.send(r);self.c.attest(r['id'],PROOF)
        self.r.propose_terms(self.pid,'SIMULATION ONLY: changed agreement and amount','task','fixed',2000000)
        with self.assertRaises(ValueError):self.c.assess(r['id'])
    def test_tools_no_privileged_operations(self):
        import asyncio
        from mcp.server.fastmcp import FastMCP
        from resultgate.network.mcp import register
        server=FastMCP('test');reg=register(server,None)
        names={t.name for t in asyncio.run(server.list_tools())}
        self.assertEqual(names,{'submit_provider','update_provider','suspend_provider','accept_provider_terms','discover_registered_providers'})
        reg.db.close()
    def test_public_text_not_task_data(self):
        self.approved();r=self.referral();self.send(r)
        raw=self.r.db.execute('SELECT data FROM network_referrals').fetchone()[0]
        self.assertNotIn('out1',raw);self.assertNotIn('evt1',raw);self.assertNotIn(self.token,raw)
    def test_expired_ownership(self):
        p=self.r.get(self.pid);p['challenge_expires']=0;self.r.save(p,'fixture')
        with self.assertRaises(ValueError):self.r.review(self.pid,p['challenge'],PROOF,True)
    def test_numeric_validation(self):
        self.approved()
        for v in [True,-1,float('nan'),10001]:
            with self.assertRaises(ValueError):self.referral(rule='basis_points',amount=v)
    def test_bound_rules(self):
        self.approved()
        with self.assertRaises(ValueError):self.referral(amount=2)
    def test_provider_binding(self):
        self.approved();r=self.referral()
        body=json.dumps(dict(event_id='e',referral_id=r['id'],outcome_id='o',kind='task',status='succeeded',value_micros=1,currency='USD',evidence_sha256=PROOF)).encode()
        ts=int(time.time());sig=hmac.digest(KEY,str(ts).encode()+b'.'+body,'sha256').hex()
        with self.assertRaises(ValueError):self.c.ingest('another-provider',body,ts,sig,key=KEY)
    def test_signed_invalid_schema(self):
        for body in [b'{"x":1,"x":2}',b'{"value_micros":true}']:
            ts=int(time.time());sig=hmac.digest(KEY,str(ts).encode()+b'.'+body,'sha256').hex()
            with self.assertRaises(ValueError):self.c.ingest(self.pid,body,ts,sig,key=KEY)
    def test_persistent_dedup_second_connection(self):
        self.approved();r=self.referral();self.send(r);self.c.attest(r['id'],PROOF);self.c.assess(r['id'])
        other=Registry(self.temp.name);c=Receipts(other)
        self.assertEqual(c.assess(r['id'])['commission_micros'],1000000)
        self.assertEqual(c.summary()['eligible_simulations'],1)
        self.assertEqual(c.summary()['eligible_operator_attested'],0)
        other.db.close()
    def test_retention(self):
        self.approved();r=self.referral();self.send(r)
        self.r.db.execute('UPDATE network_referrals SET created=0')
        self.c.purge()
        with self.assertRaises(ValueError):self.c.get(r['id'])
    def test_expired_terms(self):
        self.approved();r=self.referral();self.send(r);self.c.attest(r['id'],PROOF)
        r=self.c.get(r['id']);r['expires']=0;self.c.save(r)
        with self.assertRaises(ValueError):self.c.assess(r['id'])
