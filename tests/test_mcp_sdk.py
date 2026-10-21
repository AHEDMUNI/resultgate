"""Real SDK over TCP to a separate gateway process; internal fixture, not adoption."""
import asyncio
import importlib.util
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import httpx
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator

spec = importlib.util.spec_from_file_location('remote_acceptance', Path(__file__).resolve().parents[1] / 'scripts/mcp_remote_acceptance.py')
client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client_module)


class SdkTests(unittest.TestCase):
    def test_sdk_over_real_tcp(self):
        self.run_sdk(False)

    def test_preview_sdk_over_real_tcp(self):
        self.run_sdk(True)

    def run_sdk(self, preview):
        with tempfile.TemporaryDirectory() as directory:
            registry = Registry(directory)
            token = MarketOperator(Market(registry)).issue_credential('sdk-internal-fixture')
            registry.db.close()
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            url = f'http://127.0.0.1:{port}'
            proc = subprocess.Popen([sys.executable, '-m', 'resultgate.network.gateway', '--directory', directory, '--port', str(port)] + (['--marketplace-preview'] if preview else []), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                with httpx.Client(trust_env=False, timeout=1) as client:
                    deadline = time.monotonic() + 10
                    while True:
                        try:
                            if client.get(url + '/healthz').status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        if proc.poll() is not None or time.monotonic() > deadline:
                            self.fail('gateway startup failed')
                        time.sleep(.05)
                result = asyncio.run(client_module.probe(url + '/mcp', token, marketplace_preview=preview))
                self.assertTrue(result['replay_prevented'])
                self.assertFalse(result['independent_adoption'])
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
