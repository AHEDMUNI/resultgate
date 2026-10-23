import asyncio
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from resultgate.first_order.service import Intake, public_url, verify_result, request_template


class FirstOrderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1792588800
        self.store = Intake(self.tmp.name, clock=lambda: self.now)

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def quote(self):
        return self.store.prepare('request-1', 'https://example.com', True, 'hobby_monthly')

    def test_retry_and_conflicting_spec(self):
        q = self.quote()
        self.assertEqual(q, self.quote())
        with self.assertRaises(ValueError):
            self.store.prepare('request-1', 'https://other.example.com', True)
        self.assertEqual(1, self.store.db.execute('SELECT count(*) FROM requests').fetchone()[0])

    def test_approval_exact_scope_budget_expiry_revocation(self):
        q = self.quote()
        for sha, budget, expiry in [('bad', 19000000, self.now+30),
                                    (q['quote_sha256'], 1, self.now+30),
                                    (q['quote_sha256'], 19000000, self.now+4000)]:
            with self.assertRaises(ValueError):
                self.store.approve(q['request_id'], sha, budget, expiry)
        approved = self.store.approve(q['request_id'], q['quote_sha256'], 19000000, self.now+30)
        self.assertTrue(approved['owner_approval_current'])
        self.assertFalse(approved['execution_enabled'])
        self.assertEqual(0, approved['revenue_micros'])
        self.assertFalse(self.store.revoke(q['request_id'])['owner_approval_current'])
        self.store.approve(q['request_id'], q['quote_sha256'], 19000000, self.now+30)
        self.now += 31
        self.assertFalse(self.store.get(q['request_id'])['owner_approval_current'])

    def test_stale_price_cannot_be_approved(self):
        self.now += 31*86400
        q = self.quote()
        with self.assertRaises(ValueError):
            self.store.approve(q['request_id'], q['quote_sha256'], 19000000, self.now+30)

    def test_free_default_and_plan_changes_require_new_quote(self):
        q = self.store.prepare('free-request', 'https://example.com', True)
        self.assertEqual(0, q['subscription_first_month_micros'])
        self.assertTrue(self.store.approve(q['request_id'], q['quote_sha256'], 0, self.now+30)['owner_approval_current'])
        with self.assertRaises(ValueError):
            self.store.prepare('free-request', 'https://example.com', True, 'hobby_monthly')

    def test_private_data_not_stored(self):
        self.quote()
        stored = self.store.db.execute('SELECT spec,quote FROM requests').fetchone()
        self.assertNotIn('example.com', str(stored))
        self.assertEqual(0, os.stat(self.tmp.name+'/first-order.sqlite3').st_mode & 0o077)

    def test_invalid_targets_and_missing_permission(self):
        for url in ['http://example.com', 'https://127.0.0.1', 'https://[::1]',
                    'https://user:pass@example.com', 'https://example.com?key=secret',
                    'https://a.local', 'https://example.com:444', 'https://example.com\\@a.com']:
            with self.assertRaises(ValueError):
                public_url(url)
        with self.assertRaises(ValueError):
            self.store.prepare('request-1', 'https://example.com')

    def test_response_checks_do_not_claim_authenticity(self):
        evidence = {'success': True, 'data': {'markdown': '# Hello',
                    'metadata': {'sourceURL': 'https://example.com', 'statusCode': 200}}}
        report = verify_result('https://example.com', evidence)
        self.assertEqual('contract_pass', report['status'])
        self.assertFalse(report['payment_proven'])
        self.assertFalse(report['commission_earned'])
        for bad in [{'success': False}, {'success': True, 'data': []},
                    {'success': True, 'data': {'markdown': 'oops', 'metadata': {'statusCode': 403}}}]:
            self.assertEqual('needs_review', verify_result('https://example.com', bad)['status'])
        with self.assertRaises(ValueError):
            verify_result('https://example.com', {'data': 'a' * (1024*1024)})

    def test_no_transport_or_credentials_in_request(self):
        with patch('socket.socket', side_effect=AssertionError('no networking')):
            template = request_template('https://example.com')
            self.quote()
        self.assertEqual(['markdown'], template['body']['formats'])
        self.assertFalse(template['execution_enabled'])
        self.assertNotIn('Authorization', template)

    def test_mcp_exposes_no_approval_or_execution(self):
        from resultgate.first_order.mcp import build
        server = build(self.tmp.name)
        names = {tool.name for tool in asyncio.run(server.list_tools())}
        self.assertEqual({'compare_public_page_services', 'prepare_public_page_request',
                          'get_public_page_request', 'prepare_firecrawl_request',
                          'verify_public_page_result'}, names)


class StdioIntegration(unittest.TestCase):
    def test_independent_sdk_process(self):
        import sys
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def run(directory):
            params = StdioServerParameters(command=sys.executable,
                args=['-m', 'resultgate.first_order.mcp', '--directory', directory])
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    self.assertEqual(5, len((await session.list_tools()).tools))
                    result = await session.call_tool('prepare_public_page_request',
                        {'request_key': 'sdk-fixture', 'url': 'https://example.com', 'permission_confirmed': True})
                    self.assertFalse(result.isError)
                    q = json.loads(result.content[0].text)
                    self.assertEqual('awaiting_owner_approval', q['state'])
                    self.assertFalse(q['execution_enabled'])
        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(run(directory))
