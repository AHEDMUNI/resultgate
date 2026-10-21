"""One authorized public GROBID demo inference through MCP; internal integration only."""
import argparse
import asyncio
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import tempfile
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

SPEC={'description':'Structure the public example from GROBID documentation',
      'required_capabilities':['citation_structuring'],
      'citation':'Graff, Expert. Opin. Ther. Targets (2002) 6(1): 103-113',
      'expected_surname':'Graff','expected_year':2002}
async def main():
    with tempfile.TemporaryDirectory() as directory:
        params=StdioServerParameters(command=sys.executable,args=['-I','-m','resultgate.server','--brokerage','--delegation',
            '--allow-demo-task-requests','--internal-delegation-tests','--delegation-store',directory,'--provider-registry',directory],cwd=directory)
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session:
                await session.initialize()
                names={t.name for t in (await session.list_tools()).tools};assert len(names)==17
                assert 'submit_provider' in names and 'review' not in names
                registered=await session.call_tool('discover_registered_providers',{})
                assert registered.structuredContent['providers']==[]
                found=await session.call_tool('discover_agents',{'required_capabilities':['citation_structuring']})
                assert found.structuredContent['providers'][0]['id']=='grobid_demo'
                plan=await session.call_tool('prepare_delegation',{'task':SPEC,'request_id':'internal-grobid-demo'})
                assert not plan.isError
                tid=plan.structuredContent['id']
                response=await session.call_tool('execute_delegation',{'task_id':tid,'task':SPEC,'consent_to_send_public_citation':True})
                assert not response.isError
                data=response.structuredContent
                duplicate=await session.call_tool('execute_delegation',{'task_id':tid,'task':SPEC,'consent_to_send_public_citation':True})
                assert duplicate.structuredContent['duplicate']
        # New MCP process, same explicit opt-in store. No extra external execution.
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session:
                await session.initialize()
                restored=await session.call_tool('delegation_status',{'task_id':tid})
                assert restored.structuredContent['state']==data['task']['state']
        report={'kind':'internal_isolated_installed_full_acceptance','timestamp_utc':datetime.now(timezone.utc).isoformat(),
            'provider':'GROBID project demo','provider_kind':'specialist_ml_service_not_autonomous_agent',
            'state':data['task']['state'],'error':data['task']['error'],'result':data['result'],
            'result_hash':data['task']['result_hash'],'criteria':'surname Graff and year 2002, declared before dispatch',
            'tools_discovered':17,'installed_isolated':True,'restart_restored':True,'duplicate_not_redispatched':True,'independent_uses':0,
            'commission_eligible':False,'revenue_usd':0,'money_spent_usd':0}
        print(json.dumps(report,indent=2))
        return data['task']['state']=='verified'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--live',action='store_true');args=parser.parse_args()
    if not args.live: parser.error('--live required for one public demo citation disclosure')
    sys.exit(0 if asyncio.run(main()) else 1)
