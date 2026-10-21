import json
import os
import tempfile
import unittest
from pathlib import Path
import httpx
from resultgate.commerce.account_readiness import inspect_account, read_restricted_key, summarize


class AccountReadinessTests(unittest.TestCase):
    def setUp(self):
        self.key = 'rk_live_' + 'x' * 24
        self.account = {'object': 'account', 'id': 'acct_fixture', 'charges_enabled': True,
                        'payouts_enabled': True, 'details_submitted': True,
                        'requirements': {'currently_due': [], 'past_due': []},
                        'email': 'private@example.com', 'individual': {'id_number': 'PRIVATE'}}

    def test_only_read_request_and_no_automatic_approval(self):
        def handle(request):
            self.assertEqual('GET', request.method)
            self.assertEqual('https://api.stripe.com/v1/accounts/acct_fixture', str(request.url))
            self.assertEqual(b'', request.content)
            return httpx.Response(200, json=self.account)
        report = inspect_account(self.key, 'acct_fixture', httpx.MockTransport(handle))
        self.assertFalse(report['checkout_enabled'])
        self.assertFalse(report['connect_eligibility_confirmed'])
        self.assertNotIn('private@example.com', json.dumps(report))
        self.assertNotIn('PRIVATE', json.dumps(report))

    def test_missing_requirements_are_unknown(self):
        self.assertIsNone(summarize(self.account)['requirement_counts']['pending_verification'])

    def test_account_binding(self):
        with self.assertRaises(ValueError): summarize(self.account, 'acct_other')

    def test_reject_general_or_test_keys_before_network(self):
        for key in ('sk_live_secret', 'sk_test_secret', 'rk_test_secret', ''):
            with self.assertRaises(ValueError): inspect_account(key)

    def test_reject_path_injection(self):
        with self.assertRaises(ValueError): inspect_account(self.key, 'acct_x/../../charges')

    def test_no_redirect_or_sensitive_error(self):
        for status in (302, 401, 403, 500):
            def handle(request):
                return httpx.Response(status, text=self.key, headers={'Location':'https://example.com'})
            with self.assertRaisesRegex(ValueError, '^stripe_account_read_failed$'):
                inspect_account(self.key, transport=httpx.MockTransport(handle))

    def test_key_file_permissions_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'key'
            path.write_text(self.key); path.chmod(0o600)
            self.assertEqual(self.key, read_restricted_key(path))
            path.chmod(0o644)
            with self.assertRaises(ValueError): read_restricted_key(path)
            path.chmod(0o600)
            link = Path(directory) / 'link'; link.symlink_to(path)
            with self.assertRaises(OSError): read_restricted_key(link)
            other = Path(directory) / 'other'; os.link(path, other)
            with self.assertRaises(ValueError): read_restricted_key(path)

    def test_truthy_values_do_not_become_verified_flags(self):
        self.account['charges_enabled'] = 'true'
        self.assertIsNone(summarize(self.account)['charges_enabled'])
