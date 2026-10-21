"""Bearer MCP smoke client. No provider execution; credentials via hidden prompt."""
import argparse
import asyncio
import getpass
import hashlib
import json
import secrets
from urllib.parse import urlsplit
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def require(condition):
    if not condition:
        raise ValueError("Acceptance condition failed")


async def probe(url, token):
    async with httpx.AsyncClient(headers={'Authorization': 'Bearer ' + token},
                                 timeout=10, follow_redirects=False, trust_env=False) as client:
        async with streamable_http_client(url, http_client=client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                names = {tool.name for tool in (await session.list_tools()).tools}
                require(names == {'search_providers', 'create_simulation_task', 'get_simulation_task'})
                search = await session.call_tool('search_providers', {})
                require(not search.isError)
                args = dict(request_id='acceptance-' + secrets.token_hex(8),
                            task_sha256=hashlib.sha256(b'internal acceptance fixture').hexdigest(),
                            success_criteria_sha256=hashlib.sha256(b'simulation only').hexdigest())
                first = await session.call_tool('create_simulation_task', args)
                require(not first.isError)
                task = json.loads(first.content[0].text)
                require(task['external_dispatch'] is False)
                replay = await session.call_tool('create_simulation_task', args)
                duplicate = json.loads(replay.content[0].text)
                require(duplicate['id'] == task['id'] and duplicate['duplicate'])
                fetched = await session.call_tool('get_simulation_task', {'task_id': task['id']})
                require(not fetched.isError)
                return {'sdk_handshake': True, 'tools': sorted(names), 'replay_prevented': True,
                        'execution_enabled': False, 'independent_adoption': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.path != '/mcp':
        parser.error('HTTPS URL ending in /mcp required, without credentials/query/fragment')
    token = getpass.getpass('Invited test tenant bearer token (hidden): ')
    try:
        result = asyncio.run(probe(args.url, token))
    except Exception:
        raise SystemExit('Acceptance failed; credentials and exception details suppressed.') from None
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
