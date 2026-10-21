"""Stripe test-mode Checkout adapter. No live key, real payout or account creation."""
import hashlib
import hmac
import json
import time
import re
from urllib.parse import urlsplit
import httpx


class StripeRequestRejected(ValueError):
    """Only approved diagnostic fields; never retains Stripe message/body/headers."""
    def __init__(self, status, response):
        self.safe = {'http_status': int(status)}
        try:
            error = json.loads(response).get('error', {})
            kinds = {'invalid_request_error','authentication_error','api_error','card_error','idempotency_error','rate_limit_error'}
            codes = {'parameter_missing','parameter_unknown','parameter_invalid_integer',
                     'parameter_invalid_string_blank','parameter_invalid_empty','resource_missing',
                     'account_invalid','account_country_invalid_address','balance_insufficient',
                     'transfers_not_allowed','platform_account_required','url_invalid',
                     'idempotency_key_in_use','testmode_charges_only','payment_intent_invalid_parameter',
                     'amount_too_small','amount_too_large'}
            params = {'expires_at','success_url','cancel_url','mode','currency','account','amount',
                      'payment_intent','reverse_transfer','refund_application_fee',
                      'payment_intent_data[transfer_data][destination]',
                      'payment_intent_data[application_fee_amount]',
                      'line_items[0][price_data][currency]','line_items[0][price_data][unit_amount]'}
            self.safe.update(error_type=error.get('type') if error.get('type') in kinds else 'other',
                             error_code=error.get('code') if error.get('code') in codes else 'other',
                             parameter=error.get('param') if error.get('param') in params else 'other')
        except (ValueError,TypeError,AttributeError): pass
        super().__init__('stripe_request_rejected')


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
                (method == 'GET' and (re.fullmatch(allowed_get, path) or path=='/v1/checkout/sessions'))):
            raise ValueError('unsupported test operation')
        if method=='GET' and path=='/v1/checkout/sessions':
            if not isinstance(data,dict) or set(data)-{'limit','created[gte]','starting_after'} or data.get('limit')!='100':
                raise ValueError('bounded session audit required')
        headers={'Authorization':'Bearer '+self.secret}
        if key: headers['Idempotency-Key']=key
        with httpx.Client(timeout=15,trust_env=False,follow_redirects=False,transport=self.transport) as client:
            with client.stream(method,'https://api.stripe.com'+path,headers=headers,params=data if method=='GET' else None,data=data if method!='GET' else None) as r:
                body=bytearray()
                for chunk in r.iter_bytes():
                    body.extend(chunk)
                    if len(body)>1024*1024: raise ValueError('Stripe response too large')
                if r.status_code>=300: raise StripeRequestRejected(r.status_code,body)
        result=json.loads(body)
        if not isinstance(result,dict): raise ValueError('invalid response')
        if result.get('livemode') is True: raise ValueError('live response forbidden')
        return result

    def repair_dynamic_methods_rejection(self, commerce, oid):
        """Private operator recovery ONLY after confirmed deprecated-parameter 400.

        Audit every Sandbox Checkout since this order began; any matching session
        or uncertain/truncated scan blocks changing the idempotency key.
        """
        from .core import hashed
        db=commerce.db
        db.execute('CREATE TABLE IF NOT EXISTS commerce_checkout_repairs (order_id TEXT PRIMARY KEY, digest TEXT, created REAL, state TEXT, evidence TEXT)')
        if db.execute('SELECT 1 FROM commerce_checkout_repairs WHERE order_id=?',(oid,)).fetchone(): return
        old=db.execute('SELECT digest,created,state FROM commerce_checkout_attempts WHERE order_id=?',(oid,)).fetchone()
        if not old or old[2]!='http_400': raise RuntimeError('repair_requires_confirmed_validation_rejection')
        if db.execute('SELECT 1 FROM commerce_sessions WHERE order_id=?',(oid,)).fetchone() or db.execute('SELECT 1 FROM commerce_payments WHERE order_id=?',(oid,)).fetchone():
            raise RuntimeError('repair_existing_checkout_requires_review')
        o=commerce.load('orders',oid)
        params={'limit':'100','created[gte]':str(o['expires']-3600-60)}
        scanned=0
        for _ in range(20):
            page=self.request('GET','/v1/checkout/sessions',params)
            if not isinstance(page.get('data'),list) or type(page.get('has_more')) is not bool:
                raise RuntimeError('repair_audit_incomplete')
            for session in page['data']:
                if session.get('livemode') is not False: raise RuntimeError('repair_audit_incomplete')
                if session.get('client_reference_id')==oid or session.get('metadata',{}).get('order_id')==oid:
                    raise RuntimeError('repair_existing_checkout_requires_review')
                scanned+=1
            if not page['has_more']: break
            if not page['data'] or not re.fullmatch(r'cs_test_[A-Za-z0-9]+',page['data'][-1].get('id','')):
                raise RuntimeError('repair_audit_incomplete')
            params['starting_after']=page['data'][-1]['id']
        else: raise RuntimeError('repair_audit_incomplete')
        # Current owner request authorizes this same $100 Sandbox attempt. Renew only
        # inside the ORIGINAL order lifetime, after no-session proof, before new POST.
        if o['expires'] < time.time()+1800: raise RuntimeError('repair_original_order_expired_review')
        if o.get('approval') and o['approval']['expires'] < time.time()+1800:
            o['approval']['expires']=o['expires']
        proof={'cause':'owner_confirmed_unsupported_payment_method_types_HTTP400',
               'original_attempt':list(old),'original_key':'rg-test-'+oid,
               'audit_lower_bound':params['created[gte]'],'sessions_scanned':scanned,
               'no_matching_session':True,'reviewed_at':time.time()}
        with db:
            commerce.save('orders',o)
            db.execute('INSERT INTO commerce_checkout_repairs VALUES(?,?,?,?,?)',
                       (oid,None,time.time(),'prepared',json.dumps(proof)))
        return {'order_id':oid,'audit_sha':hashed(proof),'sessions_scanned':scanned,'replacement_key':'rg-test-dynamic-v1-'+oid}

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
        # Persist frozen parameters BEFORE POST. Never roll an uncertain request onto
        # another key/order, or reuse Stripe's key after its retention window.
        from .core import hashed
        commerce.db.execute('CREATE TABLE IF NOT EXISTS commerce_checkout_attempts (order_id TEXT PRIMARY KEY, digest TEXT, created REAL, state TEXT)')
        digest=hashed(payload)
        with commerce.db:
            commerce.db.execute('INSERT OR IGNORE INTO commerce_checkout_attempts VALUES(?,?,?,?)',(oid,digest,time.time(),'started'))
        commerce.db.execute('CREATE TABLE IF NOT EXISTS commerce_checkout_repairs (order_id TEXT PRIMARY KEY, digest TEXT, created REAL, state TEXT, evidence TEXT)')
        repaired=commerce.db.execute('SELECT 1 FROM commerce_checkout_repairs WHERE order_id=?',(oid,)).fetchone()
        attempt_table='commerce_checkout_repairs' if repaired else 'commerce_checkout_attempts'
        stripe_key=('rg-test-dynamic-v1-' if repaired else 'rg-test-')+oid
        if repaired:
            with commerce.db:
                commerce.db.execute('UPDATE commerce_checkout_repairs SET digest=? WHERE order_id=? AND digest IS NULL',(digest,oid))
        attempt=commerce.db.execute('SELECT digest,created FROM '+attempt_table+' WHERE order_id=?',(oid,)).fetchone()
        if attempt[0]!=digest: raise ValueError('Checkout parameters changed; inspect original request before retry')
        if time.time()-attempt[1]>23*3600: raise ValueError('Checkout retry window expired; inspect Stripe before retry')
        try:
            session=self.request('POST','/v1/checkout/sessions',payload,stripe_key)
        except StripeRequestRejected as error:
            # A rejection is diagnostic evidence, not authority to change the key.
            with commerce.db:
                commerce.db.execute('UPDATE '+attempt_table+' SET state=? WHERE order_id=?',('http_'+str(error.safe['http_status']),oid))
            raise
        result=commerce.bind_session(oid,session)
        with commerce.db:
            commerce.db.execute('UPDATE '+attempt_table+' SET state=? WHERE order_id=?',('bound',oid))
        return result


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
