import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from deploy.referral_metrics import PREFIX, instrument, strip
from deploy.publish_business_site import replacement
from resultgate.referral_observation import observe
from scripts.referral_path_report import report

ROOT=Path(__file__).resolve().parents[1]

class MeasurementTests(unittest.TestCase):
    def test_config_upgrade_idempotence_and_auth_preservation(self):
        source=(ROOT/'deploy/nginx-agents.conf.staged').read_text()
        plain=replacement(source,'/var/www/resultgate-business/test')
        measured=instrument(plain)
        self.assertEqual(strip(measured),plain)
        self.assertEqual(instrument(replacement(strip(measured),'/var/www/resultgate-business/test')),measured)
        mcp=source[source.index('    location = /mcp'):source.index('    location / { return 404; }')]
        self.assertIn(mcp,measured)
        for secret in ('$remote_addr','$request_uri','$http_referer','$cookie_'):
            self.assertNotIn(secret,PREFIX)
        self.assertIn('if ($args != "") { return 400; }',measured)
        self.assertIn('return 302 https://browseract.com?fpr=ahed-ddc97e;',measured)
        with self.assertRaises(ValueError):strip(measured.replace('set $rg_event catalog_html','set $rg_event changed'))
    def test_report_separates_origins_and_provider_proof(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            rows=[dict(at='2026-10-24T00:30:00+00:00',event='browseract_handoff',origin=o,status=302) for o in ('internal_declared','bot_declared','unknown')]
            rows.append(dict(at='2026-10-23T12:00:00+00:00',event='catalog_html',origin='unknown',status=200))
            (folder/'resultgate-referral.log').write_text('\n'.join(map(json.dumps,rows))+'\nPRIVATE INVALID\n')
            r=report('2026-10-23',folder)
            self.assertEqual(r['observed_requests']['browseract_handoff'],dict(internal_declared=1,bot_declared=1,unknown=1))
            self.assertEqual(r['rejected_lines'],1)
            self.assertIsNone(r['independent_visitors']);self.assertIsNone(r['browseract_confirmed_clicks'])
            self.assertNotIn('PRIVATE',json.dumps(r))
            self.assertEqual(r['coverage'],'unavailable_or_partial')
    def test_missing_log_and_db_are_not_zero(self):
        with tempfile.TemporaryDirectory() as d:
            r=report('2026-10-23',Path(d),str(Path(d)/'missing.db'))
            self.assertIsNone(r['observed_requests']);self.assertIsNone(r['local_tool_counts'])
            self.assertFalse((Path(d)/'missing.db').exists())
    def test_opt_in_counts_only_no_inputs(self):
        with patch.dict(os.environ,{},clear=True):self.assertEqual(observe('list_referral_providers'),'disabled')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'counts.db'
            with patch.dict(os.environ,{'RESULTGATE_LOCAL_METRICS_DB':str(path),'RESULTGATE_LOCAL_METRICS_ORIGIN':'internal_declared'},clear=True):
                for _ in range(2):self.assertEqual(observe('recommend_referral_service'),'local_only')
            with sqlite3.connect(path) as db:
                row=db.execute('select tool,origin,n from tool_counts').fetchone()
                self.assertEqual(row,('recommend_referral_service','internal_declared',2))
            self.assertEqual(path.stat().st_mode & 0o077,0)
