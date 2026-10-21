"""Legacy offline matching tests, now included in the project's unittest runner."""
import unittest
from resultgate.routing import Provider, route_task

class RoutingTests(unittest.TestCase):
    def test_matching_and_price_order(self):
        providers=[Provider('b','B',('pdf','ocr'),'https://example.org/b',2,True),
                   Provider('a','A',('pdf','ocr'),'https://example.org/a',1,True),
                   Provider('c','C',('pdf',),'https://example.org/c',0,True)]
        self.assertEqual([p['provider_id'] for p in route_task(['pdf','ocr'],providers)],['a','b'])
    def test_unverified_excluded_by_default(self):
        p=Provider('a','A',('pdf',),'https://example.org/a')
        self.assertEqual(route_task(['pdf'],[p]),[])
        self.assertEqual(len(route_task(['pdf'],[p],require_verified=False)),1)
    def test_budget_and_commission_not_assumed(self):
        p=Provider('a','A',('pdf',),'https://example.org/a',2,True,True)
        self.assertEqual(route_task(['pdf'],[p],max_price_usd=1),[])
        self.assertFalse(route_task(['pdf'],[p])[0]['commission_available'])
    def test_empty_capabilities_rejected(self):
        with self.assertRaises(ValueError): route_task([],[])
    def test_nonfinite_prices(self):
        for value in [float('nan'),float('inf'),-1,True]:
            with self.assertRaises(ValueError): route_task(['pdf'],[],max_price_usd=value)
            self.assertEqual(route_task(['pdf'],[Provider('a','A',('pdf',),'https://example.org',value,True)]),[])
