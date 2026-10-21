"""Local API + MCP adapters for shadow billing; no outbound calls or real payments."""
from typing import Any
import argparse
import asyncio
import json
import os
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from resultgate.server import create_app, strict_object, reject_constant
from resultgate.extraction import MAX_BYTES
from resultgate.models import ExtractionInput, CitationInput
from .service import ShadowService, Rejected

def create_shadow_app(service):
    # Reuse loopback trusted-host protection, replace only audit route handlers.
    app = create_app()
    async def audit(request):
        try:
            if 'origin' in request.headers:
                raise Rejected(403, 'browser origins not allowed')
            authorization = request.headers.get('authorization', '')
            token = authorization[7:] if authorization.startswith('Bearer ') else ''
            service.authorize(token)
            if request.headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                raise Rejected(415, 'application/json required')
            body = bytearray()
            async with asyncio.timeout(5):
                async for chunk in request.stream():
                    if len(body) + len(chunk) > MAX_BYTES:
                        raise Rejected(413, 'body exceeds 1 MiB')
                    body.extend(chunk)
            payload = json.loads(body, object_pairs_hook=strict_object, parse_constant=reject_constant)
            result = service.call(token, request.path_params.get('tool', request.url.path.rsplit('/', 1)[1]),
                                  payload, request.headers.get('idempotency-key', ''))
            return JSONResponse(result, headers={'Cache-Control': 'no-store'})
        except Rejected as exc:
            return JSONResponse({'error': str(exc), 'mode': 'shadow_only'}, status_code=exc.code)
        except TimeoutError:
            return JSONResponse({'error': 'read timeout'}, status_code=408)
        except (ValueError, RecursionError, UnicodeError):
            return JSONResponse({'error': 'invalid input'}, status_code=422)
    from starlette.routing import Route
    async def health(request):
        return JSONResponse({'mode': 'shadow_only', 'payments_enabled': False})
    app.router.routes = [Route('/health', health), Route('/v1/extraction', audit, methods=['POST']),
                         Route('/v1/citations', audit, methods=['POST'])]
    return app

def create_shadow_mcp(service, token):
    mcp = FastMCP('ResultGate Shadow Trial', instructions='Internal local experiment. No real charges. Reuse request_id on retry; one unit per completed tool operation, including fail/unknown outcomes.')
    @mcp.tool()
    def check_extraction(payload: ExtractionInput, request_id: str) -> dict[str, Any]:
        """Extraction contract check with simulated metering. No factual truth guarantee."""
        return service.call(token, 'extraction', payload.model_dump(exclude_unset=True), request_id)
    @mcp.tool()
    def check_citations(payload: CitationInput, request_id: str) -> dict[str, Any]:
        """Literal citation check with simulated metering, not semantic verification."""
        return service.call(token, 'citations', payload.model_dump(exclude_unset=True), request_id)
    return mcp

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--http', action='store_true')
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    token = os.environ.get('RESULTGATE_TRIAL_TOKEN', '')
    if len(token) < 32:
        parser.error('set RESULTGATE_TRIAL_TOKEN to a random secret of at least 32 characters')
    service = ShadowService(token)
    if args.http:
        import uvicorn
        uvicorn.run(create_shadow_app(service), host='127.0.0.1', port=args.port,
                    access_log=False, limit_concurrency=8, timeout_keep_alive=5)
    else:
        create_shadow_mcp(service, token).run(transport='stdio')

if __name__ == '__main__':
    main()
