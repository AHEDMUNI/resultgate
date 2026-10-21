"""Internal installed-wheel check, isolated from checkout. No external requests."""
import asyncio
import json
import sys
import tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    with tempfile.TemporaryDirectory() as directory:
        params=StdioServerParameters(command=sys.executable,args=['-I','-m','resultgate.server','--brokerage'],cwd=directory)
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                names={tool.name for tool in (await session.list_tools()).tools}
                assert names=={'check_extraction','check_citations','discover_providers','match_task','route_task','execute_route','track_referral'}
                result=await session.call_tool('discover_providers',{'capability':'doi_metadata'})
                assert len(result.structuredContent['providers'])==2
                result=await session.call_tool('match_task',{'required_capabilities':['doi_metadata']})
                assert result.structuredContent['matches'][0]['id']=='crossref'
                route=await session.call_tool('route_task',{'provider_id':'crossref','public_doi':'10.1038/nphys1170','request_id':'internal-wheel'})
                assert not route.isError
                rid=route.structuredContent['referral']['route_id']
                state=await session.call_tool('track_referral',{'route_id':rid})
                assert state.structuredContent['status']=='prepared'
                refused=await session.call_tool('execute_route',{'route_id':rid,'public_doi':'10.1038/nphys1170','confirm_public_identifier':True})
                assert refused.isError
    print(json.dumps({'kind':'internal_isolated_installed_wheel','tools_discovered':7,'discovery_matching_routing_tracking':True,'network_disabled_enforced':True,'verified_independent_uses':0,'revenue_usd':0}))

if __name__=='__main__':asyncio.run(main())
