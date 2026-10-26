"""Human CLI for preview recommendations; no task execution or retained need text."""
import argparse
import asyncio
import getpass
import json
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = 'https://agents.allubiyerbamate.com/mcp'


async def recommend(token, need):
    async with httpx.AsyncClient(headers={'Authorization':'Bearer '+token}, timeout=15,
                                 trust_env=False, follow_redirects=False) as http:
        async with streamable_http_client(URL, http_client=http) as (read, write, _):
            async with ClientSession(read, write) as client:
                await client.initialize()
                names = {tool.name for tool in (await client.list_tools()).tools}
                if 'recommend_services' not in names:
                    return {'available': False, 'reason': 'Marketplace preview is not enabled on this deployment.'}
                answer = await client.call_tool('recommend_services', {'need':need})
                if answer.isError:
                    raise ValueError('request rejected')
                return json.loads(answer.content[0].text)


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    token = getpass.getpass('Invited requester token (hidden): ')
    need = getpass.getpass('Describe a non-sensitive need (hidden, not saved): ')
    if not 1 <= len(need) <= 2000:
        raise SystemExit('Need must contain 1..2000 characters.')
    try:
        print(json.dumps(asyncio.run(recommend(token, need)), ensure_ascii=False, indent=2))
    except Exception:
        raise SystemExit('Request failed; credential and need details suppressed.') from None
