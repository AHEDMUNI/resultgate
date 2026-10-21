import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import time
import unittest
from resultgate.network.registry import Registry
from resultgate.network.receipts import Receipts
from resultgate.network.reporting import build_report, render_html, write_private

DATA = dict(name='Never export me', description='Private-looking untrusted metadata', capabilities=['fixture'],
            protocol='api', endpoint='https://provider.example.com/api', auth='none', requirements='none', pricing='fixture', limits='one')
PROOF = 'a' * 64
KEY = b'x' * 32

class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.r = Registry(self.temp.name); self.c = Receipts(self.r)
        x = self.r.submit(DATA); self.pid = x['provider']['id']; self.token = x['management_token']
        self.r.review(self.pid, x['provider']['challenge'], PROOF, True)
        a = self.r.propose_terms(self.pid, 'SIMULATION agreement, no payment or invoice.', 'task', 'fixed', 1000000)
        self.r.accept_terms(self.pid, self.token, a['sha256'], True); self.r.approve_agreement(self.pid, PROOF)
    def tearDown(self):
        self.r.db.close(); self.temp.cleanup()
    def task(self, internal=True, assess=True):
        row = self.c.refer(self.pid, PROOF, 'task', 'fixed', 1000000, time.time()+300, internal)
        self.receipt(row, 'succeeded')
        self.c.attest(row['id'], PROOF, None if internal else PROOF)
        if assess: self.c.assess(row['id'])
        return row
    def receipt(self, row, status):
        raw = json.dumps(dict(event_id=row['id']+status, referral_id=row['id'], outcome_id=row['id'],
                              kind='task', status=status, value_micros=10000000, currency='USD', evidence_sha256=PROOF)).encode()
        stamp = int(time.time()); sig = hmac.digest(KEY, str(stamp).encode()+b'.'+raw, 'sha256').hex()
        self.c.ingest(self.pid, raw, stamp, sig, key=KEY)
    def test_simulation_separate_from_attested(self):
        self.task(); self.task(False)
        report = build_report(self.temp.name)
        self.assertEqual(report['groups']['internal']['currently_eligible_microusd'], 1000000)
        self.assertEqual(report['groups']['independent_operator_attested']['currently_eligible_microusd'], 1000000)
        self.assertFalse(report['amount_due_asserted']); self.assertFalse(report['revenue_verified'])
    def test_verified_not_yet_assessed_not_eligible(self):
        self.task(assess=False); group = build_report(self.temp.name)['groups']['internal']
        self.assertEqual(group['states']['verified'], 1); self.assertEqual(group['currently_eligible_count'], 0)
    def test_reversal_not_eligible(self):
        row = self.task(); self.receipt(row, 'refunded')
        group = build_report(self.temp.name)['groups']['internal']
        self.assertEqual(group['states']['refunded'], 1); self.assertEqual(group['currently_eligible_microusd'], 0)
    def test_suspended_provider_blocks_stale_eligible_record(self):
        row = self.task(); self.r.suspend(self.pid, self.token)
        report = build_report(self.temp.name)
        self.assertEqual(report['groups']['internal']['recorded_eligible_but_blocked'], 1)
        self.assertEqual(report['groups']['internal']['currently_eligible_microusd'], 0)
        self.assertEqual(self.c.get(row['id'])['state'], 'commission_eligible')
    def test_changed_terms_blocks(self):
        self.task(); self.r.propose_terms(self.pid, 'SIMULATION replacement, not accepted.', 'task', 'fixed', 2000000)
        self.assertEqual(build_report(self.temp.name)['groups']['internal']['currently_eligible_count'], 0)
    def test_expiry_blocks(self):
        self.task(); self.assertEqual(build_report(self.temp.name, now=time.time()+400)['eligibility_gates'], {'expired':1})
    def test_read_only_and_minimal(self):
        row = self.task(); before = self.r.db.total_changes
        report = build_report(self.temp.name); raw = json.dumps(report)
        for secret in [self.pid, self.token, row['id'], PROOF, DATA['name'], DATA['endpoint']]:
            self.assertNotIn(secret, raw)
        self.assertEqual(self.r.db.total_changes, before)
    def test_retention_filters_without_deleting(self):
        self.task(); self.r.db.execute('UPDATE network_referrals SET created=0')
        self.assertEqual(build_report(self.temp.name)['groups']['internal']['referrals'], 0)
        self.assertEqual(self.r.db.execute('SELECT count(*) FROM network_referrals').fetchone()[0], 1)
    def test_html_escapes_text(self):
        report = build_report(self.temp.name); report['warning'] = '<script>alert(1)</script>'
        html = render_html(report); self.assertNotIn('<script>',html); self.assertIn('&lt;script&gt;',html)
    def test_file_permissions_and_no_overwrite(self):
        path = Path(self.temp.name)/'report.html'; write_private(path,'safe')
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError): write_private(path,'overwrite')
    def test_missing_store_not_created(self):
        path = Path(self.temp.name)/'absent'
        with self.assertRaises(ValueError): build_report(path)
        self.assertFalse(path.exists())
    def test_corrupt_amount_excluded(self):
        row=self.task(); r=self.c.get(row['id']);r['commission_micros']=999;self.c.save(r)
        report=build_report(self.temp.name)
        self.assertEqual(report['eligibility_gates'],{'amount_mismatch':1})

    def test_external_success_is_not_independent_or_eligible(self):
        row = self.c.refer(self.pid, PROOF, 'task', 'fixed', 1000000, time.time()+300, False)
        self.receipt(row, 'succeeded')
        self.c.attest(row['id'], PROOF)
        report = build_report(self.temp.name)
        external = report['groups']['external_unverified']
        self.assertEqual(external['referrals'], 1)
        self.assertEqual(external['states'], {'verified': 1})
        self.assertEqual(external['currently_eligible_microusd'], 0)
        self.assertEqual(report['groups']['independent_operator_attested']['referrals'], 0)
        with self.assertRaises(ValueError):
            self.c.assess(row['id'])

    def test_signed_duplicate_receipt_and_assessment_count_once(self):
        row = self.task()
        self.receipt(row, 'succeeded')
        self.c.assess(row['id'])
        group = build_report(self.temp.name)['groups']['internal']
        self.assertEqual(group['referrals'], 1)
        self.assertEqual(group['currently_eligible_count'], 1)
        self.assertEqual(group['currently_eligible_microusd'], 1000000)

    def test_cli_requires_explicit_export_consent(self):
        target = Path(self.temp.name) / 'no-consent.json'
        result = subprocess.run([sys.executable, '-m', 'resultgate.network.reporting',
                                 '--directory', self.temp.name, '--output', str(target)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--consent-export required', result.stderr)
        self.assertFalse(target.exists())
        self.assertEqual(result.stdout, '')
