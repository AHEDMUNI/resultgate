import json
import tempfile
import unittest
from unittest.mock import patch
from resultgate.delegation.browser_use_trial import Trial, TrialError, Transport, identifier, amount, PageFacts

RID='11111111-1111-4111-8111-111111111111'
SID='22222222-2222-4222-8222-222222222222'
FACTS={'title':'Example Domain','heading':'Example Domain','documentation_example':True}
HTML='<title>Example Domain</title><h1>Example Domain</h1><p>For documentation examples.</p>'
class Fake:
    def __init__(self):
        self.calls=[];self.balance=1;self.free=True;self.active=0;self.state='completed';self.output=FACTS.copy();self.ambiguous=False;self.stop_fail=False
    def request(self,method,path,payload=None,*,page=False):
        self.calls.append((method,path,payload,page))
        if page:return HTML
        if path.endswith('/billing/account'):return {'isFreeTier':self.free,'totalCreditsBalanceUsd':self.balance,'activeSessionCount':self.active}
        if method=='POST' and path=='/api/v4/runs':
            if self.ambiguous:raise TrialError('transport_failed')
            return {'id':RID,'sessionId':SID}
        if path.endswith('/status'):return {'status':self.state}
        if path.endswith('/cancel'):return {}
        if '/browsers/' in path:
            if self.stop_fail:raise TrialError('transport_failed')
            return {'status':'stopped'}
        if path.endswith('/cost'):return {'sessionId':SID,'totalCostUsd':'0.012345'}
        return {'id':RID,'sessionId':SID,'status':self.state,'output':self.output,'totalCostUsd':'0.010000'}

class BrowserUseTrialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.fake=Fake();self.trial=Trial(self.tmp.name,self.fake)
    def tearDown(self):self.trial.db.close();self.tmp.cleanup()
    def run_trial(self):return self.trial.run(consent=True,free_no_card_no_recharge_confirmed=True)
    def test_requires_explicit_consent_before_network(self):
        with self.assertRaises(TrialError):self.trial.run()
        self.assertEqual(self.fake.calls,[])
    def test_preflight_blocks_paid_empty_busy_accounts(self):
        for attr,value in [('free',False),('balance',0),('active',1)]:
            old=getattr(self.fake,attr);setattr(self.fake,attr,value)
            with self.assertRaises(TrialError):self.run_trial()
            setattr(self.fake,attr,old)
        self.assertFalse(any(c[0]=='POST' for c in self.fake.calls))
    def test_full_mock_flow_verifies_and_stops_without_real_commission(self):
        r=self.run_trial();self.assertTrue(r['verified']);self.assertTrue(r['browser_stopped'])
        self.assertEqual(r['session_usage_usd'],'0.012345');self.assertFalse(r['commission_eligible'])
        self.assertEqual(r['cohort'],'internal');self.assertNotIn('output',r)
        request=next(c[2] for c in self.fake.calls if c[1]=='/api/v4/runs')
        self.assertEqual(request['maxCostUsd'],'0.10');self.assertIsNone(request['browserSettings']['proxyCountryCode'])
        self.assertFalse(request['agentmail']);self.assertNotIn('secretBindings',request)
    def test_repeat_after_restart_does_not_dispatch(self):
        first=self.run_trial();count=len(self.fake.calls)
        with tempfile.TemporaryDirectory() as unused:
            second=Trial(self.tmp.name,self.fake)
            try:self.assertEqual(second.run(),first)
            finally:second.db.close()
        self.assertEqual(len(self.fake.calls),count)
    def test_ambiguous_create_never_retried(self):
        self.fake.ambiguous=True;r=self.run_trial();self.assertIn('unknown',r['state'])
        self.run_trial();self.assertEqual(sum(c[0]=='POST' for c in self.fake.calls),1)
    def test_wrong_output_fails_independent_validation(self):
        self.fake.output={'title':'wrong','heading':'Example Domain','documentation_example':True}
        r=self.run_trial();self.assertFalse(r['verified']);self.assertTrue(r['browser_stopped'])
    def test_failure_is_not_verified(self):
        self.fake.state='failed';r=self.run_trial();self.assertFalse(r['verified']);self.assertEqual(r['state'],'failed')
    def test_cleanup_failure_not_claimed_stopped(self):
        self.fake.stop_fail=True;r=self.run_trial();self.assertFalse(r['browser_stopped'])
    def test_nonterminal_cancel_and_stop(self):
        self.run_trial();self.fake.state='running'
        r=self.trial.reconcile(poll_seconds=0)
        self.assertTrue(r['cancel_requested']);self.assertTrue(r['browser_stopped']);self.assertFalse(r['verified'])
    def test_routes_and_dns_rejected_before_sending_key(self):
        t=Transport('test-only-placeholder')
        with self.assertRaises(TrialError):t.request('GET','https://evil.example/')
        with patch('socket.getaddrinfo',return_value=[(0,0,0,'',('127.0.0.1',443))]):
            with self.assertRaises(TrialError):t.request('GET','/api/v2/billing/account')
    def test_numeric_and_identifier_validation(self):
        for value in [True,'NaN','Infinity',-1,None]:
            with self.assertRaises(TrialError):amount(value)
        with self.assertRaises(TrialError):identifier('../secret')
    def test_preflight_does_not_claim_credit_origin_or_recharge(self):
        r=self.trial.preflight();self.assertFalse(r['promotional_origin_verified_by_api']);self.assertFalse(r['recharge_setting_verified_by_api'])

    def test_public_fixture_may_have_no_title_but_requires_heading(self):
        p=PageFacts();p.feed('<html><h1>Public test fixture</h1><p>Some text</p></html>')
        self.assertEqual(p.facts(), {'title':'','heading':'Public test fixture','documentation_example':False})
        p=PageFacts();p.feed('<title>Example Domain</title><p>No heading</p>')
        with self.assertRaises(TrialError):p.facts()
