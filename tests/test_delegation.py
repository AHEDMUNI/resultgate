import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from resultgate.delegation.engine import Delegator
from resultgate.delegation.store import Store
from resultgate.delegation.providers import parse_result
from resultgate.brokerage.transport import ProviderFailure

SPEC={'description':'Structure this public bibliographic example','required_capabilities':['citation_structuring'],
 'citation':'Graff, Expert. Opin. Ther. Targets (2002) 6(1): 103-113', 'expected_surname':'Graff','expected_year':2002}
OUTPUT={'surnames':['Graff'],'years':['2002'],'titles':['Expert. Opin. Ther. Targets'],'untrusted_data':True}
PROOF='a'*64
class Fake:
    def __init__(self): self.calls=0
    def execute(self,spec): self.calls+=1;return OUTPUT.copy()

class DelegationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.adapter=Fake()
        self.e=Delegator(self.tmp.name,True,True,self.adapter)
    def tearDown(self): self.e.store.db.close();self.tmp.cleanup()
    def plan(self,key='opaque-1'): return self.e.plan(SPEC,key)['id']
    def verified(self):
        task=self.plan();self.e.execute(task,SPEC,True);return task
    def accepted(self):
        task=self.verified();state=self.e.status(task);self.e.accept_result(task,state['result_hash'],PROOF);return task
    def agree(self,kind='fixed',amount=250000):
        self.e.agreement('agreement','grobid_demo','simulation',kind,amount,PROOF,time.time()+3600)
    def test_lifecycle(self):
        task=self.verified()
        states=[r[0] for r in self.e.store.db.execute('SELECT state FROM events WHERE task_id=?',(task,))]
        self.assertEqual(states,['discovered','routed','dispatching','accepted','executing','completed','verified'])
        self.assertEqual(self.e.status(task)['commission_micros'],0)
    def test_persistence_dedup_and_no_content(self):
        task=self.verified()
        e=Delegator(self.tmp.name,True,True,self.adapter)
        self.assertTrue(e.execute(task,SPEC,True)['duplicate']);self.assertEqual(self.adapter.calls,1)
        self.assertEqual(e.plan(SPEC,'opaque-1')['id'],task)
        dump='\n'.join(e.store.db.iterdump())
        for private in [SPEC['citation'],SPEC['description'],'opaque-1','Graff']: self.assertNotIn(private,dump)
        self.assertEqual(os.stat(Path(self.tmp.name)/'delegation.sqlite3').st_mode & 0o777,0o600)
        e.store.db.close()
    def test_two_connections_no_double_dispatch(self):
        task=self.plan();e=Delegator(self.tmp.name,True,True,self.adapter)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda engine:engine.execute(task,SPEC,True),[self.e,e]))
        self.assertEqual(self.adapter.calls,1);self.assertEqual(sum(r['duplicate'] for r in results),1)
        e.store.db.close()
    def test_conflict_and_consent(self):
        task=self.plan()
        with self.assertRaises(ValueError): self.e.plan(dict(SPEC,expected_year=2003),'opaque-1')
        with self.assertRaises(ValueError): self.e.execute(task,SPEC,False)
        self.e.allow_network=False
        with self.assertRaises(ValueError): self.e.execute(task,SPEC,True)
        self.assertEqual(self.adapter.calls,0)
    def test_cancel_before_dispatch(self):
        task=self.plan();self.e.block(task,'cancelled')
        self.assertTrue(self.e.execute(task,SPEC,True)['duplicate']);self.assertEqual(self.adapter.calls,0)
    def test_cancel_in_flight(self):
        task=self.plan();entered=threading.Event();release=threading.Event()
        def run(spec): entered.set();release.wait(2);return OUTPUT
        with patch.object(self.adapter,'execute',side_effect=run):
            with ThreadPoolExecutor() as pool:
                future=pool.submit(self.e.execute,task,SPEC,True)
                self.assertTrue(entered.wait(2));self.e.block(task,'cancelled');release.set()
                self.assertEqual(future.result()['task']['state'],'cancelled')
    def test_timeout_no_retry(self):
        task=self.plan()
        with patch.object(self.adapter,'execute',side_effect=ProviderFailure('timeout')) as call:
            self.assertEqual(self.e.execute(task,SPEC,True)['task']['state'],'outcome_unknown')
            self.assertTrue(self.e.execute(task,SPEC,True)['duplicate']);call.assert_called_once()
    def test_provider_failure(self):
        task=self.plan()
        with patch.object(self.adapter,'execute',side_effect=ProviderFailure('http_503')):
            self.assertEqual(self.e.execute(task,SPEC,True)['task']['state'],'failed')
    def test_wrong_output_fails(self):
        task=self.plan()
        with patch.object(self.adapter,'execute',return_value=dict(OUTPUT,years=['2003'])):
            self.assertEqual(self.e.execute(task,SPEC,True)['task']['state'],'failed')
        self.agree()
        with self.assertRaises(ValueError): self.e.assess_commission(task,'agreement')
    def test_crash_inflight_stays_unknown(self):
        task=self.plan();obj=self.e.store.get(task);obj['deadline']=time.time()-1;self.e.store.event(obj,'dispatching')
        self.assertEqual(self.e.status(task)['state'],'outcome_unknown')
        self.assertTrue(self.e.execute(task,SPEC,True)['duplicate'])
    def test_fixed_commission_once(self):
        task=self.accepted();self.agree()
        for _ in range(3): self.assertEqual(self.e.assess_commission(task,'agreement')['commission_micros'],250000)
        self.assertEqual(self.e.store.db.execute('SELECT count(*) FROM commissions').fetchone()[0],1)
        self.assertEqual(self.e.store.summary()['eligible_referrals'],0)
        self.assertEqual(self.e.store.summary()['commissions'][0]['mode'],'simulation')
    def test_percentage(self):
        task=self.accepted();self.agree('basis_points',1250)
        self.assertEqual(self.e.assess_commission(task,'agreement',20000000)['commission_micros'],2500000)
    def test_missing_agreement_and_acceptance(self):
        task=self.verified()
        with self.assertRaises(ValueError): self.e.assess_commission(task,'missing')
        self.agree()
        with self.assertRaises(ValueError): self.e.assess_commission(task,'agreement')
        with self.assertRaises(ValueError): self.e.accept_result(task,'b'*64,PROOF)
    def test_blocked_voids_and_cannot_restore(self):
        for reason in ['cancelled','disputed','refunded']:
            e=Delegator(None,True,True,Fake());t=e.plan(SPEC,'k')['id'];r=e.execute(t,SPEC,True)
            e.accept_result(t,r['task']['result_hash'],PROOF);e.agreement('a','grobid_demo','simulation','fixed',1,PROOF,time.time()+100)
            e.assess_commission(t,'a');e.block(t,reason)
            with self.assertRaises(ValueError): e.assess_commission(t,'a')
            self.assertEqual(e.store.db.execute('SELECT status FROM commissions').fetchone()[0],'void');e.store.db.close()
    def test_immutable_agreement_and_expiry(self):
        task=self.accepted();self.agree()
        with self.assertRaises(sqlite3.IntegrityError): self.agree()
        with patch('resultgate.delegation.engine.time.time',return_value=time.time()+7200):
            with self.assertRaises(ValueError): self.e.assess_commission(task,'agreement')
    def test_internal_never_becomes_external(self):
        task=self.plan()
        with self.assertRaises(ValueError): self.e.attest_independent(task,PROOF)
        e=Delegator();t=e.plan(SPEC,'x')['id'];self.assertEqual(e.status(t)['cohort'],'external_unverified')
        e.attest_independent(t,PROOF);self.assertEqual(e.status(t)['cohort'],'independent_verified');e.store.db.close()
    def test_real_agreement_not_demo(self):
        with self.assertRaises(ValueError): self.e.agreement('a','grobid_demo','operator_attested','fixed',1,PROOF,time.time()+100)
        self.e.agreement('a','claix_a2a','operator_attested','fixed',1,PROOF,time.time()+100)
        task=self.accepted()
        with self.assertRaises(ValueError): self.e.assess_commission(task,'a')
    def test_retention_deletion(self):
        task=self.verified();self.e.store.delete(task)
        with self.assertRaises(ValueError): self.e.status(task)
        task=self.plan('second');self.e.store.db.execute('UPDATE tasks SET created=?',(time.time()-31*86400,));self.e.store.purge()
        self.assertEqual(self.e.store.db.execute('SELECT count(*) FROM events').fetchone()[0],0)
    def test_xml_and_unsafe_input(self):
        for raw in [b'<!DOCTYPE x [<!ENTITY a "x">]><biblStruct/>',b'<bad/>',b'x'*131073]:
            with self.assertRaises(ProviderFailure): parse_result(raw)
        with self.assertRaises(ValueError): self.e.plan(dict(SPEC,endpoint='http://127.0.0.1'),'x')
    def test_mcp_compatibility_and_privileged_tools_absent(self):
        async def run():
            params=StdioServerParameters(command=sys.executable,args=['-m','resultgate.server','--brokerage','--delegation','--delegation-store',self.tmp.name],cwd=str(Path(__file__).resolve().parents[1]))
            async with stdio_client(params) as (r,w):
                async with ClientSession(r,w) as session:
                    await session.initialize();names={t.name for t in (await session.list_tools()).tools}
                    self.assertEqual(len(names),12);self.assertIn('route_task',names);self.assertNotIn('assess_commission',names)
                    result=await session.call_tool('prepare_delegation',{'task':SPEC,'request_id':'mcp'})
                    self.assertFalse(result.isError);tid=result.structuredContent['id']
                    refused=await session.call_tool('execute_delegation',{'task_id':tid,'task':SPEC,'consent_to_send_public_citation':True})
                    self.assertTrue(refused.isError)
        asyncio.run(run())
