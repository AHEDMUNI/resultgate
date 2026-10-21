"""Internal live integration. Explicit --live sends two public example DOIs; never adoption."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    checks=[]
    params=StdioServerParameters(command=sys.executable,args=['-m','resultgate.server','--brokerage','--allow-public-provider-requests'],cwd=str(Path(__file__).resolve().parents[1]))
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            names={t.name for t in (await session.list_tools()).tools}
            assert {'discover_providers','match_task','route_task','execute_route','track_referral','check_extraction','check_citations'} <= names
            found=await session.call_tool('discover_providers',{'capability':'doi_metadata'})
            assert len(found.structuredContent['providers'])==2
            matched=await session.call_tool('match_task',{'required_capabilities':['doi_metadata']})
            assert {p['id'] for p in matched.structuredContent['matches']}=={'crossref','datacite'}
            for provider,doi in [('crossref','10.1038/nphys1170'),('datacite','10.6084/m9.figshare.21545982')]:
                prepared=await session.call_tool('route_task',{'provider_id':provider,'public_doi':doi,'request_id':'internal-'+provider})
                assert not prepared.isError
                rid=prepared.structuredContent['referral']['route_id']
                result=await session.call_tool('execute_route',{'route_id':rid,'public_doi':doi,'confirm_public_identifier':True})
                assert not result.isError
                output=result.structuredContent
                tracked=await session.call_tool('track_referral',{'route_id':rid})
                assert tracked.structuredContent['status']==output['referral']['status']
                duplicate=await session.call_tool('execute_route',{'route_id':rid,'public_doi':doi,'confirm_public_identifier':True})
                assert duplicate.structuredContent['duplicate']
                checks.append({'provider_id':provider,'public_fixture_doi':doi,'status':output['referral']['status'],
                    'evidence':output['referral']['execution_evidence'],'result':output['result'],
                    'tracked':True,'retry_did_not_dispatch':True})
    report={'kind':'internal_live_provider_integration','timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'tools_discovered':len(names),'checks':checks,'verified_independent_uses':0,'revenue_usd':0,'payments_enabled':False}
    print(json.dumps(report,indent=2))
    return all(c['status']=='succeeded' for c in checks)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if not args.live: parser.error('explicit --live required for these two public example DOI requests')
    sys.exit(0 if asyncio.run(run()) else 1)
