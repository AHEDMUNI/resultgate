import json,sqlite3,sys,unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from resultgate.referral_selector import Selection,Preparation,select,prepare,catalog
from resultgate.referral_measurement import record
from resultgate.referral_daily import daily
class SelectionTests(unittest.TestCase):
    def test_permission_and_free_boundaries(self):
        self.assertEqual(select(Selection(need='search_results'))['decision'],'reject')
        self.assertEqual(select(Selection(need='search_results',sources_permitted=True))['decision'],'use_local_first')
        self.assertEqual(select(Selection(need='search_results',sources_permitted=True,existing_solution_sufficient=True))['candidates'],[])
        for p in catalog()['providers']:
            result=select(Selection(need=p['need'],sources_permitted=True,local_solution_sufficient=False))
            self.assertEqual(result['candidates'][0]['id'],p['id'])
            self.assertFalse(result['paid_plan_recommended'])
            task=prepare(Preparation(provider_id=p['id'],sources_permitted=True))
            self.assertEqual(task['handoff']['tracking'],'provider_affiliate_link' if p['id']=='browseract' else 'none')
            self.assertEqual(task['handoff']['affiliate_link'],p['id']=='browseract')
            if p['id']=='browseract': self.assertEqual(task['handoff']['url'],'https://browseract.com?fpr=ahed-ddc97e')
            self.assertFalse(task['execution_started']);self.assertFalse(task['purchase_authorized'])
            self.assertTrue(task['input_fields']);self.assertTrue(task['output_fields'])
    def test_evidence_dedup_and_unknown(self):
        db=sqlite3.connect(':memory:');day=datetime.now(ZoneInfo('America/Chicago')).date().isoformat()
        e=dict(id='a',subject='internal-test',evidence_ref='sample-proof',kind='usage',origin='internal',provider_id='firecrawl')
        self.assertTrue(record(db,e));self.assertFalse(record(db,e))
        with self.assertRaises(ValueError):record(db,dict(e,origin='independent_verified'))
        stats=daily(db,day)['providers']['firecrawl']['usage']
        self.assertIsNone(stats['total']);self.assertEqual(stats['recorded_events']['internal'],1);self.assertEqual(stats['recorded_events']['independent_verified'],0)
    def test_no_unverified_financial_event(self):
        with self.assertRaises(ValueError):record(sqlite3.connect(':memory:'),dict(id='a',subject='x',evidence_ref='x',kind='commission_pending',origin='unknown',provider_id='apify'))
class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_six_provider_tasks_over_mcp(self):
        from mcp import ClientSession,StdioServerParameters
        from mcp.client.stdio import stdio_client
        async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','resultgate.browseract_demo'])) as (r,w):
            async with ClientSession(r,w) as s:
                await s.initialize(); names={t.name for t in (await s.list_tools()).tools}
                self.assertTrue({'list_referral_providers','recommend_referral_service','prepare_referral_task'}<=names)
                for p in catalog()['providers']:
                    result=await s.call_tool('prepare_referral_task',{'request':{'provider_id':p['id'],'sources_permitted':True}})
                    self.assertFalse(result.isError);self.assertFalse(json.loads(result.content[0].text)['execution_started'])
