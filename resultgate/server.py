"""Local MCP stdio and authenticated loopback HTTP. No outbound data transfer in default mode."""
from typing import Any
import argparse
import asyncio
import hmac
import json
import os
import sqlite3
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .extraction import audit_extraction, MAX_BYTES
from .citations import audit_citations
from .models import ExtractionInput, CitationInput, UsageContext
from .local_usage import LocalUsage

mcp = FastMCP('ResultGate', instructions='Check supplied evidence. Pass means contract checks only, never factual truth. No telemetry by default. Opt-in --brokerage --delegation discovers reviewed providers and delegates public citation structuring with explicit consent; --provider-registry adds locally reviewed provider submissions. No public A2A server or payments. Optional local metrics require CLI opt-in and a caller-declared real_task usage context.')
usage_store = None

def measure(tool, result, usage):
    if usage_store is not None and usage is not None:
        try:
            usage_store.record(tool,result['status'],usage.model_dump())
        except (OSError, ValueError, RuntimeError, sqlite3.Error):
            result['measurement_status']='not_recorded'
    return result

@mcp.tool()
def check_extraction(payload: ExtractionInput, usage: UsageContext | None = None) -> dict[str, Any]:
    """Audit records: failed jobs, missing pages/fields, count mismatch, duplicate keys. No fetches. Missing completion evidence returns unknown. Optional usage context only records locally when operator starts with --usage-dir; task_id must identify one real task, reused on retries."""
    return measure('extraction',audit_extraction(payload.model_dump(exclude_unset=True)),usage)

@mcp.tool()
def check_citations(payload: CitationInput, usage: UsageContext | None = None) -> dict[str, Any]:
    """Check exact quotes/source IDs in supplied text, NOT semantic truth. Offsets count Unicode code points. No fetches. Optional usage is local-only and requires explicit --usage-dir opt-in."""
    return measure('citations',audit_citations(payload.model_dump(exclude_unset=True)),usage)

async def health(request):
    return JSONResponse({'service':'ResultGate','version':'0.3.1','mode':'local_pilot'})

def strict_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key]=value
    return result

def reject_constant(value):
    raise ValueError('nonfinite JSON')

async def audit(request: Request):
    # Browser origins are never needed for this local machine API.
    if 'origin' in request.headers:
        return JSONResponse({'error':'browser origins not allowed'},status_code=403)
    token=request.app.state.api_token
    supplied=request.headers.get('authorization','').encode('utf-8')
    if not token or not hmac.compare_digest(supplied,('Bearer '+token).encode()):
        return JSONResponse({'error':'authentication required'},status_code=401)
    if request.headers.get('content-type','').split(';')[0].strip().lower()!='application/json':
        return JSONResponse({'error':'application/json required'},status_code=415)
    body=bytearray()
    try:
        async with asyncio.timeout(5):
            async for chunk in request.stream():
                if len(body)+len(chunk)>MAX_BYTES:
                    return JSONResponse({'error':'body exceeds 1 MiB'},status_code=413)
                body.extend(chunk)
    except TimeoutError:
        return JSONResponse({'error':'body read timed out'},status_code=408)
    try:
        payload=json.loads(body,object_pairs_hook=strict_object,parse_constant=reject_constant)
        fn=audit_extraction if request.url.path.endswith('extraction') else audit_citations
        return JSONResponse(fn(payload))
    except (ValueError,RecursionError,UnicodeError):
        return JSONResponse({'error':'invalid input; see contract and limits'},status_code=422)

def create_app(token=None):
    if token is not None and (not isinstance(token,str) or len(token)<32):
        raise ValueError('HTTP token must contain at least 32 characters')
    app=Starlette(routes=[Route('/health',health),Route('/v1/extraction',audit,methods=['POST']),Route('/v1/citations',audit,methods=['POST'])],middleware=[Middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','[::1]'])])
    app.state.api_token=token
    return app

app=create_app()

def main():
    global usage_store
    parser=argparse.ArgumentParser()
    parser.add_argument('--http',action='store_true')
    parser.add_argument('--referrals',action='store_true',help='Run six read-only referral/evidence tools for six providers over stdio')
    parser.add_argument('--brokerage',action='store_true',help='Opt in to experimental provider discovery and routing tools')
    parser.add_argument('--allow-public-provider-requests',action='store_true',help='Permit explicitly consented free public DOI requests through brokerage')
    parser.add_argument('--delegation',action='store_true',help='Opt in to specialist task delegation tools')
    parser.add_argument('--delegation-store',help='Opt in to private 30-day SQLite task events')
    parser.add_argument('--allow-demo-task-requests',action='store_true',help='Allow explicitly approved public citation processing on GROBID demo')
    parser.add_argument('--internal-delegation-tests',action='store_true',help='Classify this operator process as internal testing')
    parser.add_argument('--provider-registry',help='Opt in to local reviewed provider submission tools; private directory')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--usage-dir',help='Explicitly opt in to local-only MCP real-task counts; no automatic upload')
    args=parser.parse_args()
    if args.referrals:
        if (args.http or args.brokerage or args.delegation or args.usage_dir or
                args.provider_registry or args.delegation_store or
                args.allow_public_provider_requests or args.allow_demo_task_requests or
                args.internal_delegation_tests):
            parser.error('--referrals is a standalone local stdio mode')
        from .browseract_demo import main as referrals_main
        referrals_main()
        return
    if (args.delegation_store or args.allow_demo_task_requests or args.internal_delegation_tests) and not args.delegation:
        parser.error('delegation options require --delegation')
    if args.delegation and (not args.brokerage or args.http):
        parser.error('--delegation requires --brokerage and MCP stdio')
    if args.provider_registry:
        if args.http or not args.brokerage:
            parser.error('--provider-registry requires --brokerage and stdio')
        from .network.mcp import register as register_network
        register_network(mcp,args.provider_registry)
    if args.delegation:
        from .delegation.mcp import register as register_delegation
        register_delegation(mcp,args.delegation_store,args.allow_demo_task_requests,args.internal_delegation_tests)
    if args.allow_public_provider_requests and not args.brokerage:
        parser.error('--allow-public-provider-requests requires --brokerage')
    if args.brokerage and args.http:
        parser.error('brokerage currently supports MCP stdio only')
    if args.brokerage:
        from .brokerage.mcp import register
        register(mcp, args.allow_public_provider_requests)
    if args.http:
        if args.usage_dir:
            parser.error('local usage measurement currently supports MCP only')
        token=os.environ.get('RESULTGATE_API_TOKEN')
        if not token or len(token)<32:
            parser.error('set RESULTGATE_API_TOKEN to a random secret of at least 32 characters')
        import uvicorn
        uvicorn.run(create_app(token),host='127.0.0.1',port=args.port,access_log=False,limit_concurrency=8,timeout_keep_alive=5)
    else:
        if args.usage_dir:
            usage_store=LocalUsage(args.usage_dir)
        mcp.run(transport='stdio')

if __name__=='__main__':
    main()
