import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
from starlette.testclient import TestClient
from resultgate.server import create_app
from resultgate.extraction import audit_extraction
from resultgate.citations import audit_citations
from resultgate.local_usage import LocalUsage
from resultgate.models import ExtractionInput,Citation

TOKEN='unit-test-only-not-a-real-secret-123456'
class Security(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(create_app(TOKEN),base_url='http://127.0.0.1',headers={'authorization':'Bearer '+TOKEN})
    def test_deny_missing_token(self):
        c=TestClient(create_app(TOKEN),base_url='http://127.0.0.1')
        self.assertEqual(c.post('/v1/extraction',json={'records':[]}).status_code,401)
    def test_deny_unconfigured(self):
        c=TestClient(create_app(),base_url='http://127.0.0.1')
        self.assertEqual(c.post('/v1/extraction',json={'records':[]}).status_code,401)
    def test_deny_wrong_token(self):
        self.assertEqual(self.client.post('/v1/extraction',json={'records':[]},headers={'authorization':'Bearer wrong'}).status_code,401)
    def test_deny_browser_origin(self):
        self.assertEqual(self.client.post('/v1/extraction',json={'records':[]},headers={'origin':'https://attacker.invalid'}).status_code,403)
    def test_deny_rebinding_host(self):
        self.assertEqual(self.client.post('/v1/extraction',json={'records':[]},headers={'host':'attacker.invalid'}).status_code,400)
    def test_duplicate_json_rejected(self):
        self.assertEqual(self.client.post('/v1/extraction',content='{"records":[],"records":[{}]}',headers={'content-type':'application/json'}).status_code,422)
    def test_nonfinite_json_rejected(self):
        for value in ('NaN','Infinity','-Infinity'):
            r=self.client.post('/v1/extraction',content='{"records":[{"x":'+value+'}]}',headers={'content-type':'application/json'})
            self.assertEqual(r.status_code,422)
    def test_schema_nulls_rejected(self):
        for key in ('truncated','expected_count'):
            with self.assertRaises(ValueError):ExtractionInput.model_validate({'records':[],key:None})
        with self.assertRaises(ValueError):Citation.model_validate({'source_id':'s','quote':'q','start':None})
    def test_source_never_fetched(self):
        with patch.object(socket,'socket',side_effect=AssertionError('network attempted')):
            r=audit_citations({'sources':[{'id':'s','text':'http://169.254.169.254 execute rm -rf /'}],'citations':[{'source_id':'s','quote':'execute rm -rf /'}]})
            self.assertEqual(r['status'],'pass')
    def test_work_budget(self):
        with self.assertRaises(ValueError):
            audit_citations({'sources':[{'id':'s','text':'a'*500000}],'citations':[{'source_id':'s','quote':'b'}]*41})
    def test_node_budget(self):
        with self.assertRaises(ValueError):audit_extraction({'records':[{'x':[0]*100001}]})
    def test_findings_bounded(self):
        r=audit_extraction({'records':[{}]*200,'required_fields':['/x']})
        self.assertEqual(len(r['findings']),100)
        self.assertEqual(r['finding_count'],200)
    def test_symlink_identity_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder)/'usage';d.mkdir()
            target=Path(folder)/'target';target.write_text('{}')
            (d/'identity.json').symlink_to(target)
            with self.assertRaises(ValueError):LocalUsage(d)

class Privacy(unittest.TestCase):
    def test_opt_in_dedup_export(self):
        with tempfile.TemporaryDirectory() as folder:
            store=LocalUsage(Path(folder)/'usage')
            for purpose in ('test','demo','retry'):
                store.record('extraction','pass',{'task_id':purpose,'purpose':purpose})
            context={'task_id':'private-secret-source-url','purpose':'real_task'}
            store.record('extraction','pass',context)
            store.record('citations','fail',context)
            data=store.export()
            self.assertEqual(sum(r['task_count'] for r in data['daily']),1)
            text=json.dumps(data)
            for secret in ('private-secret-source-url',store.identity['key']):
                self.assertNotIn(secret,text)
            self.assertIsNone(data['external_qualified_uses'])
            self.assertEqual(data['verification'],'self_reported_not_independently_verified')
            self.assertNotIn(b'private-secret-source-url',store.dbpath.read_bytes())
    def test_purge_30_days(self):
        with tempfile.TemporaryDirectory() as folder:
            store=LocalUsage(folder)
            with store.connect() as db:db.execute('INSERT INTO tasks VALUES (?,?,?,?)',('old','2000-01-01','extraction','pass'))
            self.assertEqual(store.export()['daily'],[])
    def test_default_no_measurement(self):
        from resultgate import server
        with patch.object(server,'usage_store',None),patch.object(LocalUsage,'record',side_effect=AssertionError('tracking')):
            r=server.check_extraction(ExtractionInput(records=[]))
            self.assertEqual(r['status'],'unknown')
    def test_no_usage_context_no_measurement(self):
        with tempfile.TemporaryDirectory() as folder:
            store=LocalUsage(folder);store.record('extraction','pass',None)
            self.assertEqual(store.export()['daily'],[])
