import tempfile
import time
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from resultgate.network.marketplace import Marketplace, MarketplaceOperator
from resultgate.network.gateway import create_app

SPEC = dict(name='Fixture service', description='Internal test only', capabilities=['web_scraping'],
            protocol='api', endpoint='https://provider.example.com/api', auth='api_key',
            requirements='Public pages only', pricing='USD per page, declared', limits='One page')


class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.registry = Registry(self.directory.name)
        self.market = Market(self.registry)
        self.tokens = MarketOperator(self.market)
        self.owner = self.tokens.issue_credential('owner')
        self.other = self.tokens.issue_credential('other')
        self.portal = Marketplace(self.market)
        self.operator = MarketplaceOperator(self.portal)

    def tearDown(self):
        self.registry.db.close()
        self.directory.cleanup()

    def apply(self, request='one', **changes):
        return self.portal.apply(self.owner, request_id=request, public_metadata_consent=True,
                                 service={**SPEC, **changes})

    def provider(self, **changes):
        r = self.registry.submit({**SPEC, **changes})
        p = r['provider']
        self.registry.review(p['id'], p['challenge'], 'a'*64, approve=True)
        return p['id'], r['management_token']

    def price(self, pid, micros, unit='page'):
        self.operator.review_price(pid, currency='USD', unit=unit, price_micros=micros,
                                   evidence_sha256='b'*64, valid_until=time.time()+3600)

    def test_intake_isolated_idempotent_and_not_auto_listed(self):
        app = self.apply()
        self.assertFalse(app['execution_enabled'])
        self.assertEqual(self.registry.discover(), [])
        self.assertTrue(self.apply()['duplicate'])
        with self.assertRaises(ValueError): self.apply(name='Changed')
        with self.assertRaises(ValueError): self.portal.status(self.other, app['application_id'])
        self.assertEqual(self.portal.status(self.owner, app['application_id'])['state'], 'pending_review')
        with self.assertRaises(ValueError):
            self.portal.apply(self.owner, request_id='bad', public_metadata_consent=False, service=SPEC)
        with self.assertRaises(ValueError):
            self.portal.apply(self.owner, request_id='numeric', public_metadata_consent=1, service=SPEC)
        for i in range(4): self.apply(str(i))
        with self.assertRaises(ValueError): self.apply('sixth')

    def test_review_requires_matching_independent_approval(self):
        app = self.apply()
        wrong, _ = self.provider(name='Different service')
        with self.assertRaises(ValueError): self.operator.decide(app['application_id'], 'c'*64, wrong)
        pid, _ = self.provider()
        decided = self.operator.decide(app['application_id'], 'c'*64, pid)
        self.assertEqual(decided['state'], 'approved_listing')
        self.assertFalse(decided['execution_enabled'])
        with self.assertRaises(ValueError): self.operator.decide(app['application_id'], 'c'*64, pid)

    def test_price_comparability_expiry_and_revision_binding(self):
        cheap, management = self.provider(name='Cheap')
        dear, _ = self.provider(name='Dear')
        unknown, _ = self.provider(name='Monthly')
        self.price(cheap, 100)
        self.price(dear, 200)
        self.price(unknown, 1, 'month')
        result = self.portal.recommend(self.owner, need='أريد استخراج بيانات', unit='page', max_price_micros=150)
        self.assertEqual([x['provider_id'] for x in result['recommendations']], [cheap])
        self.assertIsNone(result['recommendations'][0]['quality'])
        with patch('resultgate.network.marketplace.time.time', return_value=time.time()+7200):
            self.assertEqual(self.portal.recommend(self.owner, capabilities=['web_scraping'], unit='page', max_price_micros=150)['recommendations'], [])
        self.registry.update(cheap, management, {**SPEC, 'name': 'Cheap', 'pricing': 'changed'})
        p = self.registry.get(cheap)
        self.registry.review(cheap, p['challenge'], 'd'*64, approve=True)
        self.assertEqual(self.portal.recommend(self.owner, capabilities=['web_scraping'], unit='page', max_price_micros=150)['recommendations'], [])

    def test_commission_does_not_boost_and_suspension_hides(self):
        cheap, _ = self.provider(name='No commission')
        expensive, management = self.provider(name='Commission')
        self.price(cheap, 1); self.price(expensive, 2)
        a = self.registry.propose_terms(expensive, 'Simulation agreement fixture only, no real entitlement', 'task', 'basis_points', 5000)
        self.registry.accept_terms(expensive, management, a['sha256'], explicit_acceptance=True)
        self.registry.approve_agreement(expensive, 'd'*64)
        rows = self.portal.recommend(self.owner, capabilities=['web_scraping'], unit='page')['recommendations']
        self.assertEqual(rows[0]['provider_id'], cheap)
        self.assertEqual(rows[1]['commercial_relationship'], 'agreement_recorded')
        self.registry.suspend(expensive, management)
        self.assertEqual(len(self.portal.recommend(self.owner, capabilities=['web_scraping'])['recommendations']), 1)
        self.assertTrue(self.portal.recommend(self.owner, need='I need something unknown')['clarification_required'])

    def test_expired_and_revoked_credential_no_access(self):
        app = self.apply()
        self.tokens.revoke(self.owner)
        with self.assertRaises(ValueError): self.portal.status(self.owner, app['application_id'])
        with self.assertRaises(ValueError): self.portal.recommend(self.owner, need='scrape')

    def test_mcp_opt_in_and_caller_evidence_audit(self):
        headers = {'Authorization':'Bearer '+self.owner, 'Accept':'application/json, text/event-stream'}
        with TestClient(create_app(self.directory.name, marketplace_enabled=True), base_url='http://127.0.0.1', client=('127.0.0.1',5000)) as client:
            def call(name, args):
                return client.post('/mcp', headers=headers, json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}).json()
            self.assertFalse(call('apply_provider', {'request_id':'test','service':SPEC,'public_metadata_consent':True})['result']['isError'])
            self.assertFalse(call('recommend_services', {'need':'scrape'})['result']['isError'])
            result = call('audit_supplied_extraction', {'records':[{'name':'One'}], 'required_fields':['/name']})
            self.assertFalse(result['result']['isError'])
            self.assertIn('unknown',result['result']['content'][0]['text'])
            self.assertEqual(call('approve_provider', {})['error']['code'], -32602)
