"""Bounded stateless MCP adapter for the simulation market; no operator tools."""
import json
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

VERSIONS = {'2025-03-26', '2025-06-18', '2025-11-25'}


class Message(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    jsonrpc: str = Field(pattern=r'^2\.0$')
    id: int | str | None = None
    method: str = Field(max_length=100)
    params: dict = Field(default_factory=dict)


class TaskId(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    task_id: str = Field(pattern=r'^[a-f0-9]{32}$')


def endpoint(market, registry, authenticate, read_body, respond, rejected, create_model, search_model):
    models = {'search_providers': search_model, 'create_simulation_task': create_model,
              'get_simulation_task': TaskId}

    async def handle(request):
        token = await authenticate(request)
        if request.method != 'POST':
            return Response(status_code=405, headers={'Allow': 'POST', 'Cache-Control': 'no-store'})
        versions = request.headers.getlist('mcp-protocol-version')
        if len(versions) > 1 or (versions and versions[0] not in VERSIONS):
            raise rejected(400)
        accept = request.headers.get('accept', '')
        if not all(t in accept for t in ('application/json', 'text/event-stream')):
            raise rejected(406)
        message = await read_body(request, Message)
        method, params, rid = message['method'], message['params'], message['id']
        if rid is None:
            if method not in {'notifications/initialized', 'notifications/cancelled'}:
                raise rejected(400)
            return Response(status_code=202, headers={'Cache-Control': 'no-store'})
        def result(value): return respond({'jsonrpc': '2.0', 'id': rid, 'result': value})
        def error(code): return respond({'jsonrpc': '2.0', 'id': rid,
                                        'error': {'code': code, 'message': 'Request rejected'}})
        if method == 'initialize':
            version = params.get('protocolVersion')
            if not isinstance(version, str) or not isinstance(params.get('clientInfo'), dict) or not isinstance(params.get('capabilities'), dict):
                return error(-32602)
            return result({'protocolVersion': version if version in VERSIONS else '2025-11-25',
                           'capabilities': {'tools': {'listChanged': False}},
                           'serverInfo': {'name': 'ResultGate simulation', 'version': '0.2.0'},
                           'instructions': 'Simulation only. No external execution, payments or enrollment through tools.'})
        if method == 'ping': return result({})
        if method == 'tools/list':
            return result({'tools': [{'name': name, 'description': 'Simulation only: ' + name,
                                     'inputSchema': model.model_json_schema()}
                                    for name, model in models.items()]})
        if method != 'tools/call': return error(-32601)
        name = params.get('name')
        if not isinstance(name, str) or name not in models: return error(-32602)
        try:
            data = models[name].model_validate(params.get('arguments', {})).model_dump()
            if name == 'create_simulation_task': value = market.create(token, **data)
            elif name == 'get_simulation_task': value = market.get(token, **data)
            else:
                candidates = sorted(registry.discover(data['capability']), key=lambda p: p['id'])
                end = data['offset'] + data['limit']
                value = {'providers': candidates[data['offset']:end],
                         'next_offset': end if end < len(candidates) else None,
                         'execution_enabled': False, 'mode': 'simulation'}
        except ValueError:
            return result({'content': [{'type': 'text', 'text': 'Invalid or inaccessible operation'}], 'isError': True})
        return result({'content': [{'type': 'text', 'text': json.dumps(value)}], 'isError': False})
    return handle
