"""Loopback-only HTTP simulation harness. Not a public marketplace or payment API."""
import argparse
import asyncio
from contextlib import asynccontextmanager
import ipaddress
import json
from pathlib import Path
import re
import sqlite3
import time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import ClientDisconnect, Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from .catalog import catalog
from .market import Market, RequestBudgetExceeded
from .registry import Registry

MAX_BODY = 16384
BODY_TIMEOUT_SECONDS = 5

class CreateTask(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,100}$')
    task_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    success_criteria_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')

class AdvanceTask(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,100}$')
    state: Literal['offered','accepted','executing','completed','transaction_proven','failed','cancelled']
    evidence_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    consent_to_send: bool = False
    max_cost_micros: int = Field(default=0, ge=0, le=0)
    simulated_value_micros: int = Field(default=0, ge=0, le=10**15)
    simulated_transaction_id_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')

class Rejected(Exception):
    def __init__(self, status): self.status = status


def response(data, status=200):
    return JSONResponse(data, status_code=status, headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

async def body(request, model):
    if request.headers.get('content-type','').split(';')[0].strip().lower() != 'application/json':
        raise Rejected(415)
    raw = bytearray()
    try:
        async with asyncio.timeout(BODY_TIMEOUT_SECONDS):
            async for chunk in request.stream():
                if len(raw)+len(chunk)>MAX_BODY: raise Rejected(413)
                raw.extend(chunk)
    except TimeoutError:
        raise Rejected(408) from None
    except ClientDisconnect:
        raise Rejected(400) from None
    def unique(pairs):
        value={}
        for key,item in pairs:
            if key in value: raise ValueError('duplicate key')
            value[key]=item
        return value
    try:
        return model.model_validate(json.loads(raw, object_pairs_hook=unique)).model_dump()
    except (ValueError, UnicodeError, ValidationError, RecursionError):
        raise Rejected(400) from None


def create_app(directory):
    """Open an operator-initialized private Registry; never mint HTTP credentials."""
    path=Path(directory)
    if path.is_symlink() or not path.is_dir() or not (path/'identity.key').is_file() or not (path/'delegation.sqlite3').is_file():
        raise ValueError('existing operator-initialized private registry required')
    registry=Registry(path); market=Market(registry)
    window=[time.monotonic(),0]

    @asynccontextmanager
    async def lifespan(app):
        yield
        registry.db.close()

    async def authenticate(request):
        values=request.headers.getlist('authorization')
        if len(values)!=1 or not re.fullmatch(r'Bearer [a-f0-9]{64}',values[0]): raise Rejected(401)
        token=values[0][7:]
        try: market.consume_request(token)
        except RequestBudgetExceeded: raise Rejected(429) from None
        except ValueError: raise Rejected(401) from None
        return token

    async def capabilities(request): return response(catalog())

    async def create(request):
        token=await authenticate(request); data=await body(request,CreateTask)
        return response(market.create(token,**data))

    async def get(request):
        token=await authenticate(request)
        return response(market.get(token,request.path_params['task_id']))

    async def advance(request):
        token=await authenticate(request); data=await body(request,AdvanceTask)
        return response(market.advance(token,request.path_params['task_id'],**data))

    async def delete(request):
        token=await authenticate(request)
        return response(market.delete(token,request.path_params['task_id']))

    app=Starlette(routes=[Route('/v1/capabilities',capabilities),Route('/v1/tasks',create,methods=['POST']),
        Route('/v1/tasks/{task_id}',get,methods=['GET']),Route('/v1/tasks/{task_id}',delete,methods=['DELETE']),
        Route('/v1/tasks/{task_id}/events',advance,methods=['POST'])], lifespan=lifespan)

    async def boundary(request: Request, call_next):
        # No proxy forwarding, browser requests, query credentials or DNS-rebinding hosts.
        try:
            peer=request.client.host if request.client else ''
            if not ipaddress.ip_address(peer).is_loopback: raise Rejected(403)
            hosts=request.headers.getlist('host')
            if len(hosts)!=1 or not re.fullmatch(r'(127\.0\.0\.1|localhost|\[::1\])(?::[0-9]{1,5})?',hosts[0]):
                raise Rejected(403)
            if request.headers.getlist('origin') or request.url.query or request.headers.getlist('forwarded') or request.headers.getlist('x-forwarded-for'):
                raise Rejected(403)
            now=time.monotonic()
            if now-window[0]>=60: window[:]=[now,0]
            window[1]+=1
            if window[1]>360: raise Rejected(429)
            sizes=request.headers.getlist('content-length')
            if len(sizes)>1: raise Rejected(400)
            if sizes:
                if not sizes[0].isdigit(): raise Rejected(400)
                if int(sizes[0])>MAX_BODY: raise Rejected(413)
            return await call_next(request)
        except Rejected as error: return response({'error':'request_rejected'},error.status)
        except (ValueError, sqlite3.Error): return response({'error':'invalid_or_inaccessible_operation'},400)
    app.add_middleware(BaseHTTPMiddleware, dispatch=boundary)
    return app


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',required=True)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    if not 1024<=args.port<=65535: parser.error('port must be 1024..65535')
    import uvicorn
    uvicorn.run(create_app(args.directory),host='127.0.0.1',port=args.port,access_log=False,
                proxy_headers=False,server_header=False,timeout_keep_alive=5,limit_concurrency=16)

if __name__=='__main__': main()
