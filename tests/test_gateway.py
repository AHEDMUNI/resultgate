import asyncio
from unittest.mock import patch
import socket
import threading
import time
import httpx
import uvicorn
import tempfile
import unittest
from starlette.testclient import TestClient
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from resultgate.network.gateway import create_app

PROOF='a'*64
class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.registry=Registry(self.tmp.name)
        self.operator=MarketOperator(Market(self.registry))
        self.token=self.operator.issue_credential('one'); self.other=self.operator.issue_credential('two')
        self.client=TestClient(create_app(self.tmp.name),base_url='http://127.0.0.1',client=('127.0.0.1',5000))
        self.client.__enter__()
    def tearDown(self):
        self.client.__exit__(None,None,None);self.registry.db.close();self.tmp.cleanup()
    def headers(self,token=None): return {'Authorization':'Bearer '+(token or self.token)}
    def create(self,**extra):
        data=dict(request_id='test',task_sha256=PROOF,success_criteria_sha256=PROOF);data.update(extra)
        return self.client.post('/v1/tasks',headers=self.headers(),json=data)
    def test_catalog_no_secrets_or_execution(self):
        r=self.client.get('/v1/capabilities');self.assertEqual(r.status_code,200)
        self.assertFalse(r.json()['external_execution_enabled_by_configuration'])
        self.assertEqual(r.headers['cache-control'],'no-store')
    def test_auth_isolation_dedup_and_restart(self):
        self.assertEqual(self.client.post('/v1/tasks',json={}).status_code,401)
        first=self.create();self.assertEqual(first.status_code,200)
        tid=first.json()['id'];self.assertTrue(self.create().json()['duplicate'])
        self.assertEqual(self.client.get('/v1/tasks/'+tid,headers=self.headers(self.other)).status_code,400)
        with TestClient(create_app(self.tmp.name),base_url='http://127.0.0.1',client=('127.0.0.1',5001)) as second:
            result=second.get('/v1/tasks/'+tid,headers=self.headers()).json()
            self.assertEqual(result['id'],tid);self.assertEqual(result['mode'],'simulation')
    def test_origins_hosts_peers_queries_refused(self):
        for headers in [{'Origin':'https://evil.example'},{'Host':'evil.example'},{'X-Forwarded-For':'127.0.0.1'}]:
            self.assertEqual(self.client.get('/v1/capabilities',headers=headers).status_code,403)
        self.assertEqual(self.client.get('/v1/capabilities?token=x').status_code,403)
        with TestClient(create_app(self.tmp.name),base_url='http://127.0.0.1',client=('192.0.2.1',5001)) as remote:
            self.assertEqual(remote.get('/v1/capabilities').status_code,403)
    def test_strict_body_limits_duplicates_extra_and_paid(self):
        h=self.headers();h['Content-Type']='application/json'
        self.assertEqual(self.client.post('/v1/tasks',headers=h,content=b'x'*16385).status_code,413)
        self.assertEqual(self.create(tenant_id='other').status_code,400)
        self.assertEqual(self.client.post('/v1/tasks',headers=h,content='{"request_id":"a","request_id":"b"}').status_code,400)
        tid=self.create().json()['id']
        r=self.client.post('/v1/tasks/'+tid+'/events',headers=h,json={'event_id':'e','state':'accepted','consent_to_send':True,'max_cost_micros':1})
        self.assertEqual(r.status_code,400)
        self.assertNotIn('input',r.text)
    def test_no_admin_surface_or_privilege_transition(self):
        self.assertEqual(self.client.post('/v1/admin',headers=self.headers(),json={}).status_code,404)
        tid=self.create().json()['id']
        r=self.client.post('/v1/tasks/'+tid+'/events',headers=self.headers(),json={'event_id':'e','state':'verified','evidence_sha256':PROOF})
        self.assertEqual(r.status_code,400)
    def test_revocation_and_delete(self):
        tid=self.create().json()['id']
        self.assertEqual(self.client.delete('/v1/tasks/'+tid,headers=self.headers()).status_code,200)
        self.assertEqual(self.create().status_code,400)
        self.operator.revoke(self.token)
        self.assertEqual(self.client.get('/v1/tasks/'+tid,headers=self.headers()).status_code,401)
    def test_requires_initialized_store(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(ValueError):create_app(empty)

    def test_streaming_limit_and_duplicate_auth(self):
        h=self.headers();h['Content-Type']='application/json'
        streamed=self.client.post('/v1/tasks',headers=h,content=iter([b'x'*8192,b'y'*8193]))
        self.assertEqual(streamed.status_code,413)
        duplicate=[('Authorization','Bearer '+self.token),('Authorization','Bearer '+self.other)]
        self.assertEqual(self.client.get('/v1/tasks/unknown',headers=duplicate).status_code,401)

    def test_local_rate_bound(self):
        for _ in range(360): self.assertEqual(self.client.get('/v1/capabilities').status_code,200)
        self.assertEqual(self.client.get('/v1/capabilities').status_code,429)

    def test_two_real_socket_clients_share_durable_store(self):
        sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen(16)
        base='http://127.0.0.1:'+str(sock.getsockname()[1])
        server=uvicorn.Server(uvicorn.Config(create_app(self.tmp.name),access_log=False,
            proxy_headers=False,log_level='error',limit_concurrency=16))
        thread=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True)
        thread.start()
        try:
            deadline=time.monotonic()+5
            while not server.started and thread.is_alive() and time.monotonic()<deadline: time.sleep(.01)
            self.assertTrue(server.started)
            with httpx.Client(base_url=base,trust_env=False,timeout=3) as first, httpx.Client(base_url=base,trust_env=False,timeout=3) as second:
                created=first.post('/v1/tasks',headers=self.headers(),json=dict(request_id='real-socket',task_sha256=PROOF,success_criteria_sha256=PROOF))
                self.assertEqual(created.status_code,200);task_id=created.json()['id']
                read=second.get('/v1/tasks/'+task_id,headers=self.headers())
                self.assertEqual(read.json()['id'],task_id)
                self.assertEqual(read.json()['mode'],'simulation')
                self.assertEqual(second.get('/v1/tasks/'+task_id,headers=self.headers(self.other)).status_code,400)
                self.assertEqual(first.get('/v1/capabilities',headers={'Origin':'https://evil.example'}).status_code,403)
        finally:
            server.should_exit=True;thread.join(timeout=5);sock.close()
            self.assertFalse(thread.is_alive())

    def test_slow_stream_deadline_and_disconnect_are_generic(self):
        # Direct ASGI receive allows a real stalled body without blocking TestClient's thread.
        async def run(disconnect=False):
            async def receive():
                if disconnect: return {'type':'http.disconnect'}
                await asyncio.sleep(1)
                return {'type':'http.request','body':b'{}','more_body':False}
            scope={'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':'POST',
                'scheme':'http','path':'/v1/tasks','raw_path':b'/v1/tasks','query_string':b'',
                'server':('127.0.0.1',8765),'client':('127.0.0.1',5001),
                'headers':[(b'host',b'127.0.0.1'),(b'content-type',b'application/json'),
                    (b'authorization',('Bearer '+self.token).encode())]}
            messages=[]
            async def send(message):messages.append(message)
            await self.client.app(scope,receive,send)
            return messages
        with patch('resultgate.network.gateway.BODY_TIMEOUT_SECONDS',.01):
            timed=asyncio.run(run())
        self.assertEqual(timed[0]['status'],408)
        self.assertIn(b'request_rejected',timed[1]['body'])
        disconnected=asyncio.run(run(True))
        self.assertEqual(disconnected[0]['status'],400)

    def test_provider_role_binding_and_explicit_requester_consent(self):
        fixture=dict(name='Fixture',description='Internal synthetic fixture',capabilities=['citation_structuring'],
            protocol='api',endpoint='https://provider.example.com/api',auth='none',requirements='none',pricing='free fixture',limits='one task')
        tokens=[];ids=[]
        for index in range(2):
            submission=self.registry.submit(dict(fixture,name='Fixture '+str(index)))
            pid=submission['provider']['id'];ids.append(pid)
            self.registry.review(pid,submission['provider']['challenge'],PROOF,True)
            tokens.append(self.operator.issue_credential('owner'+str(index),'provider',pid))
        tid=self.create().json()['id'];self.operator.match(tid,ids[0],'match')
        event={'event_id':'offer','state':'offered','evidence_sha256':PROOF}
        path='/v1/tasks/'+tid
        self.assertEqual(self.client.get(path,headers=self.headers(tokens[1])).status_code,400)
        self.assertEqual(self.client.post(path+'/events',headers=self.headers(tokens[1]),json=event).status_code,400)
        offered=self.client.post(path+'/events',headers=self.headers(tokens[0]),json=event)
        self.assertEqual(offered.status_code,200)
        self.assertNotIn('task_sha256',offered.json())
        accept={'event_id':'accept','state':'accepted'}
        self.assertEqual(self.client.post(path+'/events',headers=self.headers(),json=accept).status_code,400)
        accept['consent_to_send']=True
        accepted=self.client.post(path+'/events',headers=self.headers(),json=accept)
        self.assertEqual(accepted.json()['state'],'accepted')
        self.assertIn('task_sha256',self.client.get(path,headers=self.headers(tokens[0])).json())

    def test_authenticated_budget_survives_gateway_restart(self):
        frozen=time.time()
        with patch('resultgate.network.market.time.time',return_value=frozen):
            for _ in range(120):
                self.assertEqual(self.client.get('/v1/tasks/unknown',headers=self.headers()).status_code,400)
            with TestClient(create_app(self.tmp.name),base_url='http://127.0.0.1',client=('127.0.0.1',5001)) as second:
                response=second.get('/v1/tasks/unknown',headers=self.headers())
                self.assertEqual(response.status_code,429)
                self.assertEqual(response.json(),{'error':'request_rejected'})
                self.assertEqual(second.get('/v1/tasks/unknown',headers=self.headers(self.other)).status_code,400)
