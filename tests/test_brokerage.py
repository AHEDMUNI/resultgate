import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch, MagicMock
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from resultgate.brokerage.catalog import CATALOG, discover, fresh
from resultgate.brokerage.matching import match
from resultgate.brokerage.adapters import descriptor
from resultgate.brokerage.service import Broker
from resultgate.brokerage.transport import fetch_json, public_addresses, ProviderFailure, MAX_RESPONSE

DOI='10.1038/nphys1170'
RESPONSE={'message':{'DOI':DOI,'title':['Public metadata title']}}

class BrokerageTests(unittest.TestCase):
    def setUp(self):
        self.b=Broker(allow_network=True)
    def route(self,key='task'):
        return self.b.route('crossref',DOI,key)['referral']['route_id']
    def test_catalog_and_matching(self):
        self.assertEqual(len(discover()),4)
        self.assertEqual({p['id'] for p in match(['doi_metadata'])},{'crossref','datacite'})
        self.assertEqual(match(['web_search']),[])
        self.assertEqual({p['id'] for p in match(['web_search'],False)},{'firecrawl','tavily'})
        self.assertEqual(match(['doi_metadata','web_search']),[])
        self.assertTrue(all(not p['commission_available'] for p in discover()))
    def test_catalog_expiry(self):
        self.assertFalse(fresh(CATALOG[0],date(2027,1,1)))
        with patch('resultgate.brokerage.adapters.fresh',return_value=False):
            with self.assertRaises(ValueError): self.route()
    def test_reject_url_secrets_and_unknown(self):
        for value in ['http://127.0.0.1','https://api.crossref.org','10.1038/../admin','10.1038/x?token=secret','10.1038/x\r\nHost: localhost']:
            with self.assertRaises(ValueError): descriptor('crossref',value)
        for provider in ['unknown','firecrawl','tavily']:
            with self.assertRaises(ValueError): descriptor(provider,DOI)
    def test_consent_both_layers(self):
        rid=self.route()
        with patch('resultgate.brokerage.service.fetch_json') as fetch:
            with self.assertRaises(ValueError): self.b.execute(rid,DOI,False)
            self.b.allow_network=False
            with self.assertRaises(ValueError): self.b.execute(rid,DOI,True)
            fetch.assert_not_called()
    def test_success_tracking_and_duplicate(self):
        rid=self.route()
        with patch('resultgate.brokerage.service.fetch_json',return_value=RESPONSE) as fetch:
            result=self.b.execute(rid,DOI,True)
            self.assertEqual(result['referral']['status'],'succeeded')
            self.assertTrue(result['result']['untrusted_data'])
            self.assertTrue(self.b.execute(rid,DOI,True)['duplicate'])
            fetch.assert_called_once()
        state=self.b.ledger.view(rid)
        self.assertEqual(state['commission_usd'],0)
        self.assertFalse(state['independent_use_verified'])
        self.assertNotIn(DOI,repr(self.b.ledger.events))
        self.assertNotIn('Public metadata title',repr(self.b.ledger.events))
    def test_input_conflict_and_no_dispatch(self):
        rid=self.route()
        self.assertEqual(rid,self.route())
        with self.assertRaises(ValueError): self.b.route('datacite',DOI,'task')
        with patch('resultgate.brokerage.service.fetch_json') as fetch:
            with self.assertRaises(ValueError): self.b.execute(rid,'10.1038/other',True)
            fetch.assert_not_called()
    def test_failure_timeout_and_no_auto_retry(self):
        for code in ['timeout','http_429','http_503','connection_or_parse_error']:
            rid=self.route(code)
            with patch('resultgate.brokerage.service.fetch_json',side_effect=ProviderFailure(code)) as fetch:
                r=self.b.execute(rid,DOI,True)
                self.assertEqual(r['referral']['status'],'failed')
                self.assertEqual(r['referral']['execution_evidence']['code'],code)
                self.b.execute(rid,DOI,True)
                fetch.assert_called_once()
    def test_schema_mismatch_not_success(self):
        rid=self.route()
        with patch('resultgate.brokerage.service.fetch_json',return_value={'message':{'DOI':'10.9999/wrong','title':['x']}}):
            self.assertEqual(self.b.execute(rid,DOI,True)['referral']['status'],'failed')
    def test_internal_error_is_sanitized(self):
        rid=self.route()
        with patch('resultgate.brokerage.service.fetch_json',side_effect=RuntimeError('PRIVATE_SECRET')):
            response=self.b.execute(rid,DOI,True)
            self.assertNotIn('PRIVATE_SECRET',json.dumps(response))
            self.assertEqual(response['referral']['status'],'failed')
    def test_concurrent_execution_dispatches_once(self):
        rid=self.route()
        entered=threading.Event(); release=threading.Event()
        def fake(url):
            entered.set(); release.wait(timeout=3); return RESPONSE
        with patch('resultgate.brokerage.service.fetch_json',side_effect=fake) as fetch:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(self.b.execute,rid,DOI,True)
                self.assertTrue(entered.wait(timeout=2))
                second=self.b.execute(rid,DOI,True)
                self.assertEqual(second['referral']['status'],'executing')
                self.assertTrue(second['duplicate'])
                release.set()
                self.assertEqual(first.result()['referral']['status'],'succeeded')
            fetch.assert_called_once()
    def test_referral_expiry_and_bound(self):
        rid=self.route()
        self.b.ledger.events[rid]['_created']-=3601
        with self.assertRaises(ValueError): self.b.ledger.view(rid)
        for i in range(1000): self.route(str(i))
        with self.assertRaises(ValueError): self.route('overflow')
    def test_ssrf_hosts_and_dns(self):
        for url in ['http://api.crossref.org/works/a','https://127.0.0.1/','https://api.crossref.org.evil.test/',
                    'https://user:pass@api.crossref.org/works/a','https://api.crossref.org:444/a','https://api.crossref.org/a?secret=x']:
            with self.assertRaises(ProviderFailure): fetch_json(url)
        for ip in ['127.0.0.1','169.254.169.254','10.0.0.1','::1','::ffff:127.0.0.1']:
            with patch('socket.getaddrinfo',return_value=[(2,1,6,'',(ip,443))]):
                with self.assertRaises(ProviderFailure): public_addresses('api.crossref.org')
    def test_transport_redirect_size_and_errors(self):
        with patch('resultgate.brokerage.transport.public_addresses',return_value=['1.1.1.1']), patch('resultgate.brokerage.transport.PinnedHTTPS') as conn:
            response=conn.return_value.getresponse.return_value
            response.status=302
            with self.assertRaisesRegex(ProviderFailure,'http_302'): fetch_json(descriptor('crossref',DOI)['url'])
            response.status=200
            response.headers={'Content-Type':'application/json','Content-Encoding':'gzip'}
            with self.assertRaisesRegex(ProviderFailure,'unsupported_encoding'): fetch_json(descriptor('crossref',DOI)['url'])
            response.headers={'Content-Type':'application/json'}
            response.read.return_value=b'x'*8192
            with self.assertRaisesRegex(ProviderFailure,'response_too_large'): fetch_json(descriptor('crossref',DOI)['url'])
            response.read.side_effect=TimeoutError()
            with self.assertRaisesRegex(ProviderFailure,'timeout'): fetch_json(descriptor('crossref',DOI)['url'])
    def test_mcp_opt_in_and_no_network_by_default(self):
        async def run():
            params=StdioServerParameters(command=sys.executable,args=['-m','resultgate.server','--brokerage'],cwd=str(Path(__file__).resolve().parents[1]))
            async with stdio_client(params) as (read,write):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    names={t.name for t in (await session.list_tools()).tools}
                    self.assertEqual(names,{'check_extraction','check_citations','discover_providers','match_task','route_task','execute_route','track_referral'})
                    matches=await session.call_tool('match_task',{'required_capabilities':['doi_metadata']})
                    self.assertEqual(len(matches.structuredContent['matches']),2)
                    route=await session.call_tool('route_task',{'provider_id':'crossref','public_doi':DOI,'request_id':'internal-test'})
                    rid=route.structuredContent['referral']['route_id']
                    result=await session.call_tool('execute_route',{'route_id':rid,'public_doi':DOI,'confirm_public_identifier':True})
                    self.assertTrue(result.isError)
                    tracked=await session.call_tool('track_referral',{'route_id':rid})
                    self.assertEqual(tracked.structuredContent['status'],'prepared')
        asyncio.run(run())
