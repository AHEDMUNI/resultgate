import tempfile
import unittest
from starlette.testclient import TestClient
from resultgate.network.gateway import create_app
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from test_network import DATA, PROOF

class ProviderSearchTests(unittest.TestCase):
    def test_shared_reviewed_discovery_hides_pending_and_suspended(self):
        with tempfile.TemporaryDirectory() as directory:
            registry=Registry(directory)
            try:
                submitted=registry.submit(DATA); pid=submitted['provider']['id']
                token=MarketOperator(Market(registry)).issue_credential('client')
                with TestClient(create_app(directory),base_url='http://127.0.0.1',client=('127.0.0.1',12)) as client:
                    path='/v1/providers/search';headers={'Authorization':'Bearer '+token}
                    self.assertEqual(client.post(path,json={}).status_code,401)
                    self.assertEqual(client.post(path,json={},headers=headers).json()['providers'],[])
                    registry.review(pid,submitted['provider']['challenge'],PROOF,True)
                    result=client.post(path,json={'capability':DATA['capabilities'][0]},headers=headers)
                    self.assertEqual(result.status_code,200)
                    data=result.json();self.assertEqual(len(data['providers']),1)
                    self.assertIsNone(data['next_offset']);self.assertFalse(data['execution_enabled']);self.assertFalse(data['providers'][0]['executable'])
                    for secret in [token,submitted['management_token'],submitted['provider']['challenge']]:
                        self.assertNotIn(secret,result.text)
                    self.assertNotIn('agreement',data['providers'][0])
                    self.assertEqual(client.post(path,json={'capability':'nonexistent'},headers=headers).json()['providers'],[])
                    self.assertEqual(client.post(path,json={'capability':'../secret'},headers=headers).status_code,400)
                    self.assertEqual(client.post(path,json={'approved':True},headers=headers).status_code,400)
                    self.assertEqual(client.post(path,json={'limit':51},headers=headers).status_code,400)
                    self.assertEqual(client.post(path,json={'offset':True},headers=headers).status_code,400)
                    registry.suspend(pid,submitted['management_token'])
                    self.assertEqual(client.post(path,json={},headers=headers).json()['providers'],[])
            finally:registry.db.close()
