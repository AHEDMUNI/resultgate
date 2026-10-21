import asyncio
import hashlib
import hmac
import json
import tempfile
import time
import unittest
from urllib.parse import parse_qs
import httpx
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from resultgate.commerce.core import Commerce, CommerceOperator, TERMS_SHA, fee
from resultgate.commerce.stripe_test import StripeTest, verify_webhook, refund_plan
from resultgate.commerce.http import create_app


class CommerceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.r=Registry(self.tmp.name)
        self.m=Market(self.r); self.c=Commerce(self.m); self.op=CommerceOperator(self.c)
        self.issuer=MarketOperator(self.m)
        self.seller=self.issuer.issue_credential('seller'); self.buyer=self.issuer.issue_credential('buyer')
        self.other=self.issuer.issue_credential('other')
        self.p=self.c.apply(self.seller,'Independent test provider',TERMS_SHA,True)
        self.op.review_provider(self.p['id'],'acct_fixture','a'*64)
        self.c.list_service(self.seller,self.p['id'],'analysis-v1','Public data analysis','data_analysis',10000)
        self.o=self.c.order(self.buyer,'analysis-v1','order-one')
        self.calls=[]
        self.created=int(time.time())
        self.adapter=StripeTest('sk_test_fixture','https://agents.allubiyerbamate.com',True,httpx.MockTransport(self.transport))

    def tearDown(self): self.r.db.close(); self.tmp.cleanup()

    def transport(self,request):
        self.calls.append(request)
        if request.method=='GET':
            return httpx.Response(200,json={'id':'acct_fixture','country':'US','charges_enabled':True,'payouts_enabled':True,'capabilities':{'transfers':'active'}})
        data=parse_qs(request.content.decode())
        self.assertEqual(['500'],data['payment_intent_data[application_fee_amount]'])
        self.assertEqual(['acct_fixture'],data['payment_intent_data[transfer_data][destination]'])
        self.assertEqual(['1'],data['line_items[0][quantity]'])
        return httpx.Response(200,json={'id':'cs_test_fixture','url':'https://checkout.stripe.com/c/pay/cs_test_fixture',
            'livemode':False,'client_reference_id':self.o['id'],'amount_total':10000,'currency':'usd'})

    def approve(self):
        self.op.approve_order(self.o['id'],self.o['owner'],self.o['quote_sha'],10000,time.time()+2400)

    def payevent(self,eid='evt_paid',paid=True):
        return {'id':eid,'type':'checkout.session.completed','livemode':False,'created':self.created,
                'data':{'object':{'id':'cs_test_fixture','payment_status':'paid' if paid else 'unpaid',
                    'payment_intent':'pi_fixture','amount_total':10000,'currency':'usd',
                    'client_reference_id':self.o['id'],'metadata':{'order_id':self.o['id']}}}}

    def paid(self):
        self.approve(); self.adapter.checkout(self.c,self.buyer,self.o['id'])
        return self.c.event(self.payevent())

    def refund(self,amount,eid):
        return self.c.event({'id':eid,'type':'charge.refunded','livemode':False,'created':self.created,
            'data':{'object':{'id':'ch_fixture','payment_intent':'pi_fixture','currency':'usd','amount':10000,'amount_refunded':amount}}})

    def dispute(self,status,eid,created):
        return self.c.event({'id':eid,'type':'charge.dispute.closed' if status in ('won','lost') else 'charge.dispute.created',
            'livemode':False,'created':created,'data':{'object':{'id':'dp_fixture','payment_intent':'pi_fixture',
            'currency':'usd','amount':10000,'status':status}}})

    def test_onboarding_terms_and_review_gate(self):
        with self.assertRaises(ValueError): self.c.apply(self.other,'Other','bad',True)
        other=self.c.apply(self.other,'Other',TERMS_SHA,True)
        with self.assertRaises(ValueError): self.c.list_service(self.other,other['id'],'bad','Service','data',100)
        with self.assertRaises(ValueError): self.op.review_provider(other['id'],'acct_fixture','b'*64)
        self.assertFalse(other['identity_verified'])
        self.assertFalse(other['live_agreement'])

    def test_no_owner_approval_no_checkout_or_network(self):
        with self.assertRaises(ValueError): self.adapter.checkout(self.c,self.buyer,self.o['id'])
        self.assertEqual([],self.calls)
        with self.assertRaises(ValueError): self.op.approve_order(self.o['id'],'f'*64,self.o['quote_sha'],10000,time.time()+10)
        with self.assertRaises(ValueError): self.op.approve_order(self.o['id'],self.o['owner'],self.o['quote_sha'],9999,time.time()+10)

    def test_paid_accrues_without_completion_and_balances(self):
        result=self.paid()
        self.assertEqual(500,result['commission_cents']); self.assertEqual(0,result['real_revenue_cents'])
        o=self.c.get(self.buyer,self.o['id'])
        self.assertEqual('paid_test',o['state']); self.assertFalse(o['settlement_confirmed'])
        postings=json.loads(self.c.db.execute('SELECT postings FROM commerce_ledger').fetchone()[0])
        self.assertEqual(0,sum(postings.values())); self.assertEqual(-9500,postings['test_provider_entitlement'])

    def test_session_and_payment_replays_do_not_double_count(self):
        self.paid(); self.adapter.checkout(self.c,self.buyer,self.o['id'])
        self.assertEqual(2,len(self.calls))
        self.assertTrue(self.c.event(self.payevent())['duplicate'])
        self.assertTrue(self.c.event(self.payevent('evt_other'))['duplicate'])
        self.assertEqual(1,self.c.db.execute('SELECT count(*) FROM commerce_ledger').fetchone()[0])

    def test_unpaid_and_unbound_events_not_accrued(self):
        self.assertEqual('not_paid',self.c.event(self.payevent(paid=False))['ignored'])
        with self.assertRaises(ValueError): self.c.event(self.payevent())
        self.assertEqual(0,self.c.db.execute('SELECT count(*) FROM commerce_payments').fetchone()[0])

    def test_full_partial_refund_and_stale_delivery(self):
        self.paid(); self.assertEqual(375,self.refund(2500,'evt_refund1')['commission_cents'])
        self.assertEqual(375,self.refund(1000,'evt_old_refund')['commission_cents'])
        self.assertEqual(0,self.refund(10000,'evt_refund2')['commission_cents'])
        total={}
        for row in self.c.db.execute('SELECT postings FROM commerce_ledger'):
            for k,v in json.loads(row[0]).items(): total[k]=total.get(k,0)+v
        self.assertTrue(all(v==0 for v in total.values()))

    def test_dispute_won_stale_created_and_lost(self):
        self.paid(); self.assertEqual(0,self.dispute('needs_response','evt_dp',10)['commission_cents'])
        self.assertEqual(500,self.dispute('won','evt_win',11)['commission_cents'])
        self.assertEqual(500,self.dispute('needs_response','evt_stale',9)['commission_cents'])

    def test_dispute_loss(self):
        self.paid(); self.assertEqual(0,self.dispute('lost','evt_lost',10)['commission_cents'])

    def test_tenant_isolation_and_revocation(self):
        with self.assertRaises(ValueError): self.c.get(self.other,self.o['id'])
        with self.assertRaises(ValueError): self.c.list_service(self.other,self.p['id'],'evil','X','data',100)
        self.assertEqual([],self.c.dashboard(self.other)['orders'])
        self.issuer.revoke(self.buyer)
        with self.assertRaises(ValueError): self.c.get(self.buyer,self.o['id'])

    def test_frozen_price_idempotency_and_order_scope(self):
        self.assertEqual(self.o,self.c.order(self.buyer,'analysis-v1','order-one'))
        with self.assertRaises(ValueError): self.c.list_service(self.seller,self.p['id'],'analysis-v1','Public data analysis','data_analysis',1)
        self.c.list_service(self.seller,self.p['id'],'analysis-v2','Public data analysis','data_analysis',5000)
        with self.assertRaises(ValueError): self.c.order(self.buyer,'analysis-v2','order-one')
        self.assertEqual('analysis-v2',self.c.search(self.buyer,'data_analysis')['services'][0]['id'])

    def test_predelegated_aggregate_budget_and_revocation(self):
        gid=self.op.grant(self.o['owner'],'analysis-v1',10000,time.time()+2400)
        self.op.use_grant(self.o['id'],gid); self.op.use_grant(self.o['id'],gid)
        second=self.c.order(self.buyer,'analysis-v1','order-two')
        with self.assertRaises(ValueError): self.op.use_grant(second['id'],gid)
        self.op.revoke_grant(gid)
        with self.assertRaises(ValueError): self.c.checkout_payload(self.buyer,self.o['id'])

    def test_signature_tamper_expiry_and_live(self):
        raw=json.dumps(self.payevent()).encode(); secret='whsec_fixture'; ts=int(time.time())
        sig=hmac.new(secret.encode(),str(ts).encode()+b'.'+raw,hashlib.sha256).hexdigest()
        header=f't={ts},v1={sig}'
        self.assertEqual(self.payevent(),verify_webhook(raw,header,secret,ts))
        for payload,signature,now in [(raw+b' ',header,ts),(raw,header,ts+301),(raw,'t=1,v1=no',ts)]:
            with self.assertRaises(ValueError): verify_webhook(payload,signature,secret,now)
        e=self.payevent(); e['livemode']=True
        with self.assertRaises(ValueError): self.c.event(e)
        with self.assertRaises(ValueError): StripeTest('sk_live_forbidden','https://example.com',True)

    def test_amount_currency_and_duplicate_event_tampering(self):
        self.paid()
        for field,value in [('amount_total',9999),('currency','eur'),('client_reference_id','other')]:
            e=self.payevent('evt_'+field); e['data']['object'][field]=value
            with self.assertRaises(ValueError): self.c.event(e)
        e=self.payevent(); e['data']['object']['amount_total']=1
        with self.assertRaises(ValueError): self.c.event(e)

    def test_rounding_and_refund_flags(self):
        self.assertEqual(0,fee(0)); self.assertEqual(1,fee(10)); self.assertEqual(500,fee(10000))
        for invalid in (True,-1,1.5):
            with self.assertRaises(ValueError): fee(invalid)
        p=refund_plan('pi_fixture',2500)
        self.assertTrue(p['parameters']['reverse_transfer']); self.assertTrue(p['parameters']['refund_application_fee'])
        self.assertFalse(p['execution_enabled'])

    def test_http_routes_auth_and_dashboard(self):
        async def run():
            app=create_app(self.c)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app,client=('127.0.0.1',1)),base_url='http://localhost') as client:
                self.assertEqual(200,(await client.get('/commerce')).status_code)
                self.assertEqual(401,(await client.get('/commerce/dashboard')).status_code)
                r=await client.get('/commerce/services',headers={'Authorization':'Bearer '+self.buyer})
                self.assertEqual(1,len(r.json()['services']))
                r=await client.get('/commerce/orders/'+self.o['id'],headers={'Authorization':'Bearer '+self.other})
                self.assertEqual(400,r.status_code)
                r=await client.post('/commerce/webhook',content=b'{}')
                self.assertEqual(503,r.status_code)
        asyncio.run(run())

    def test_no_mcp_admin_tools(self):
        from resultgate.commerce.mcp import build
        names={t.name for t in asyncio.run(build(self.c,self.buyer).list_tools())}
        self.assertEqual(8,len(names)); self.assertNotIn('approve_order',names); self.assertNotIn('review_provider',names)

    def test_new_order_honors_preexisting_grant_automatically(self):
        gid=self.op.grant(self.o['owner'],'analysis-v1',10000,time.time()+2400)
        new=self.c.order(self.buyer,'analysis-v1','auto-approved')
        self.assertEqual(gid,new['approval']['grant'])
        retry=self.c.order(self.buyer,'analysis-v1','auto-approved')
        self.assertEqual(new,retry)
        other=self.c.order(self.buyer,'analysis-v1','over-budget')
        self.assertIsNone(other['approval'])

    def test_actual_mcp_sdk_process(self):
        import os
        import sys
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        async def run():
            params=StdioServerParameters(command=sys.executable,
                args=['-m','resultgate.commerce.mcp','--directory',self.tmp.name],
                env={**os.environ,'RESULTGATE_REQUESTER_TOKEN':self.buyer})
            async with stdio_client(params) as (read,write):
                async with ClientSession(read,write) as session:
                    await session.initialize()
                    self.assertEqual(8,len((await session.list_tools()).tools))
                    response=await session.call_tool('search_services',{'capability':'data_analysis'})
                    self.assertFalse(response.isError)
                    payload=json.loads(response.content[0].text)
                    self.assertEqual('analysis-v1',payload['services'][0]['id'])
        asyncio.run(run())
