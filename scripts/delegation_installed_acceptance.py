"""Internal installed-wheel acceptance, no network or payment."""
import asyncio
import json
import sys
import tempfile
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

SPEC={'description':'Public test','required_capabilities':['citation_structuring'],
      'citation':'Graff, Expert. Opin. Ther. Targets (2002) 6(1): 103-113',
      'expected_surname':'Graff','expected_year':2002}
async def main():
    with tempfile.TemporaryDirectory() as directory:
        params=StdioServerParameters(command=sys.executable,args=['-I','-m','resultgate.server','--brokerage','--delegation','--delegation-store',directory,'--internal-delegation-tests'],cwd=directory)
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session:
                await session.initialize();assert len((await session.list_tools()).tools)==12
                task=await session.call_tool('prepare_delegation',{'task':SPEC,'request_id':'installed-test'})
                assert not task.isError;tid=task.structuredContent['id']
                refused=await session.call_tool('execute_delegation',{'task_id':tid,'task':SPEC,'consent_to_send_public_citation':True})
                assert refused.isError
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session:
                await session.initialize();task=await session.call_tool('delegation_status',{'task_id':tid})
                assert task.structuredContent['state']=='routed'
    print(json.dumps({'kind':'internal_installed_wheel','tools':12,'restart_restored':True,'network_disabled_enforced':True,'independent_uses':0}))
if __name__=='__main__':asyncio.run(main())
