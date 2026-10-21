import concurrent.futures
import json
import multiprocessing
import tempfile
import unittest
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from test_network import DATA, PROOF


def process_create(args):
    directory, token = args
    r=Registry(directory)
    try: return Market(r).create(token,'shared-request',PROOF,'b'*64)
    finally: r.db.close()

class MarketTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.r=Registry(self.tmp.name)
        s=self.r.submit(DATA); self.pid=s['provider']['id']; self.management=s['management_token']
        self.r.review(self.pid,s['provider']['challenge'],PROOF,True)
        a=self.r.propose_terms(self.pid,'SIMULATION: ten percent of an accepted paid transaction','transaction','basis_points',1000)
        self.r.accept_terms(self.pid,self.management,a['sha256'],True);self.r.approve_agreement(self.pid,PROOF)
        self.m=Market(self.r);self.o=MarketOperator(self.m)
        self.requester=self.o.issue_credential('tenant-a');self.other=self.o.issue_credential('tenant-b')
        self.provider=self.o.issue_credential('provider-owner','provider',self.pid)
    def tearDown(self):
        self.r.db.close();self.tmp.cleanup()
    def create(self,key='request'):
        return self.m.create(self.requester,key,PROOF,'b'*64)['id']
    def through(self,until='commission_eligible',key='request'):
        tid=self.create(key)
        steps=[('matched',lambda:self.o.match(tid,self.pid,'match')),
               ('offered',lambda:self.m.advance(self.provider,tid,'offer','offered',evidence_sha256=PROOF)),
               ('accepted',lambda:self.m.advance(self.requester,tid,'accept','accepted',consent_to_send=True)),
               ('delegated',lambda:self.o.advance(tid,'delegate','delegated')),
               ('executing',lambda:self.m.advance(self.provider,tid,'execute','executing')),
               ('completed',lambda:self.m.advance(self.provider,tid,'complete','completed',evidence_sha256=PROOF)),
               ('verified',lambda:self.o.advance(tid,'verify','verified',evidence_sha256=PROOF)),
               ('transaction_proven',lambda:self.m.advance(self.provider,tid,'payment','transaction_proven',evidence_sha256=PROOF,simulated_transaction_id_sha256=PROOF,simulated_value_micros=10000000)),
               ('commission_eligible',lambda:self.o.advance(tid,'assess','commission_eligible'))]
        for state,fn in steps:
            fn()
            if state==until: break
        return tid
    def test_full_simulation_and_once_only_commission(self):
        tid=self.through(); t=self.m.get(self.requester,tid)
        self.assertEqual(t['simulated_commission_micros'],1000000)
        self.assertEqual(t['actual_commission_micros'],0);self.assertEqual(t['mode'],'simulation')
        self.assertFalse(t['external_dispatch']);self.assertFalse(t['payments_enabled'])
        self.assertTrue(self.o.advance(tid,'assess','commission_eligible')['duplicate'])
        self.assertEqual(self.r.db.execute("SELECT count(*) FROM market_events WHERE state='commission_eligible'").fetchone()[0],1)
    def test_cross_tenant_and_provider_scope(self):
        tid=self.create()
        for token in [self.other,self.provider,'0'*64]:
            with self.assertRaises(ValueError): self.m.get(token,tid)
        self.o.match(tid,self.pid,'match')
        self.assertEqual(self.m.get(self.provider,tid)['provider_id'],self.pid)
        self.assertNotIn('task_sha256',self.m.get(self.provider,tid))
        offer=self.m.advance(self.provider,tid,'offer','offered',evidence_sha256=PROOF)
        self.assertNotIn('success_criteria_sha256',offer)
        with self.assertRaises(ValueError): self.m.advance(self.other,tid,'cancel','cancelled')
    def test_roles_cannot_skip_or_verify(self):
        tid=self.through('completed')
        for token in [self.requester,self.provider]:
            with self.assertRaises(ValueError): self.m.advance(token,tid,'fake','verified',evidence_sha256=PROOF)
        with self.assertRaises(ValueError): self.o.advance(tid,'early','commission_eligible')
    def test_consent_is_separate_from_cost(self):
        tid=self.through('offered')
        with self.assertRaises(ValueError): self.m.advance(self.requester,tid,'a','accepted')
        with self.assertRaises(ValueError): self.m.advance(self.requester,tid,'a','accepted',consent_to_send=True,max_cost_micros=1)
        self.assertEqual(self.m.get(self.requester,tid)['state'],'offered')
    def test_refund_voids_simulation_and_blocks_revival(self):
        tid=self.through();self.o.advance(tid,'refund','refunded',evidence_sha256=PROOF)
        self.assertEqual(self.m.get(self.requester,tid)['simulated_commission_micros'],0)
        with self.assertRaises(ValueError):self.o.advance(tid,'again','commission_eligible')
        self.assertTrue(self.o.advance(tid,'refund','refunded',evidence_sha256=PROOF)['duplicate'])
    def test_failure_cancellation_dispute(self):
        tid=self.through('executing');self.m.advance(self.provider,tid,'fail','failed')
        with self.assertRaises(ValueError): self.m.advance(self.provider,tid,'complete','completed',evidence_sha256=PROOF)
        tid2=self.create('cancel-task');self.m.advance(self.requester,tid2,'cancel','cancelled')
        self.assertEqual(self.m.get(self.requester,tid2)['state'],'cancelled')
    def test_dispute_and_missing_agreement_cannot_earn(self):
        tid=self.through('transaction_proven')
        self.r.propose_terms(self.pid,'SIMULATION new unsigned terms','transaction','fixed',1)
        with self.assertRaises(ValueError):self.o.advance(tid,'assess','commission_eligible')
        with self.assertRaises(ValueError):self.m.advance(self.provider,tid,'dispute','disputed',evidence_sha256=PROOF)
        self.o.advance(tid,'dispute','disputed',evidence_sha256=PROOF)
        self.assertEqual(self.m.get(self.requester,tid)['simulated_commission_micros'],0)
    def test_wrong_provider_and_positive_virtual_transaction(self):
        tid=self.through('verified')
        submitted=self.r.submit(dict(DATA,name='Second fixture'))
        pid=submitted['provider']['id']
        self.r.review(pid,submitted['provider']['challenge'],PROOF,True)
        stranger=self.o.issue_credential('second-owner','provider',pid)
        with self.assertRaises(ValueError):self.m.get(stranger,tid)
        with self.assertRaises(ValueError):self.m.advance(self.provider,tid,'zero','transaction_proven',evidence_sha256=PROOF)
        result=self.m.advance(self.provider,tid,'virtual','transaction_proven',evidence_sha256=PROOF,simulated_transaction_id_sha256=PROOF,simulated_value_micros=1)
        self.assertEqual(result['mode'],'simulation');self.assertEqual(result['actual_commission_micros'],0)
    def test_transaction_attribution_survives_task_deletion(self):
        first=self.through('transaction_proven')
        self.m.delete(self.requester,first)
        second=self.through('verified',key='second')
        with self.assertRaises(ValueError):
            self.m.advance(self.provider,second,'payment','transaction_proven',evidence_sha256='c'*64,simulated_transaction_id_sha256=PROOF,simulated_value_micros=100)
        self.assertEqual(self.m.get(self.requester,second)['state'],'verified')
        self.assertEqual(self.r.db.execute('SELECT count(*) FROM market_outcomes').fetchone()[0],1)
    def test_expired_exact_retry_fails_closed(self):
        self.create()
        self.r.db.execute('UPDATE market_tasks SET created=0')
        with self.assertRaises(ValueError):self.m.create(self.requester,'request',PROOF,'b'*64)
    def test_spec_and_event_replay_conflicts(self):
        tid=self.through('offered')
        with self.assertRaises(ValueError):self.m.create(self.requester,'request','c'*64,'b'*64)
        with self.assertRaises(ValueError):self.m.advance(self.provider,tid,'offer','offered',evidence_sha256='c'*64)
        self.assertTrue(self.m.create(self.requester,'request',PROOF,'b'*64)['duplicate'])
        self.assertNotEqual(self.m.create(self.other,'request',PROOF,'b'*64)['id'],tid)
    def test_revocation_and_agreement_change(self):
        tid=self.through('transaction_proven')
        self.r.review(self.pid,'','',False)
        with self.assertRaises(ValueError):self.o.advance(tid,'assess','commission_eligible')
        self.o.revoke(self.requester)
        with self.assertRaises(ValueError):self.m.get(self.requester,tid)
    def test_management_token_is_not_requester_credential(self):
        with self.assertRaises(ValueError):self.m.create(self.management,'r',PROOF,'b'*64)
        with self.assertRaises(ValueError):self.o.issue_credential('fake','operator')
    def test_no_secrets_or_task_body_in_records(self):
        tid=self.create()
        rows=json.dumps(list(self.r.db.execute('SELECT * FROM market_tasks')))
        credentials=json.dumps(list(self.r.db.execute('SELECT * FROM market_credentials')))
        self.assertNotIn(self.requester,credentials);self.assertNotIn('tenant-a',rows+credentials)
        self.assertNotIn('tenant_hash',self.m.get(self.requester,tid))
        with self.assertRaises(ValueError):self.m.create(self.requester,'body','private document','b'*64)
    def test_delete_keeps_bounded_replay_tombstone(self):
        tid=self.create();self.m.delete(self.requester,tid)
        with self.assertRaises(ValueError):self.m.get(self.requester,tid)
        with self.assertRaises(ValueError):self.m.create(self.requester,'request',PROOF,'b'*64)
        data=self.r.db.execute('SELECT data FROM market_tasks WHERE id=?',(tid,)).fetchone()[0]
        self.assertNotIn(PROOF,data)
    def test_multiprocess_dedup_on_initialized_store(self):
        ctx=multiprocessing.get_context('spawn')
        with concurrent.futures.ProcessPoolExecutor(max_workers=2,mp_context=ctx) as pool:
            rows=list(pool.map(process_create,[(self.tmp.name,self.requester)]*2))
        self.assertEqual(rows[0]['id'],rows[1]['id'])
        self.assertEqual(sum(r['duplicate'] for r in rows),1)
