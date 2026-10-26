import subprocess
import sys
import unittest
from unittest.mock import patch
from resultgate.referral_selector import Selection, catalog, select

class ReferralReleaseTests(unittest.TestCase):
    def test_commission_metadata_cannot_change_selection(self):
        request = Selection(need='browser_interaction', sources_permitted=True, local_solution_sufficient=False)
        original = select(request)
        changed = catalog()
        for p in changed['providers']:
            p['commission_rate'] = 999999 if p['id'] != 'browseract' else 0
            p['referral_url'] = None
        with patch('resultgate.referral_selector.catalog', return_value=changed):
            result = select(request)
        self.assertEqual(result['decision'], original['decision'])
        self.assertEqual([p['id'] for p in result['candidates']], [p['id'] for p in original['candidates']])

    def test_referrals_cannot_enable_http_or_provider_execution(self):
        for flag in ('--http', '--brokerage', '--delegation', '--allow-public-provider-requests', '--allow-demo-task-requests'):
            run = subprocess.run([sys.executable, '-m', 'resultgate.server', '--referrals', flag], capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 2)
            self.assertIn('standalone local stdio', run.stderr)
