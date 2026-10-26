import unittest
from resultgate.browseract_demo import Request, Report, assess, validate
class BrowserActTests(unittest.TestCase):
    def request(self,**kw): return Request(product_urls=['https://example.com/product'],**kw)
    def test_fit_gates_and_disclosed_referral(self):
        self.assertEqual('reject',assess(self.request())['decision'])
        self.assertEqual('use_existing_api',assess(self.request(sources_permitted=True,existing_api_or_export=True))['decision'])
        self.assertEqual('free_first',assess(self.request(sources_permitted=True))['decision'])
        x=assess(self.request(sources_permitted=True,local_execution_sufficient=False,recurring_cloud_need=True))
        self.assertEqual('consider_basic',x['decision']); self.assertEqual('https://browseract.com?fpr=ahed-ddc97e',x['offer']['referral_url'])
        self.assertIn('commission',x['offer']['disclosure'])
        self.assertFalse(x['purchase_authorized']); self.assertIsNone(x['task']['limits']['spending_authorization'])
    def test_private_credentials_duplicate_inputs(self):
        for url in ('http://example.com/p','https://user:secret@example.com/p','https://127.0.0.1/p','https://localhost/p','https://example.com/p?key=secret'):
            with self.assertRaises(ValueError): Request(product_urls=[url])
        with self.assertRaises(ValueError): Request(product_urls=['https://example.com/p']*20)
    def report(self,rows, samples=[]):
        return Report(expected_urls=['https://example.com/p'],rows=rows,sample_rows=samples,origin='internal',engine='fixture')
    def row(self): return dict(source_url='https://example.com/p',product='Demo',price='12.50',currency='USD',availability='in_stock',checked_at='2026-10-22T00:00:00Z',error=None)
    def test_complete_and_sample_mismatch(self):
        row=self.row(); x=validate(self.report([row],[dict(row,price='10.00')]))
        self.assertTrue(x['all_successful']); self.assertEqual(0,x['sample_matches']); self.assertFalse(x['commission_approved'])
    def test_missing_duplicates_bad_prices(self):
        self.assertFalse(validate(self.report([]))['complete'])
        self.assertFalse(validate(self.report([self.row(),self.row()]))['complete'])
        for p in ('NaN','Infinity','-1',None):
            self.assertFalse(validate(self.report([dict(self.row(),price=p)]))['complete'])
    def test_errors_not_guessed_success(self):
        x=validate(self.report([dict(self.row(),price=None,error='Not displayed')]))
        self.assertTrue(x['complete']); self.assertFalse(x['all_successful']); self.assertEqual(1,x['errors'])
    def test_unknown_origin_rejected(self):
        with self.assertRaises(ValueError): Report(expected_urls=['x'],rows=[],origin='independent_verified',engine='fixture')
if __name__=='__main__': unittest.main()

class MeasurementTests(unittest.TestCase):
    def test_no_double_count_or_internal_independent_mix(self):
        import sqlite3
        from resultgate.referral_measurement import record, summary
        db=sqlite3.connect(':memory:')
        event=dict(id='fixture-1',kind='commission_approved',origin='internal',evidence_ref='fixture-1',subject='test',amount_cents=480,currency='USD')
        self.assertTrue(record(db,event)); self.assertFalse(record(db,event))
        self.assertEqual(0,summary(db)['groups']['independent_verified']['approved_cents'])
        self.assertEqual(480,summary(db)['groups']['internal']['approved_cents'])
        with self.assertRaises(ValueError): record(db,dict(event,amount_cents=900))
        with self.assertRaises(ValueError): record(db,dict(event,kind='arrival'))
