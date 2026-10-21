"""Stripe test-mode Checkout adapter. No live key, real payout or account creation."""
import hashlib
import hmac
import json
import time
import re
from urllib.parse import urlsplit
import httpx


class StripeTest:
    def __init__(self, secret, origin, enabled=False, transport=None):
        if not enabled or not isinstance(secret,str) or not secret.startswith('sk_test_'):
            raise ValueError('explicit test opt-in and test secret required; live keys forbidden')
        p=urlsplit(origin)
        if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ('','/'):
            raise ValueError('fixed HTTPS return origin required')
        self.secret=secret; self.origin=origin.rstrip('/'); self.transport=transport

    def request(self, method, path, data=None, key=None):
        allowed_post = {'/v1/checkout/sessions', '/v1/accounts', '/v1/account_links', '/v1/refunds'}
        allowed_get = r'/v1/(accounts/acct_|payment_intents/pi_|charges/ch_|application_fees/fee_|transfers/tr_|balance_transactions/txn_|refunds/re_)[A-Za-z0-9]+'
        if not ((method == 'POST' and path in allowed_post) or
                (method == 'GET' and re.fullmatch(allowed_get, path))):
            raise ValueError('unsupported test operation')
        headers={'Authorization':'Bearer '+self.secret}
        if key: headers['Idempotency-Key']=key
        with httpx.Client(timeout=15,trust_env=False,follow_redirects=False,transport=self.transport) as client:
            with client.stream(method,'https://api.stripe.com'+path,headers=headers,data=data) as r:
                if r.status_code>=300: raise ValueError('Stripe test request rejected; inspect restricted operator logs')
                body=bytearray()
                for chunk in r.iter_bytes():
                    body.extend(chunk)
                    if len(body)>1024*1024: raise ValueError('Stripe response too large')
        result=json.loads(body)
        if not isinstance(result,dict): raise ValueError('invalid response')
        if result.get('livemode') is True: raise ValueError('live response forbidden')
        return result

    def checkout(self, commerce, token, oid):
        payload=commerce.checkout_payload(token,oid)
        prior=commerce.db.execute('SELECT url FROM commerce_sessions WHERE order_id=?',(oid,)).fetchone()
        if prior: return {'checkout_url':prior[0],'order_id':oid,'mode':'test','duplicate':True}
        o=commerce.get(token,oid)
        expires = int(min(o['expires'], o['approval']['expires']))
        if expires < time.time()+1800:
            raise ValueError('Checkout needs at least 30 minutes of remaining owner authorization')
        account=self.request('GET','/v1/accounts/'+o['account'])
        if (account.get('id')!=o['account'] or account.get('country')!='US'
            or account.get('charges_enabled') is not True or account.get('payouts_enabled') is not True
            or account.get('capabilities',{}).get('transfers')!='active'):
            raise ValueError('eligible US test connected account required')
        payload.update(success_url=self.origin+'/commerce/return',cancel_url=self.origin+'/commerce/cancel',
                       expires_at=str(expires))
        # Same order and parameters after timeout -> same Stripe idempotency key.
        session=self.request('POST','/v1/checkout/sessions',payload,'rg-test-'+oid)
        return commerce.bind_session(oid,session)


def verify_webhook(raw, signature, secret, now=None):
    if not isinstance(raw,bytes) or len(raw)>262144 or not secret.startswith('whsec_'):
        raise ValueError('bounded signed raw body required')
    if not isinstance(signature,str) or len(signature)>2048: raise ValueError('invalid signature')
    parts=[part.split('=',1) for part in signature.split(',')]
    timestamps=[v for k,v in parts if k=='t']
    if len(timestamps)!=1: raise ValueError('one timestamp required')
    timestamp=int(timestamps[0]); now=time.time() if now is None else now
    if abs(now-timestamp)>300: raise ValueError('expired signature')
    expected=hmac.new(secret.encode(),str(timestamp).encode()+b'.'+raw,hashlib.sha256).hexdigest()
    if not any(k=='v1' and hmac.compare_digest(expected,v) for k,v in parts):
        raise ValueError('invalid signature')
    def unique(pairs):
        value={}
        for k,v in pairs:
            if k in value: raise ValueError('duplicate JSON key')
            value[k]=v
        return value
    event=json.loads(raw,object_pairs_hook=unique)
    if event.get('livemode') is not False: raise ValueError('live events forbidden')
    return event


def refund_plan(payment_intent, cents):
    from .core import fee
    fee(cents)
    if not isinstance(payment_intent,str) or not payment_intent.startswith('pi_') or cents==0:
        raise ValueError('payment and positive amount required')
    return {'endpoint':'/v1/refunds','parameters':{'payment_intent':payment_intent,'amount':cents,
            'reverse_transfer':True,'refund_application_fee':True},'execution_enabled':False,
            'note':'Operator review only. No refund API calls or transfers are implemented.'}
