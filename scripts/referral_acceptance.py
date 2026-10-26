"""Installed-package MCP journey. Internal only; no provider calls or telemetry."""
import asyncio
import json
import os
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TOOLS = {'list_referral_providers', 'recommend_referral_service', 'prepare_referral_task',
         'assess_browseract_fit', 'validate_browseract_report', 'validate_browseract_csv'}
PROVIDERS = {'browseract', 'searchapi', 'pdfco', 'make', 'apify', 'firecrawl'}

async def check(command, args, directory):
    env = {k: v for k, v in os.environ.items() if not k.startswith('RESULTGATE_')}
    async with stdio_client(StdioServerParameters(command=command, args=args, cwd=directory, env=env)) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            assert {t.name for t in (await session.list_tools()).tools} == TOOLS
            async def call(name, arguments):
                result = await session.call_tool(name, arguments)
                assert not result.isError, result
                return json.loads(result.content[0].text)
            catalog = await call('list_referral_providers', {})
            assert {p['id'] for p in catalog['providers']} == PROVIDERS
            fit = await call('assess_browseract_fit', {'request': {
                'product_urls': ['https://example.com/product'], 'sources_permitted': True}})
            assert fit['decision'] == 'free_first'
            assert fit['offer']['referral_url'] == 'https://browseract.com?fpr=ahed-ddc97e'
            assert 'commission' in fit['offer']['disclosure'].lower()
            incomplete = await call('validate_browseract_report', {'report': {
                'expected_urls': ['https://example.com/product'], 'rows': [],
                'origin': 'internal', 'engine': 'fixture'}})
            assert not incomplete['complete']
            csv = ('product_name,price,currency,availability,product_url,extracted_at_utc,error\n'
                   'Example,12.50,USD,In stock,https://example.com/product,2026-10-26T00:00:00Z,\n')
            checked = await call('validate_browseract_csv', {'payload': {
                'csv_text': csv, 'expected_urls': ['https://example.com/product'], 'origin': 'internal'}})
            assert checked['validation']['all_successful']
            assert not checked['validation']['execution_independently_verified']
            for provider in catalog['providers']:
                selected = await call('recommend_referral_service', {'request': {
                    'need': provider['need'], 'sources_permitted': True,
                    'local_solution_sufficient': False}})
                assert selected['candidates'][0]['id'] == provider['id']
                assert selected['execution_started'] is False
                prepared = await call('prepare_referral_task', {'request': {
                    'provider_id': provider['id'], 'sources_permitted': True}})
                assert not prepared['execution_started'] and not prepared['purchase_authorized']
                if provider['id'] == 'browseract':
                    assert prepared['handoff']['provider_url'] == 'https://browseract.com?fpr=ahed-ddc97e'
                    assert prepared['handoff']['url'] == 'https://agents.allubiyerbamate.com/go/browseract'
                    assert prepared['handoff']['affiliate_link'] is True
                    assert 'commission' in prepared['disclosure'].lower()
            for field, decision in [('existing_solution_sufficient', 'use_existing_solution'),
                                    ('local_solution_sufficient', 'use_local_first')]:
                result = await call('recommend_referral_service', {'request': {
                    'need': 'browser_interaction', 'sources_permitted': True, field: True}})
                assert result['decision'] == decision
            denied = await call('prepare_referral_task', {'request': {'provider_id': 'browseract'}})
            assert denied['status'] == 'rejected'

async def main():
    assert version('resultgate-pilot') == '0.3.1'
    with tempfile.TemporaryDirectory() as directory:
        exe = Path(sys.executable).parent / ('resultgate-pilot.exe' if os.name == 'nt' else 'resultgate-pilot')
        alias = exe.with_name('resultgate-referrals.exe' if os.name == 'nt' else 'resultgate-referrals')
        await check(str(exe), ['--referrals'], directory)
        await check(str(alias), [], directory)
        assert list(Path(directory).iterdir()) == []
    print(json.dumps({'kind': 'internal_installed_package_acceptance', 'version': version('resultgate-pilot'),
                      'tools': sorted(TOOLS), 'providers': sorted(PROVIDERS),
                      'entry_points_tested': 2, 'browseract_official_link_and_disclosure': True,
                      'free_first_and_permission_guards': True, 'provider_calls': 0,
                      'independent_customers_proven': False}))

if __name__ == '__main__':
    asyncio.run(main())
