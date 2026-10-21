import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator

class HostPilotTests(unittest.TestCase):
    def test_real_process_restart_health_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            registry=Registry(directory)
            token=MarketOperator(Market(registry)).issue_credential('restart-fixture')
            registry.db.close()
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            base=f'http://127.0.0.1:{port}'
            ids=[]
            for attempt in range(2):
                proc=subprocess.Popen([sys.executable,'-m','resultgate.network.gateway','--directory',directory,'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                try:
                    deadline=time.monotonic()+10
                    while True:
                        try:
                            with opener.open(base+'/healthz',timeout=1) as response:
                                health=json.load(response)
                            break
                        except OSError:
                            if proc.poll() is not None or time.monotonic()>deadline:self.fail('gateway startup failed')
                            time.sleep(.05)
                    self.assertFalse(health['external_execution'])
                    req=urllib.request.Request(base+'/v1/tasks',data=json.dumps({'request_id':'restart','task_sha256':'a'*64,'success_criteria_sha256':'b'*64}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
                    with opener.open(req,timeout=2) as response:record=json.load(response)
                    ids.append(record['id']);self.assertEqual(record['duplicate'],bool(attempt))
                finally:
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait()
            self.assertEqual(ids[0],ids[1])
