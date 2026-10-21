import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publish_site',ROOT/'deploy/publish_business_site.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.tags=[]
    def handle_starttag(self,tag,attrs):
        self.tags.append(tag)
        self.links += [v for k,v in attrs if k in ('href','src')]

class BusinessSiteTests(unittest.TestCase):
    def test_reload_transition_retries_complete_boundary(self):
        expected = {**dict.fromkeys(module.PAGES, '200'), '/mcp':'401',
                    '/healthz':'404', '/v1/capabilities':'404'}
        first = dict(expected); first['/'] = '404'
        with patch.object(module, 'probe', side_effect=list(first.values())+list(expected.values())) as probe, patch.object(module.time, 'sleep'):
            module.verify_routes()
            self.assertEqual(probe.call_count, 2*len(expected))

    def test_exposed_mcp_never_passes(self):
        with patch.object(module, 'probe', return_value='200'), patch.object(module.time, 'sleep'):
            with self.assertRaisesRegex(ValueError, '/mcp: HTTP 200'):
                module.verify_routes()

    def test_navigation_and_no_active_content(self):
        for name in module.PAGES.values():
            text=(ROOT/'web/business'/name).read_text()
            if name.endswith('.css'): continue
            page=Links(); page.feed(text)
            self.assertNotIn('script',page.tags); self.assertNotIn('form',page.tags)
            for link in page.links:
                if link.startswith('/'): self.assertIn(link,module.PAGES)
            self.assertIn('ALLUBI Yerba Mate LLC',text)
            self.assertIn('support@allubiyerbamate.com',text)
            self.assertIn('Live checkout is not currently available',text)

    def test_only_root_404_replaced(self):
        before=(ROOT/'deploy/nginx-agents.conf.staged').read_text()
        after=module.replacement(before,'/var/www/resultgate-business/test')
        a=before.index('    location = /mcp'); b=before.index('    location / { return 404; }')
        self.assertIn(before[a:b],after)
        self.assertEqual(before,after[:after.index('# RESULTGATE BUSINESS START')]+after[after.index('location / { return 404; }'):])
        for path in module.PAGES: self.assertIn('location = '+path+' {',after)

    def test_unknown_config_and_reinstall_fail_closed(self):
        before=(ROOT/'deploy/nginx-agents.conf.staged').read_text()
        for content in (before.replace('return 404','return 200'),before+'\nserver_name other.example;',module.replacement(before,'/var/www/test')):
            with self.assertRaises(ValueError): module.replacement(content,'/var/www/test')
