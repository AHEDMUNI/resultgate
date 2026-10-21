import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import secrets
import sys
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from experiments.metered.service import ShadowService, Rejected
from experiments.metered.server import create_shadow_app

GOOD = {'records':[{'id':1}], 'expected_count':1, 'job_status':'completed',
        'next_cursor':None, 'truncated':False}
CITE = {'sources':[{'id':'s','text':'PRIVATE_SOURCE_MARKER'}],
        'citations':[{'source_id':'s','quote':'PRIVATE_SOURCE_MARKER'}]}

class ShadowTests(unittest.TestCase):
    def setUp(self):
        self.token = secrets.token_urlsafe(32)
        self.service = ShadowService(self.token, credits=2)
        self.client = TestClient(create_shadow_app(self.service), base_url='http://127.0.0.1',
            headers={'Authorization':'Bearer '+self.token, 'Idempotency-Key':'one'})
    def call(self, payload=GOOD, key='one', tool='extraction'):
        return self.service.call(self.token, tool, payload, key)
    def test_dedup_and_conflict(self):
        self.assertEqual(self.call()['billing']['units_this_request'], 1)
        self.assertEqual(self.call()['billing']['units_this_request'], 0)
        with self.assertRaises(Rejected) as ctx: self.call(CITE, tool='citations')
        self.assertEqual(ctx.exception.code, 409)
    def test_concurrent_retry(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _:self.call(), range(40)))
        self.assertEqual(sum(r['billing']['units_this_request'] for r in results), 1)
    def test_concurrent_cap(self):
        def run(i):
            try: return self.call(key=str(i))['billing']['units_this_request']
            except Rejected as exc:
                self.assertEqual(exc.code,429)
                return 0
        with ThreadPoolExecutor(max_workers=8) as pool: counts=list(pool.map(run, range(40)))
        self.assertEqual(sum(counts),2)
    def test_exhaustion_and_retry(self):
        self.call(); self.call(key='two')
        self.assertTrue(self.call()['billing']['duplicate'])
        with self.assertRaises(Rejected) as ctx: self.call(key='three')
        self.assertEqual(ctx.exception.code,429)
    def test_invalid_and_execution_failure_not_counted(self):
        with self.assertRaises(Rejected): self.call({'records':[], 'expected_count':True})
        with patch('experiments.metered.service.audit_extraction', side_effect=RuntimeError('simulated')):
            with self.assertRaises(RuntimeError): self.call()
        self.assertEqual(self.service.summary()['completed_unique_operations'],0)
    def test_unknown_fail_are_completed_checks(self):
        self.assertEqual(self.call({'records':[]})['result']['status'],'unknown')
        self.assertEqual(self.call(dict(GOOD,expected_count=2),key='two')['result']['status'],'fail')
        self.assertEqual(self.service.credits,0)
    def test_bad_auth_and_id(self):
        with self.assertRaises(Rejected): self.service.call('bad','extraction',GOOD,'one')
        with self.assertRaises(Rejected): self.call(key='../private')
        self.assertEqual(self.service.credits,2)
    def test_private_summary(self):
        self.call(CITE, key='PRIVATE_TASK_MARKER', tool='citations')
        summary=self.service.summary()
        self.assertNotIn('PRIVATE', json.dumps(summary))
        self.assertNotIn('PRIVATE', repr(self.service._events))
        self.assertEqual(summary['verified_external_uses'],0)
        self.assertEqual(summary['money_collected_usd_micros'],0)
    def test_http_both_tools_and_duplicate(self):
        for tool,payload,key in [('extraction',GOOD,'one'),('citations',CITE,'two')]:
            for expected in [1,0]:
                r=self.client.post('/v1/'+tool,json=payload,headers={'Idempotency-Key':key})
                self.assertEqual(r.status_code,200)
                self.assertEqual(r.json()['billing']['units_this_request'],expected)
    def test_http_security(self):
        cases=[({'Origin':'http://evil.test'},403),({'Authorization':'Bearer bad'},401),
               ({'Host':'evil.test'},400),({'Idempotency-Key':''},422)]
        for headers,status in cases:
            self.assertEqual(self.client.post('/v1/extraction',json=GOOD,headers=headers).status_code,status)
        self.assertEqual(self.service.credits,2)
    def test_http_strict_json_and_limit(self):
        for data,status in [('x'*1048577,413),('{"records":[],"records":[]}',422),('{"records":[],"x":NaN}',422)]:
            self.assertEqual(self.client.post('/v1/extraction',content=data,headers={'Content-Type':'application/json'}).status_code,status)
        self.assertEqual(self.service.credits,2)
    def test_real_mcp_shadow_roundtrip(self):
        async def run():
            params=StdioServerParameters(command=sys.executable,args=['-m','experiments.metered.server'],
                cwd=str(Path(__file__).resolve().parents[1]),env={'RESULTGATE_TRIAL_TOKEN':self.token})
            async with stdio_client(params) as (read,write):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    self.assertEqual({t.name for t in (await session.list_tools()).tools},{'check_extraction','check_citations'})
                    for name,payload,key in [('check_extraction',GOOD,'a'),('check_citations',CITE,'b')]:
                        for units in [1,0]:
                            result=await session.call_tool(name,{'payload':payload,'request_id':key})
                            self.assertFalse(result.isError)
                            self.assertEqual(result.structuredContent['billing']['units_this_request'],units)
                    bad=await session.call_tool('check_extraction',{'payload':GOOD,'request_id':'b'})
                    self.assertTrue(bad.isError)
        asyncio.run(run())
