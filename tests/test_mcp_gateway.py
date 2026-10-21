import json
import tempfile
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient
from resultgate.network.gateway import create_app
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator


class McpGatewayTests(unittest.TestCase):
    def test_auth_protocol_isolation_revocation_and_no_paid_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Registry(directory)
            operator = MarketOperator(Market(registry))
            token = operator.issue_credential('customer')
            other = operator.issue_credential('stranger')
            headers = {'Authorization': 'Bearer ' + token,
                       'Accept': 'application/json, text/event-stream',
                       'MCP-Protocol-Version': '2025-11-25'}
            with TestClient(create_app(directory), base_url='http://127.0.0.1',
                            client=('127.0.0.1', 5000)) as client:
                def rpc(method, params=None, custom=None):
                    return client.post('/mcp', headers=custom or headers,
                        json={'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})
                self.assertEqual(client.post('/mcp', json={}).status_code, 401)
                init = rpc('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {}, 'clientInfo': {}})
                self.assertEqual(init.json()['result']['protocolVersion'], '2025-11-25')
                names = {t['name'] for t in rpc('tools/list').json()['result']['tools']}
                self.assertEqual(names, {'search_providers', 'create_simulation_task', 'get_simulation_task'})
                args = {'request_id': 'one', 'task_sha256': 'a'*64, 'success_criteria_sha256': 'b'*64}
                created = rpc('tools/call', {'name': 'create_simulation_task', 'arguments': args})
                task = json.loads(created.json()['result']['content'][0]['text'])
                self.assertFalse(task['external_dispatch'])
                foreign = dict(headers, Authorization='Bearer ' + other)
                denied = rpc('tools/call', {'name': 'get_simulation_task', 'arguments': {'task_id': task['id']}}, foreign)
                self.assertTrue(denied.json()['result']['isError'])
                self.assertEqual(rpc('ping', custom=dict(headers, Origin='https://evil.example')).status_code, 403)
                self.assertEqual(rpc('ping', custom=dict(headers, **{'MCP-Protocol-Version': 'invalid'})).status_code, 400)
                self.assertEqual(client.get('/mcp', headers=headers).status_code, 405)
                self.assertEqual(rpc('tools/call', {'name': 'execute_payment'}).json()['error']['code'], -32602)
                operator.revoke(token)
                self.assertEqual(rpc('tools/list').status_code, 401)
            registry.db.close()

    def test_quota_survives_app_restart_and_shares_tenant_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Registry(directory)
            operator = MarketOperator(Market(registry))
            tokens = [operator.issue_credential('shared') for _ in range(2)]
            outsider = operator.issue_credential('separate')
            def ping(client, token):
                return client.post('/mcp', headers={'Authorization': 'Bearer ' + token,
                    'Accept': 'application/json, text/event-stream'},
                    json={'jsonrpc': '2.0', 'id': 1, 'method': 'ping'})
            with patch('resultgate.network.market.REQUESTS_PER_MINUTE', 2), patch('resultgate.network.market.time.time', return_value=2000000000):
                registry.db.execute('UPDATE market_credentials SET created=?', (2000000000,))
                with TestClient(create_app(directory), base_url='http://127.0.0.1', client=('127.0.0.1', 5000)) as client:
                    self.assertEqual(ping(client, tokens[0]).status_code, 200)
                    self.assertEqual(ping(client, tokens[1]).status_code, 200)
                with TestClient(create_app(directory), base_url='http://127.0.0.1', client=('127.0.0.1', 5000)) as client:
                    self.assertEqual(ping(client, tokens[0]).status_code, 429)
                    self.assertEqual(ping(client, outsider).status_code, 200)
            registry.db.close()

    def test_ambiguous_auth_oversize_queries_and_expired_credentials_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Registry(directory)
            operator = MarketOperator(Market(registry))
            token = operator.issue_credential('fixture')
            headers = {'Authorization': 'Bearer ' + token,
                       'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}
            with TestClient(create_app(directory), base_url='http://127.0.0.1', client=('127.0.0.1', 5000)) as client:
                self.assertEqual(client.post('/mcp?token=never', headers=headers, json={}).status_code, 403)
                self.assertEqual(client.post('/mcp', headers=headers, content=b'x'*16385).status_code, 413)
                duplicate = [('Authorization', 'Bearer ' + token)] * 2
                self.assertEqual(client.post('/mcp', headers=duplicate, json={}).status_code, 401)
                self.assertEqual(client.post('/mcp', headers=dict(headers, Host='evil.example'), json={}).status_code, 403)
                self.assertEqual(client.post('/mcp', headers=headers, content='{"jsonrpc":"2.0","id":1,"id":2,"method":"ping"}').status_code, 400)
                registry.db.execute('UPDATE market_credentials SET created=0')
                self.assertEqual(client.post('/mcp', headers=headers, json={}).status_code, 401)
            registry.db.close()
