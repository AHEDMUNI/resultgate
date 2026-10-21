"""Local sandbox routes for people, provider dashboards and signed Stripe events.

Not wired into production nginx. Reuse existing private registry and tenant tokens.
"""
import asyncio
import ipaddress
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route
from starlette.middleware.base import BaseHTTPMiddleware
from .core import TERMS, TERMS_SHA
from .stripe_test import verify_webhook


def create_app(commerce, stripe=None, webhook_secret=None):
    def reply(data,status=200):
        return JSONResponse(data,status_code=status,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    async def read(request):
        data=bytearray()
        async with asyncio.timeout(5):
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data)>262144: raise ValueError('body limit')
        return bytes(data)
    async def handle(request):
        try:
            if request.url.path=='/commerce/webhook':
                if not webhook_secret: return reply({'blocked':'webhook not configured'},503)
                raw=await read(request)
                try: event=verify_webhook(raw,request.headers.get('stripe-signature',''),webhook_secret)
                except (ValueError,TypeError,KeyError): return reply({'error':'invalid_signature_or_payload'},400)
                try: return reply(commerce.event(event))
                except (ValueError,KeyError,TypeError): return reply({'error':'reconciliation_required_retry'},503)
            auth=request.headers.getlist('authorization')
            if len(auth)!=1 or not auth[0].startswith('Bearer '): return reply({'error':'unauthorized'},401)
            token=auth[0][7:]
            try: commerce.market.consume_request(token)
            except ValueError: return reply({'error':'invalid_or_exhausted_credential'},401)
            path=request.url.path
            if request.method=='GET':
                if path=='/commerce/terms': return reply({'terms':TERMS,'sha256':TERMS_SHA,'mode':'test'})
                if path=='/commerce/services': return reply(commerce.search(token))
                if path=='/commerce/dashboard': return reply(commerce.dashboard(token))
                return reply(commerce.get(token,request.path_params['order_id']))
            if request.headers.get('content-type','').split(';')[0]!='application/json': return reply({'error':'json_required'},415)
            data=json.loads(await read(request))
            if not isinstance(data,dict): raise ValueError('object required')
            if path=='/commerce/providers/apply': result=commerce.apply(token,**data)
            elif path=='/commerce/services': result=commerce.list_service(token,**data)
            elif path=='/commerce/orders': result=commerce.order(token,**data)
            else:
                if stripe is None: return reply({'blocked':'Stripe sandbox not configured'},503)
                result=stripe.checkout(commerce,token,request.path_params['order_id'])
            return reply(result)
        except (ValueError,KeyError,TypeError,TimeoutError): return reply({'error':'invalid_or_inaccessible_request'},400)
    async def landing(request):
        return HTMLResponse('<h1>ResultGate marketplace — sandbox</h1><p>No live payments. Providers: no joining or monthly fee; 15% of eligible paid transactions, adjusted for refunds and disputes. No service completion condition.</p><p>Invited providers use POST /commerce/providers/apply. Customers use GET /commerce/services and POST /commerce/orders with their own credential. Payment approval is an owner-only step.</p>',headers={'Content-Security-Policy':"default-src 'none'; frame-ancestors 'none'",'Cache-Control':'no-store'})
    routes=[Route('/commerce',landing),Route('/commerce/return',landing),Route('/commerce/cancel',landing),Route('/commerce/webhook',handle,methods=['POST']),
            Route('/commerce/terms',handle),Route('/commerce/providers/apply',handle,methods=['POST']),
            Route('/commerce/services',handle,methods=['GET','POST']),Route('/commerce/dashboard',handle),
            Route('/commerce/orders',handle,methods=['POST']),Route('/commerce/orders/{order_id}',handle),
            Route('/commerce/orders/{order_id}/checkout',handle,methods=['POST'])]
    app=Starlette(routes=routes)
    async def boundary(request,call_next):
        try:
            if not request.client or not ipaddress.ip_address(request.client.host).is_loopback:
                return reply({'error':'loopback_only'},403)
        except ValueError: return reply({'error':'loopback_only'},403)
        if request.headers.get('origin') or request.url.query or request.headers.get('forwarded') or request.headers.get('x-forwarded-for'):
            return reply({'error':'request_rejected'},403)
        if request.url.hostname not in ('localhost','127.0.0.1','::1'):
            return reply({'error':'host_rejected'},403)
        return await call_next(request)
    app.add_middleware(BaseHTTPMiddleware,dispatch=boundary)
    return app
