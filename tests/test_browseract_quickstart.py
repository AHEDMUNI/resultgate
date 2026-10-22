"""A newcomer can run the saved example without the project as their cwd."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class QuickstartTests(unittest.TestCase):
    def test_saved_input_and_mcp_result(self):
        root = Path(__file__).resolve().parents[1]
        payload = json.loads((root/'examples/browseract/accepted/mcp-input.json').read_text())
        self.assertEqual(payload['payload']['csv_text'], (root/'examples/browseract/accepted/result.csv').read_text())
        # Installed companion is validated separately in a clean venv. CI source
        # test retains repository cwd so it does not depend on a global install.
        run = subprocess.run([sys.executable, str(root/'scripts/browseract_demo_check.py')],
                             cwd=root, capture_output=True, text=True, timeout=70)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['rows'], 20)
        self.assertEqual(result['origin'], 'internal')
        self.assertFalse(result['provider_run_started'])
        self.assertFalse(result['commission_approved'])
