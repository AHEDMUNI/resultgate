import copy
import json
import tempfile
import time
import unittest
from urllib.parse import parse_qs
import httpx
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from resultgate.commerce.core import Commerce, CommerceOperator, TERMS_SHA
from resultgate.commerce.stripe_test import StripeTest
from resultgate.commerce.connect_test import ConnectTest


class ConnectTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.r=Registry(self.tmp.name)
        self.c=Commerce(Market(self.r)); issuer=MarketOperator(self.c.market)
        self.seller=issuer.issue_credential('seller'); self.buyer=issuer.issue_credential('buyer')
        self.p=self.c.apply(self.seller,'Test provider',TERMS_SHA,True)
        self.calls=[]; self.refunded=0; self.refund_status='succeeded'; self.corrupt=False
        self.stripe=StripeTest('sk_test_fixture','https://sandbox.example',True,httpx.MockTransport(self.transport))
        self.op=ConnectTest(self.c,self.stripe)

    def tearDown(self): self.r.db.close(); self.tmp.cleanup()

    def transport(self,req):
        path=req.url.path; self.calls.append((req.method,path,parse_qs(req.content.decode()),dict(req.headers)))
        a={'id':'acct_fixture','country':'US','metadata':{'resultgate_provider':self.p['id']},'details_submitted':True,
           'charges_enabled':True,'payouts_enabled':True,'capabilities':{'transfers':'active'}}
        if path in ('/v1/accounts','/v1/accounts/acct_fixture'): return httpx.Response(200,json=a)
        if path=='/v1/account_links': return httpx.Response(200,json={'url':'https://connect.stripe.com/setup/fixture','expires_at':time.time()+300})
        if path=='/v1/checkout/sessions': return httpx.Response(200,json={'id':'cs_test_fixture','url':'https://checkout.stripe.com/c/pay/fixture','livemode':False,'client_reference_id':self.o['id'],'amount_total':10000,'currency':'usd'})
        if path=='/v1/refunds':
            data=parse_qs(req.content.decode()); self.refunded+=int(data['amount'][0])
            return httpx.Response(200,json={'id':'re_'+str(self.refunded),'payment_intent':'pi_fixture','amount':int(data['amount'][0]),'currency':'usd','status':self.refund_status})
        if path.startswith('/v1/refunds/re_'): return httpx.Response(200,json={'id':path.rsplit('/',1)[1],'status':self.refund_status})
        objs={
            '/v1/payment_intents/pi_fixture':{'id':'pi_fixture','livemode':False,'status':'succeeded','amount':10000,'currency':'usd','metadata':{'order_id':self.o['id']},'transfer_data':{'destination':'acct_fixture'},'application_fee_amount':500,'latest_charge':'ch_fixture'},
            '/v1/charges/ch_fixture':{'id':'ch_fixture','livemode':False,'paid':True,'captured':True,'payment_intent':'pi_fixture','amount':10000,'currency':'usd','amount_refunded':self.refunded,'application_fee':'fee_fixture','transfer':'tr_fixture','balance_transaction':'txn_fixture'},
            '/v1/application_fees/fee_fixture':{'id':'fee_fixture','livemode':False,'charge':'ch_fixture','account':'acct_fixture','currency':'usd','amount':500,'amount_refunded':self.refunded//20},
            '/v1/transfers/tr_fixture':{'id':'tr_fixture','livemode':False,'source_transaction':'ch_fixture','destination':'acct_wrong' if self.corrupt else 'acct_fixture','currency':'usd','amount':10000,'amount_reversed':self.refunded},
            '/v1/balance_transactions/txn_fixture':{'id':'txn_fixture','source':'ch_fixture','currency':'usd','fee':320,'status':'available'}}
        return httpx.Response(200,json=objs[path])

    def pay(self):
        self.op.create_account(self.p['id']); self.op.review(self.p['id'],'a'*64)
        self.c.list_service(self.seller,self.p['id'],'analysis','Data analysis','data',10000)
        self.o=self.c.order(self.buyer,'analysis','one')
        CommerceOperator(self.c).approve_order(self.o['id'],self.o['owner'],self.o['quote_sha'],10000,time.time()+2400)
        self.stripe.checkout(self.c,self.buyer,self.o['id'])
        self.event={'id':'evt_paid','livemode':False,'type':'checkout.session.completed','data':{'object':{
            'id':'cs_test_fixture','payment_status':'paid','payment_intent':'pi_fixture','amount_total':10000,'currency':'usd',
            'client_reference_id':self.o['id'],'metadata':{'order_id':self.o['id']}}}}
        self.c.event(self.event)

    def sync_refund(self):
        self.c.event({'id':'evt_refund'+str(self.refunded),'livemode':False,'type':'charge.refunded','data':{'object':{
            'payment_intent':'pi_fixture','currency':'usd','amount':10000,'amount_refunded':self.refunded}}})

    def test_full_lifecycle_fee_partial_full_refund_and_reconciliation(self):
        self.pay(); first=self.op.reconcile(self.o['id'])
        self.assertTrue(first['matched']); self.assertEqual(500,first['net_commission_cents']); self.assertEqual(9500,first['provider_net_before_costs_cents'])
        self.assertTrue(self.c.event(self.event)['duplicate'])
        self.op.refund(self.o['id'],4000); self.sync_refund()
        partial=self.op.reconcile(self.o['id']); self.assertTrue(partial['matched']); self.assertEqual(300,partial['net_commission_cents']); self.assertEqual(5700,partial['provider_net_before_costs_cents'])
        self.op.refund(self.o['id'],4000); self.assertEqual(4000,self.refunded)
        self.op.refund(self.o['id'],10000); self.sync_refund()
        final=self.op.reconcile(self.o['id']); self.assertTrue(final['matched']); self.assertEqual(0,final['net_commission_cents']); self.assertEqual(0,final['real_revenue_cents']); self.assertFalse(final['settlement_confirmed'])
        for method,path,data,_ in self.calls:
            if method=='POST' and path=='/v1/refunds':
                self.assertEqual(['true'],data['reverse_transfer']); self.assertEqual(['true'],data['refund_application_fee'])

    def test_account_idempotency_and_onboarding_does_not_approve(self):
        self.op.create_account(self.p['id']); self.op.create_account(self.p['id'])
        self.assertEqual(1,sum(method=='POST' and path=='/v1/accounts' for method,path,_,_ in self.calls))
        link=self.op.onboarding_link(self.p['id']); self.assertIn('connect.stripe.com',link['url'])
        self.assertEqual('pending_review',self.c.load('providers',self.p['id'])['state'])
        self.assertNotIn('https://connect.stripe.com',str(self.r.db.execute('SELECT result FROM commerce_test_operations').fetchall()))

    def test_wrong_destination_blocks_reconciliation(self):
        self.pay(); self.corrupt=True
        with self.assertRaises(ValueError): self.op.reconcile(self.o['id'])

    def test_refund_webhook_lag_detected(self):
        self.pay(); self.op.refund(self.o['id'],4000)
        report=self.op.reconcile(self.o['id']); self.assertFalse(report['matched']); self.assertIn('refund_webhook_sync',report['findings'])

    def test_pending_refund_blocks_next_refund_and_settlement(self):
        self.pay(); self.refund_status='pending'; self.op.refund(self.o['id'],4000)
        with self.assertRaises(ValueError): self.op.refund(self.o['id'],10000)
        self.assertIn('refund_not_succeeded',self.op.reconcile(self.o['id'])['findings'])

    def test_unknown_timeout_never_reissues_refund(self):
        self.pay()
        original=self.stripe.request
        def timeout(method,path,data=None,key=None):
            if path=='/v1/refunds': raise httpx.ReadTimeout('fixture')
            return original(method,path,data,key)
        self.stripe.request=timeout
        with self.assertRaises(httpx.ReadTimeout): self.op.refund(self.o['id'],4000)
        self.stripe.request=original
        with self.assertRaises(ValueError): self.op.refund(self.o['id'],4000)
        self.assertEqual(0,self.refunded)

    def test_live_keys_and_unsafe_operations_rejected(self):
        with self.assertRaises(ValueError): StripeTest('sk_live_fixture','https://sandbox.example',True)
        for method,path in [('POST','/v1/transfers'),('POST','/v1/payouts'),('GET','/v1/accounts/acct_x/../balance'),('DELETE','/v1/accounts/acct_fixture')]:
            with self.assertRaises(ValueError): self.stripe.request(method,path)
        self.assertEqual([],self.calls)

    def test_account_retry_window_fails_closed(self):
        def fail(): raise httpx.ReadTimeout('fixture')
        with self.assertRaises(httpx.ReadTimeout): self.op.operation('test-key',{},fail)
        with self.r.db: self.r.db.execute('UPDATE commerce_test_operations SET created=0')
        with self.assertRaises(ValueError): self.op.operation('test-key',{},lambda: {})

    def test_checkout_cannot_outlive_owner_authorization(self):
        self.pay()
        checkout=[v for v in self.calls if v[1]=='/v1/checkout/sessions'][0]
        approval=self.c.load('orders',self.o['id'])['approval']
        self.assertLessEqual(int(checkout[2]['expires_at'][0]),approval['expires'])
        second=self.c.order(self.buyer,'analysis','two')
        CommerceOperator(self.c).approve_order(second['id'],second['owner'],second['quote_sha'],10000,time.time()+60)
        before=len(self.calls)
        with self.assertRaises(ValueError): self.stripe.checkout(self.c,self.buyer,second['id'])
        self.assertEqual(before,len(self.calls))

    def test_restore_preserves_payment_and_refund_idempotency(self):
        self.pay(); self.op.refund(self.o['id'],4000); self.sync_refund()
        with tempfile.TemporaryDirectory() as target:
            restored=Registry(target)
            try:
                self.r.db.backup(restored.db)
                c=Commerce(Market(restored)); op=ConnectTest(c,self.stripe)
                self.assertTrue(c.event(self.event)['duplicate'])
                op.refund(self.o['id'],4000)
                self.assertEqual(4000,self.refunded)
                self.assertEqual(300,c.load('orders',self.o['id'])['commission_cents'])
            finally: restored.db.close()

    def test_incomplete_account_cannot_be_approved(self):
        self.op.create_account(self.p['id'])
        original=self.op.account
        def incomplete(pid):
            a=original(pid); a['charges_enabled']=False; return a
        self.op.account=incomplete
        with self.assertRaises(ValueError): self.op.review(self.p['id'],'a'*64)
        self.assertEqual('pending_review',self.c.load('providers',self.p['id'])['state'])

    def test_foreign_onboarding_url_rejected(self):
        self.op.create_account(self.p['id']); original=self.stripe.request
        def unsafe(method,path,data=None,key=None):
            if path=='/v1/account_links': return {'url':'https://connect.stripe.com.evil.example/setup','expires_at':time.time()+300}
            return original(method,path,data,key)
        self.stripe.request=unsafe
        with self.assertRaises(ValueError): self.op.onboarding_link(self.p['id'])

    def test_adopt_existing_account_no_create_and_no_approval(self):
        original=self.stripe.request
        def manual(method,path,data=None,key=None):
            result=original(method,path,data,key)
            if path=='/v1/accounts/acct_fixture': result.update(type='express',metadata={})
            return result
        self.stripe.request=manual
        self.op.adopt_account(self.p['id'],'acct_fixture')
        self.op.adopt_account(self.p['id'],'acct_fixture')
        self.op.onboarding_link(self.p['id'])
        self.op.create_account(self.p['id'])
        self.assertFalse(any(method=='POST' and path=='/v1/accounts' for method,path,_,_ in self.calls))
        self.assertEqual('pending_review',self.c.load('providers',self.p['id'])['state'])
        other=MarketOperator(self.c.market).issue_credential('other')
        provider=self.c.apply(other,'Other',TERMS_SHA,True)
        with self.assertRaises(ValueError): self.op.adopt_account(provider['id'],'acct_fixture')


class ControllerConfigurationTests(unittest.TestCase):
    def test_explicit_controller_compatibility(self):
        from resultgate.commerce.connect_test import compatible_express
        a={'type':'none','controller':{'stripe_dashboard':{'type':'express'},
            'requirement_collection':'stripe','fees':{'payer':'application'},
            'losses':{'payments':'application'}}}
        self.assertTrue(compatible_express(a))
        a['controller']['fees']['payer']='account'
        self.assertFalse(compatible_express(a))
        self.assertFalse(compatible_express({'type':'none'}))
