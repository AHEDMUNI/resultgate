import unittest, sys, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
class BrowserActProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_discovery_and_calls(self):
        async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','resultgate.browseract_demo'])) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                self.assertEqual({'assess_browseract_fit','validate_browseract_report'},{t.name for t in tools.tools})
                result=await session.call_tool('assess_browseract_fit',{'request':{'product_urls':['https://example.com/product'],'sources_permitted':True}})
                self.assertFalse(result.isError)
                self.assertEqual('free_first',json.loads(result.content[0].text)['decision'])
                bad=await session.call_tool('assess_browseract_fit',{'request':{'product_urls':['https://localhost/p']}})
                self.assertTrue(bad.isError)
                result=await session.call_tool('validate_browseract_report',{'report':{'expected_urls':['https://example.com/p'],'rows':[],'origin':'internal','engine':'fixture'}})
                self.assertFalse(json.loads(result.content[0].text)['complete'])
