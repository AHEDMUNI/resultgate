"""Internal clean-install smoke test. Never counted as independent usage."""
import asyncio,json,sys,tempfile
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from resultgate.local_usage import LocalUsage

async def main():
    with tempfile.TemporaryDirectory() as directory:
        params=StdioServerParameters(command=sys.executable,args=['-m','resultgate.server','--usage-dir',directory],cwd=directory)
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                assert {t.name for t in tools.tools}=={'check_extraction','check_citations'}
                good={'records':[{'id':1,'value':'PRIVATE_SOURCE_MARKER'}],'required_fields':['/value'],'unique_fields':['/id'],'expected_count':1,'job_status':'completed','next_cursor':None,'truncated':False}
                context={'task_id':'PRIVATE_TASK_MARKER','purpose':'real_task'}
                for _ in range(2):
                    result=await session.call_tool('check_extraction',{'payload':good,'usage':context})
                    assert not result.isError and result.structuredContent['status']=='pass'
                bad=dict(good,expected_count=2)
                result=await session.call_tool('check_extraction',{'payload':bad,'usage':{'task_id':'test-task','purpose':'test'}})
                assert result.structuredContent['status']=='fail'
                result=await session.call_tool('check_extraction',{'payload':{'records':[]}})
                assert result.structuredContent['status']=='unknown'
                result=await session.call_tool('check_citations',{'payload':{'sources':[{'id':'s','text':'Quote'}],'citations':[{'source_id':'wrong','quote':'Quote'}]}})
                assert result.structuredContent['status']=='fail'
        data=LocalUsage(directory).export()
        assert sum(r['task_count'] for r in data['daily'])==1
        for p in Path(directory).iterdir():
            assert b'PRIVATE_SOURCE_MARKER' not in p.read_bytes()
            assert b'PRIVATE_TASK_MARKER' not in p.read_bytes()
        # The local fixture is discarded. No real-world event is added to any ledger.
        print(json.dumps({'kind':'internal_clean_install','mcp_initialize':True,'tools_discovered':2,'functional_checks_passed':True,'local_opt_in_dedup_privacy_checked':True,'external_qualified_uses':0}))

if __name__=='__main__':asyncio.run(main())
