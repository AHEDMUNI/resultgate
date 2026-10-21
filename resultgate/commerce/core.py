"""15% marketplace sandbox using existing tenant credentials and atomic store.

No live switch exists. Trusted operator decisions are not exposed through MCP.
"""
import hashlib
import json
import re
import secrets
import time
from ..network.registry import atomic
from ..network.market import identifier

TERMS = ('ResultGate sandbox terms v2: no joining or monthly fee; 15% of eligible USD '
         'service payment, rounded half-up to cents, due on successful payment, not completion. '
         'No customer recommendation fee. No fee on clicks/unpaid orders. Refunds reverse '
         'the fee proportionately; disputes suspend entitlement, lost disputes reverse it. '
         'Provider remainder is 85% before processing costs/adjustments. Processor costs '
         'are separate and require agreed allocation. No resale without permission. '
         'This sandbox acceptance is NOT a binding live commercial agreement.')
TERMS_SHA = hashlib.sha256(TERMS.encode()).hexdigest()


COMMISSION_BPS = 1500
LEGACY_TERMS_SHA = '2e54726ffb21396e3a49e1725cf9f63e3d222cb46885db47fe94b1bd4e814488'


def fee(cents, bps=COMMISSION_BPS):
    if type(cents) is not int or not 0 <= cents <= 10000000:
        raise ValueError('bounded integer cents required')
    if type(bps) is not int or bps not in (500, COMMISSION_BPS):
        raise ValueError('unsupported commission rate')
    return (cents * bps + 5000) // 10000


def order_rate(order):
    # Pre-v2 orders are recognized only by the immutable legacy terms digest.
    bps = order.get('commission_bps')
    if bps is None and order.get('terms_sha') == LEGACY_TERMS_SHA:
        bps = 500
    expected_terms = LEGACY_TERMS_SHA if bps == 500 else TERMS_SHA
    if order.get('terms_sha') != expected_terms or fee(order['amount'], bps) != order['fee']:
        raise ValueError('frozen order commission mismatch')
    return bps


def hashed(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def bounded(value, maximum=200):
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or any(ord(c)<32 for c in value):
        raise ValueError('bounded text required')
    return value


class Commerce:
    def __init__(self, market):
        self.market, self.store, self.db = market, market.store, market.db
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS commerce_providers(id TEXT PRIMARY KEY, owner TEXT UNIQUE, data TEXT);
        CREATE TABLE IF NOT EXISTS commerce_services(id TEXT PRIMARY KEY, provider TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS commerce_orders(id TEXT PRIMARY KEY, owner TEXT, request_key TEXT, data TEXT, UNIQUE(owner,request_key));
        CREATE TABLE IF NOT EXISTS commerce_sessions(id TEXT PRIMARY KEY, order_id TEXT UNIQUE, url TEXT);
        CREATE TABLE IF NOT EXISTS commerce_payments(id TEXT PRIMARY KEY, order_id TEXT UNIQUE, gross INTEGER, refunded INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS commerce_disputes(id TEXT PRIMARY KEY, payment TEXT, amount INTEGER, status TEXT, created INTEGER);
        CREATE TABLE IF NOT EXISTS commerce_events(id TEXT PRIMARY KEY, digest TEXT);
        CREATE TABLE IF NOT EXISTS commerce_ledger(event TEXT PRIMARY KEY, order_id TEXT, postings TEXT);
        CREATE TABLE IF NOT EXISTS commerce_grants(id TEXT PRIMARY KEY, owner TEXT, service TEXT, cap INTEGER, used INTEGER, expires REAL, active INTEGER);
        ''')

    def actor(self, token):
        return self.market._auth(token)['tenant_hash']

    def load(self, table, key):
        if table not in ('providers', 'services', 'orders'):
            raise ValueError('unknown object')
        row = self.db.execute('SELECT data FROM commerce_'+table+' WHERE id=?', (key,)).fetchone()
        if not row:
            raise ValueError('unknown or inaccessible object')
        return json.loads(row[0])

    def save(self, table, value):
        if table not in ('providers', 'services', 'orders'):
            raise ValueError('unknown object')
        self.db.execute('UPDATE commerce_'+table+' SET data=? WHERE id=?', (json.dumps(value), value['id']))

    @atomic
    def apply(self, token, name, terms_sha, authorized_signatory):
        owner = self.actor(token)
        bounded(name)
        if terms_sha != TERMS_SHA or authorized_signatory is not True:
            raise ValueError('current sandbox terms and signatory declaration required')
        old = self.db.execute('SELECT data FROM commerce_providers WHERE owner=?', (owner,)).fetchone()
        if old:
            p = json.loads(old[0])
            if p['terms_sha'] != TERMS_SHA:
                p.setdefault('terms_history', []).append({'terms_sha': p['terms_sha'], 'accepted_at': p['accepted_at']})
                p.update(terms_sha=TERMS_SHA, accepted_at=time.time(), commission_bps=COMMISSION_BPS, state='pending_review', live_agreement=False)
                self.save('providers', p)
            return p
        if self.db.execute('SELECT count(*) FROM commerce_providers').fetchone()[0] >= 1000:
            raise ValueError('capacity reached')
        p = {'id': secrets.token_hex(16), 'owner': owner, 'name': name, 'state': 'pending_review',
             'terms_sha': terms_sha, 'accepted_at': time.time(), 'mode': 'test',
             'authorized_signatory_declared': True, 'identity_verified': False,
             'account': None, 'commission_bps': COMMISSION_BPS, 'live_agreement': False}
        self.db.execute('INSERT INTO commerce_providers VALUES(?,?,?)', (p['id'], owner, json.dumps(p)))
        return p

    @atomic
    def list_service(self, token, provider_id, service_id, title, capability, price_cents):
        owner = self.actor(token); p = self.load('providers', provider_id)
        if p['owner'] != owner or p['state'] != 'approved_test' or p['terms_sha'] != TERMS_SHA:
            raise ValueError('reviewed provider ownership required')
        identifier(service_id); identifier(capability); bounded(title)
        fee(price_cents)
        if price_cents < 50:
            raise ValueError('minimum test price is 50 cents')
        # Immutable price/version avoids changing a previously approved offer.
        s = {'id': service_id, 'provider_id': provider_id, 'title': title, 'capability': capability,
             'price_cents': price_cents, 'currency': 'usd', 'commission_bps': COMMISSION_BPS,
             'mode': 'test', 'terms_sha': TERMS_SHA}
        old = self.db.execute('SELECT data FROM commerce_services WHERE id=?', (service_id,)).fetchone()
        if old:
            if json.loads(old[0]) != s:
                raise ValueError('immutable service id conflict; create a new version')
            return s
        if self.db.execute('SELECT count(*) FROM commerce_services').fetchone()[0] >= 5000:
            raise ValueError('capacity reached')
        self.db.execute('INSERT INTO commerce_services VALUES(?,?,?)', (service_id, provider_id, json.dumps(s)))
        return s

    def search(self, token, capability=None):
        self.actor(token)
        if capability is not None: identifier(capability)
        services = [json.loads(r[0]) for r in self.db.execute('SELECT data FROM commerce_services LIMIT 5000')]
        return {'mode': 'test', 'ranking': 'exact capability, then price, then stable id; no commission weighting',
                'services': sorted([s for s in services if (capability is None or s['capability']==capability)
                    and s['terms_sha']==TERMS_SHA and self.load('providers', s['provider_id'])['terms_sha']==TERMS_SHA
                    and self.load('providers', s['provider_id'])['state']=='approved_test'],
                    key=lambda s:(s['price_cents'],s['id']))[:50]}

    @atomic
    def order(self, token, service_id, request_key):
        owner = self.actor(token); identifier(request_key)
        old = self.db.execute('SELECT data FROM commerce_orders WHERE owner=? AND request_key=?', (owner,request_key)).fetchone()
        if old:
            order=json.loads(old[0])
            if order['service_id'] != service_id: raise ValueError('idempotency conflict')
            return order
        s=self.load('services',service_id); p=self.load('providers',s['provider_id'])
        if p['state']!='approved_test' or p['terms_sha']!=TERMS_SHA or s['terms_sha']!=TERMS_SHA:
            raise ValueError('provider unavailable or current terms required')
        if self.db.execute('SELECT count(*) FROM commerce_orders').fetchone()[0]>=10000:
            raise ValueError('capacity reached')
        o={'id':secrets.token_hex(16),'owner':owner,'service_id':service_id,'provider_id':p['id'],
           'account':p['account'],'amount':s['price_cents'],'currency':'usd','fee':fee(s['price_cents']),
           'commission_bps':COMMISSION_BPS,'terms_sha':TERMS_SHA,'expires':int(time.time()+3600),'state':'awaiting_owner',
           'mode':'test','approval':None,'commission_cents':0,'net_eligible_cents':0,
           'real_revenue_cents':0,'settlement_confirmed':False}
        o['quote_sha']=hashed({k:v for k,v in o.items() if k!='approval'})
        grant=self.db.execute('SELECT id,expires FROM commerce_grants WHERE owner=? AND service=? AND active=1 AND expires>? AND cap-used>=? ORDER BY expires,id LIMIT 1',
                              (owner,service_id,time.time(),o['amount'])).fetchone()
        if grant:
            self.db.execute('UPDATE commerce_grants SET used=used+? WHERE id=?',(o['amount'],grant[0]))
            o['approval']={'grant':grant[0],'expires':min(grant[1],o['expires']),'cap':o['amount'],'quote_sha':o['quote_sha']}
        self.db.execute('INSERT INTO commerce_orders VALUES(?,?,?,?)',(o['id'],owner,request_key,json.dumps(o)))
        return o

    def get(self, token, order_id):
        owner=self.actor(token); o=self.load('orders',order_id)
        if o['owner']!=owner and self.load('providers',o['provider_id'])['owner']!=owner:
            raise ValueError('unknown or inaccessible order')
        return o

    @atomic
    def checkout_payload(self, token, order_id):
        o=self.get(token,order_id)
        order_rate(o)
        if o['state'] == 'cancelled_test': raise ValueError('order cancelled')
        if o['owner']!=self.actor(token): raise ValueError('requester required')
        p=self.load('providers',o['provider_id'])
        if p['state']!='approved_test' or p['account']!=o['account']:
            raise ValueError('provider unavailable')
        approval=o['approval']
        if not approval or approval['expires']<=time.time() or o['expires']<=time.time():
            raise ValueError('current owner approval required')
        if approval.get('quote_sha') != o['quote_sha'] or type(approval.get('cap')) is not int or approval['cap'] < o['amount']:
            raise ValueError('approval quote or budget mismatch')
        if approval.get('grant'):
            row=self.db.execute('SELECT active,expires FROM commerce_grants WHERE id=?',(approval['grant'],)).fetchone()
            if not row or not row[0] or row[1]<=time.time(): raise ValueError('grant revoked/expired')
        s=self.load('services',o['service_id'])
        return {'mode':'payment',
                'line_items[0][price_data][currency]':'usd',
                'line_items[0][price_data][unit_amount]':str(o['amount']),
                'line_items[0][price_data][product_data][name]':s['title'],
                'line_items[0][quantity]':'1','client_reference_id':o['id'],
                'metadata[order_id]':o['id'],
                'payment_intent_data[metadata][order_id]':o['id'],
                'payment_intent_data[application_fee_amount]':str(o['fee']),
                'payment_intent_data[transfer_data][destination]':o['account']}

    @atomic
    def bind_session(self, order_id, session):
        o=self.load('orders',order_id)
        if session.get('livemode') is not False or not str(session.get('id','')).startswith('cs_test_'):
            raise ValueError('test session required')
        if session.get('client_reference_id')!=order_id or session.get('amount_total')!=o['amount'] or session.get('currency')!='usd':
            raise ValueError('checkout binding mismatch')
        from urllib.parse import urlsplit
        u=urlsplit(session.get('url',''))
        if u.scheme!='https' or u.netloc!='checkout.stripe.com': raise ValueError('unexpected checkout URL')
        old=self.db.execute('SELECT id,url FROM commerce_sessions WHERE order_id=?',(order_id,)).fetchone()
        if old and old!=(session['id'],session['url']): raise ValueError('checkout conflict')
        self.db.execute('INSERT OR IGNORE INTO commerce_sessions VALUES(?,?,?)',(session['id'],order_id,session['url']))
        o['state']='checkout_pending'; self.save('orders',o)
        return {'checkout_url':session['url'],'mode':'test','order_id':order_id}

    def dashboard(self, token):
        owner=self.actor(token)
        ids=[r[0] for r in self.db.execute('SELECT id FROM commerce_providers WHERE owner=?',(owner,))]
        orders=[json.loads(r[0]) for r in self.db.execute('SELECT data FROM commerce_orders LIMIT 10000')]
        return {'mode':'test','real_revenue_cents':0,'orders':[
            {k:o[k] for k in ('id','service_id','amount','state','commission_cents','net_eligible_cents','settlement_confirmed')}
            for o in orders if o['provider_id'] in ids]}

    def reconcile(self, order_id, event_id):
        o=self.load('orders',order_id)
        pay=self.db.execute('SELECT id,gross,refunded FROM commerce_payments WHERE order_id=?',(order_id,)).fetchone()
        disputed=self.db.execute("SELECT coalesce(sum(amount),0) FROM commerce_disputes WHERE payment=? AND status NOT IN ('won','warning_closed')",(pay[0],)).fetchone()[0]
        net=max(0,pay[1]-pay[2]-disputed); commission=fee(net, order_rate(o))
        delta=net-o['net_eligible_cents']; df=commission-o['commission_cents']
        postings={'test_processor_clearing':delta,'test_provider_entitlement':-(delta-df),'test_platform_commission':-df}
        self.db.execute('INSERT INTO commerce_ledger VALUES(?,?,?)',(event_id,order_id,json.dumps(postings)))
        o.update(net_eligible_cents=net,commission_cents=commission,
                 state='paid_test' if not pay[2] and not disputed else 'adjusted_test')
        self.save('orders',o)
        return {'mode':'test','duplicate':False,'commission_cents':commission,'real_revenue_cents':0,
                'settlement_reconciliation_required':True}

    @atomic
    def event(self, event):
        if event.get('livemode') is not False: raise ValueError('live events forbidden')
        eid=identifier(event['id']); fingerprint=hashed(event)
        old=self.db.execute('SELECT digest FROM commerce_events WHERE id=?',(eid,)).fetchone()
        if old:
            if old[0]!=fingerprint: raise ValueError('event id conflict')
            return {'duplicate':True,'mode':'test'}
        if self.db.execute('SELECT count(*) FROM commerce_events').fetchone()[0]>=100000:
            raise ValueError('event capacity reached; reconcile before retry')
        kind=event['type']; obj=event['data']['object']
        if kind in ('checkout.session.completed','checkout.session.async_payment_succeeded'):
            if obj.get('payment_status')!='paid': return {'ignored':'not_paid','mode':'test'}
            row=self.db.execute('SELECT order_id FROM commerce_sessions WHERE id=?',(obj['id'],)).fetchone()
            if not row: raise ValueError('unbound session; retry after reconciliation')
            oid=row[0]; o=self.load('orders',oid)
            if (obj.get('metadata',{}).get('order_id')!=oid or obj.get('client_reference_id')!=oid
                or obj.get('amount_total')!=o['amount'] or obj.get('currency')!='usd'):
                raise ValueError('payment mismatch')
            payment=identifier(obj['payment_intent'])
            oldpay=self.db.execute('SELECT id FROM commerce_payments WHERE order_id=?',(oid,)).fetchone()
            if oldpay:
                if oldpay[0]!=payment: raise ValueError('second payment for order requires review')
                self.db.execute('INSERT INTO commerce_events VALUES(?,?)',(eid,fingerprint))
                return {'duplicate':True,'mode':'test'}
            self.db.execute('INSERT INTO commerce_payments(id,order_id,gross) VALUES(?,?,?)',(payment,oid,o['amount']))
        elif kind=='charge.refunded' or kind.startswith('charge.dispute.'):
            payment=identifier(obj['payment_intent'])
            row=self.db.execute('SELECT order_id,gross,refunded FROM commerce_payments WHERE id=?',(payment,)).fetchone()
            if not row: raise ValueError('payment not yet known; retry')
            oid,gross,refunded=row
            if obj.get('currency')!='usd': raise ValueError('currency mismatch')
            if kind=='charge.refunded':
                amount=obj.get('amount_refunded'); fee(amount)
                if obj.get('amount')!=gross or amount>gross: raise ValueError('refund mismatch')
                self.db.execute('UPDATE commerce_payments SET refunded=? WHERE id=?',(max(refunded,amount),payment))
            else:
                if kind not in ('charge.dispute.created','charge.dispute.updated','charge.dispute.closed'):
                    return {'ignored':'unsupported dispute event'}
                amount=obj['amount']; fee(amount); did=identifier(obj['id']); status=obj['status']
                if amount>gross or status not in ('needs_response','under_review','won','lost','warning_needs_response','warning_under_review','warning_closed'):
                    raise ValueError('invalid dispute')
                prior=self.db.execute('SELECT payment,status,created FROM commerce_disputes WHERE id=?',(did,)).fetchone()
                created=event['created']
                if type(created) is not int: raise ValueError('event timestamp required')
                if prior and prior[0]!=payment: raise ValueError('dispute payment conflict')
                if not prior or ((created>prior[2] or (created==prior[2] and status in ('won','lost','warning_closed'))) and prior[1] not in ('won','lost','warning_closed')):
                    self.db.execute('INSERT OR REPLACE INTO commerce_disputes VALUES(?,?,?,?,?)',(did,payment,amount,status,created))
        else: return {'ignored':'unsupported_event','mode':'test'}
        self.db.execute('INSERT INTO commerce_events VALUES(?,?)',(eid,fingerprint))
        return self.reconcile(oid,eid)


class CommerceOperator:
    """Trusted local reviewer only. Never bind these methods to MCP or public routes."""
    def __init__(self, commerce):
        self.c=commerce; self.store=commerce.store; self.db=commerce.db

    @atomic
    def review_provider(self, pid, account, evidence_sha):
        p=self.c.load('providers',pid)
        if p['terms_sha'] != TERMS_SHA: raise ValueError('current provider terms required')
        if not re.fullmatch(r'acct_[a-zA-Z0-9]+',account) or not re.fullmatch(r'[a-f0-9]{64}',evidence_sha):
            raise ValueError('test account and reviewer evidence required')
        other=self.db.execute('SELECT data FROM commerce_providers WHERE id<>?',(pid,)).fetchall()
        if any(json.loads(r[0]).get('account')==account for r in other): raise ValueError('account already bound')
        p.update(state='approved_test',account=account,review_evidence_sha=evidence_sha)
        self.c.save('providers',p)
        return p

    @atomic
    def approve_order(self, oid, owner_hash, quote_sha, cap, expires):
        o=self.c.load('orders',oid); fee(cap)
        if o['state'] == 'cancelled_test': raise ValueError('order cancelled')
        if owner_hash!=o['owner'] or quote_sha!=o['quote_sha'] or cap<o['amount'] or not time.time()<expires<=o['expires']:
            raise ValueError('owner, quote, budget or expiry mismatch')
        o['approval']={'quote_sha':quote_sha,'cap':cap,'expires':expires,'source':'owner_review'}
        self.c.save('orders',o)

    @atomic
    def grant(self, owner_hash, service_id, cap, expires):
        self.c.load('services',service_id); fee(cap)
        if not re.fullmatch(r'[a-f0-9]{64}',owner_hash) or not time.time()<expires<=time.time()+86400:
            raise ValueError('bounded owner grant required')
        gid=secrets.token_hex(16)
        self.db.execute('INSERT INTO commerce_grants VALUES(?,?,?,?,0,?,1)',(gid,owner_hash,service_id,cap,expires))
        return gid

    @atomic
    def use_grant(self, oid, gid):
        o=self.c.load('orders',oid)
        if o['approval']: return o
        row=self.db.execute('SELECT owner,service,cap,used,expires,active FROM commerce_grants WHERE id=?',(gid,)).fetchone()
        if not row or row[0]!=o['owner'] or row[1]!=o['service_id'] or row[4]<=time.time() or not row[5] or row[3]+o['amount']>row[2]:
            raise ValueError('grant unavailable or exhausted')
        self.db.execute('UPDATE commerce_grants SET used=used+? WHERE id=?',(o['amount'],gid))
        o['approval']={'grant':gid,'expires':min(row[4],o['expires']),'cap':o['amount'],'quote_sha':o['quote_sha']}
        self.c.save('orders',o)
        return o

    @atomic
    def revoke_grant(self, gid):
        self.db.execute('UPDATE commerce_grants SET active=0 WHERE id=?',(gid,))
