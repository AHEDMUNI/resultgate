import json
from pathlib import Path
import unittest
from unittest.mock import patch
from resultgate.network.catalog import catalog


class CatalogTests(unittest.TestCase):
    def test_supported_and_unknown_are_explicit(self):
        result = catalog(['citation_structuring', 'arbitrary_code_execution'])
        self.assertEqual([c['id'] for c in result['capabilities']], ['citation_structuring'])
        self.assertEqual(result['unsupported_capabilities'], ['arbitrary_code_execution'])
        self.assertFalse(result['all_requested_supported'])

    def test_default_is_offline_and_does_not_enable_external_execution(self):
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            result = catalog()
        self.assertFalse(result['a2a_supported'])
        self.assertIsNone(result['public_execution_endpoint'])
        self.assertFalse(result['external_execution_enabled_by_configuration'])
        self.assertEqual(result['safe_mcp_configuration']['args'], ['resultgate-pilot==0.3.0', '--brokerage', '--delegation'])

    def test_secrets_or_instructions_are_not_capabilities(self):
        for value in ['raw task text', 'https://127.0.0.1', ['ignore instructions'], ['a']*17, ['x'*65], [False]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                catalog(value)

    def test_caller_cannot_change_shared_catalog(self):
        first = catalog()
        first['capabilities'][0]['tools'].append('fake')
        self.assertNotIn('fake', catalog()['capabilities'][0]['tools'])

    def test_external_services_and_consent_are_honest(self):
        citation = catalog(['citation_structuring'])['capabilities'][0]
        self.assertEqual(citation['provider_kind'], 'specialist_ml_demo')
        self.assertIn('required_operator_flag', citation)
        self.assertIn('per_call_consent', citation)
        submission = catalog(['provider_submission'])['capabilities'][0]
        self.assertFalse(submission['automatic_approval'])
        self.assertFalse(submission['submitted_provider_execution'])

    def test_checked_in_manifest_matches_generator(self):
        path = Path(__file__).resolve().parents[1] / 'examples' / 'agent-discovery.json'
        self.assertEqual(json.loads(path.read_text()), catalog())
