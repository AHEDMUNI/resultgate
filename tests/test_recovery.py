import json
import hmac
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from resultgate.network.recovery import snapshot, restore, MARKER

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.source=self.root/'source';self.backup=self.root/'backup';self.restored=self.root/'restored'
        self.r=Registry(self.source);self.m=Market(self.r)
        self.token=MarketOperator(self.m).issue_credential('tenant')
        self.task=self.m.create(self.token,'once','a'*64,'b'*64)
    def tearDown(self):
        self.r.db.close();self.tmp.cleanup()
    def test_snapshot_restore_preserves_identity_and_pending_dedup(self):
        self.assertTrue(snapshot(self.source,self.backup)['snapshot_created'])
        result=restore(self.backup,self.restored,acknowledge_offline_reconciliation=True)
        self.assertEqual(result['runtime_dispatch_interlock'],'Registry_Store_startup_only')
        with self.assertRaisesRegex(ValueError,'quarantined'):Registry(self.restored)
        db=sqlite3.connect(self.restored/'delegation.sqlite3')
        try:
            secret=(self.restored/'identity.key').read_bytes()
            token_hash=hmac.digest(secret,self.token.encode(),'sha256').hex()
            self.assertEqual(db.execute('SELECT role FROM market_credentials WHERE token_hash=?',(token_hash,)).fetchone()[0],'requester')
            same=json.loads(db.execute('SELECT data FROM market_tasks').fetchone()[0])
            self.assertEqual(same['id'],self.task['id']);self.assertEqual(same['state'],'discovered')
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('INSERT INTO market_tasks SELECT * FROM market_tasks')
        finally:db.close()
        self.assertTrue(json.loads((self.restored/MARKER).read_text())['reconciliation_required'])
        for name in ('identity.key','delegation.sqlite3',MARKER):
            self.assertEqual(os.stat(self.restored/name).st_mode & 0o777,0o600)
        self.assertEqual(os.stat(self.restored).st_mode & 0o777,0o700)
    def test_no_overwrite_and_ack_required(self):
        snapshot(self.source,self.backup)
        with self.assertRaises(ValueError):snapshot(self.source,self.backup)
        with self.assertRaises(ValueError):restore(self.backup,self.restored)
        self.assertFalse(self.restored.exists())
        restore(self.backup,self.restored,acknowledge_offline_reconciliation=True)
        with self.assertRaises(ValueError):restore(self.backup,self.restored,acknowledge_offline_reconciliation=True)
    def test_corruption_rejected_before_destination_creation(self):
        snapshot(self.source,self.backup)
        (self.backup/'identity.key').write_bytes(b'x'*32)
        with self.assertRaises(ValueError):restore(self.backup,self.restored,acknowledge_offline_reconciliation=True)
        self.assertFalse(self.restored.exists())
    def test_symlink_source_ancestor_and_member_refused(self):
        link=self.root/'link';link.symlink_to(self.source,target_is_directory=True)
        with self.assertRaises(ValueError):snapshot(link,self.backup)
        self.r.db.close()
        key=self.source/'identity.key';saved=self.root/'saved.key';key.rename(saved);key.symlink_to(saved)
        with self.assertRaises(ValueError):snapshot(self.source,self.backup)
        self.assertFalse(self.backup.exists())
    def test_wal_commit_is_in_snapshot(self):
        self.r.db.execute('PRAGMA journal_mode=WAL')
        self.m.create(self.token,'wal','c'*64,'d'*64)
        snapshot(self.source,self.backup)
        db=sqlite3.connect(self.backup/'delegation.sqlite3')
        try:self.assertEqual(db.execute('SELECT count(*) FROM market_tasks').fetchone()[0],2)
        finally:db.close()
