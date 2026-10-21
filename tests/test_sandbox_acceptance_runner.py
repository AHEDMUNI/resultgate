"""New runner boundaries only; these are NOT evidence of a Stripe payment."""
import hashlib
import hmac
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from http.client import HTTPConnection

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import stripe_sandbox_acceptance as runner


class AcceptanceRunnerTests(unittest.TestCase):
    def test_real_http_signature_rejects_forgery_and_accepts_signed_event(self):
        class Commerce:
            calls=[]
            def event(self,event):
                self.calls.append(event['id'])
                return {'duplicate':len(self.calls)>1}
        with tempfile.TemporaryDirectory() as d:
            server=runner.HTTPServer(('127.0.0.1',0),runner.Receiver)
            server.timeout=1;server.signing='whsec_fixture';server.order='order_fixture'
            server.events={};server.commerce=Commerce();server.directory=Path(d)
            event={'id':'evt_fixture','livemode':False,'type':'checkout.session.completed',
                   'data':{'object':{'client_reference_id':'order_fixture'}}}
            raw=json.dumps(event).encode();stamp=str(int(time.time()))
            good=hmac.new(b'whsec_fixture',stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
            try:
                for signature,expected in [('t='+stamp+',v1=wrong',400),('t='+stamp+',v1='+good,200)]:
                    worker=threading.Thread(target=server.handle_request);worker.start()
                    c=HTTPConnection('127.0.0.1',server.server_port,timeout=2)
                    c.request('POST','/webhook',body=raw,headers={'Stripe-Signature':signature})
                    self.assertEqual(expected,c.getresponse().status);c.close();worker.join(2)
                self.assertEqual(['evt_fixture','evt_fixture'],server.commerce.calls)
                self.assertTrue(server.events['evt_fixture']['signature_verified'])
                self.assertNotIn('whsec_', (Path(d)/'signed-events.json').read_text())
            finally: server.server_close()

    def test_cli_key_not_in_arguments_and_raw_output_not_printed(self):
        class Process:
            stdout=io.StringIO('Ready! webhook signing secret is whsec_FAKEONLY\n')
        class Server: signing=None
        server=Server()
        with patch.object(runner.subprocess,'Popen',return_value=Process()) as call, patch('builtins.print') as output:
            runner.start_listener('/private/stripe','sk_test_FAKE_ONLY',server,'/private/ephemeral')
        args,kwargs=call.call_args
        self.assertNotIn('sk_test_',str(args))
        self.assertEqual('sk_test_FAKE_ONLY',kwargs['env']['STRIPE_API_KEY'])
        self.assertEqual(runner.subprocess.DEVNULL,kwargs['stdin'])
        self.assertEqual('whsec_FAKEONLY',server.signing)
        output.assert_not_called()

    def test_cli_checksum_mismatch_never_creates_executable(self):
        class Opener:
            def open(self,*args,**kwargs): return io.BytesIO(b'corrupt fixture download')
        with tempfile.TemporaryDirectory() as d,patch.object(runner.urllib.request,'build_opener',return_value=Opener()),patch('builtins.print'):
            with self.assertRaisesRegex(RuntimeError,'cli_integrity_failed'):
                runner.cli_binary(Path(d))
            self.assertFalse((Path(d)/'stripe-1.54.1').exists())

    def test_stripe_rejection_exposes_only_allowlisted_diagnostics(self):
        import httpx
        from resultgate.commerce.stripe_test import StripeTest, StripeRequestRejected
        secret='sk_test_FAKEONLY'
        payload={'error':{'type':'invalid_request_error','code':'parameter_unknown',
                          'param':'expires_at','message':secret,'request_log_url':'https://private.example'}}
        adapter=StripeTest(secret,'https://example.com',True,httpx.MockTransport(lambda req:httpx.Response(400,json=payload)))
        with self.assertRaises(StripeRequestRejected) as raised:adapter.request('POST','/v1/checkout/sessions',{})
        e=raised.exception
        self.assertEqual({'http_status':400,'error_type':'invalid_request_error','error_code':'parameter_unknown','parameter':'expires_at'},e.safe)
        self.assertNotIn(secret,str(e)+str(vars(e)))
        poisoned=StripeRequestRejected(400,json.dumps({'error':{'type':secret,'code':secret,'param':secret,'message':secret}}))
        self.assertNotIn(secret,str(vars(poisoned)))
