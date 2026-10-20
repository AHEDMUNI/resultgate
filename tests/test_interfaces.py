import asyncio
import json
import sys
import unittest
from pathlib import Path
from starlette.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from resultgate.server import create_app

GOOD = {'records':[{'id':1}], 'unique_fields':['/id'], 'expected_count':1,
        'job_status':'completed','next_cursor':None,'truncated':False}

class Interfaces(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(create_app('local-test-token-not-a-real-secret-12345'),base_url='http://127.0.0.1',headers={'authorization':'Bearer local-test-token-not-a-real-secret-12345'})
    def test_api_pass(self):
        r=self.client.post('/v1/extraction',json=GOOD)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['status'],'pass')
    def test_api_unknown(self):
        self.assertEqual(self.client.post('/v1/extraction',json={'records':[]}).json()['status'],'unknown')
    def test_api_invalid(self):
        for payload in [None,[],{'records':[],'expected_count':False}]:
            self.assertEqual(self.client.post('/v1/extraction',content=json.dumps(payload),headers={'content-type':'application/json'}).status_code,422)
    def test_api_body_limit(self):
        self.assertEqual(self.client.post('/v1/extraction',content=b'x'*1048577,headers={'content-type':'application/json'}).status_code,413)
    def test_api_content_type(self):
        self.assertEqual(self.client.post('/v1/extraction',content='{}').status_code,415)
    def test_api_citations(self):
        r=self.client.post('/v1/citations',json={'sources':[{'id':'a','text':'Yes.'}],'citations':[{'source_id':'b','quote':'Yes.'}]})
        self.assertEqual(r.json()['status'],'fail')
        self.assertEqual(r.json()['semantic_support'],'not_evaluated')
    def test_real_mcp_sdk_roundtrip(self):
        async def run():
            params=StdioServerParameters(command=sys.executable,args=['-m','resultgate.server'],cwd=str(Path(__file__).resolve().parents[1]))
            async with stdio_client(params) as (read,write):
                async with ClientSession(read,write) as session:
                    init=await session.initialize()
                    listing=await session.list_tools()
                    self.assertEqual({t.name for t in listing.tools},{'check_extraction','check_citations'})
                    result=await session.call_tool('check_extraction',{'payload':GOOD})
                    self.assertFalse(result.isError)
                    self.assertEqual(result.structuredContent['status'],'pass')
                    bad=await session.call_tool('check_extraction',{'payload':{'records':[],'expected_count':True}})
                    self.assertTrue(bad.isError)
                    cite=await session.call_tool('check_citations',{'payload':{'sources':[{'id':'s','text':'Hello'}],'citations':[{'source_id':'s','quote':'Hello'}]}})
                    self.assertEqual(cite.structuredContent['status'],'pass')
        asyncio.run(run())
