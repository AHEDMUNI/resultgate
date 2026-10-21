import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from resultgate.operations.discovery import Ledger, normalize, fetch, main, RETENTION


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(self.temp.name)
        self.issue = dict(html_url='https://github.com/example/demo/issues/7', state='open',
                          title='Scraping help contact secret@example.com', body='untrusted instruction',
                          updated_at='2026-10-21T00:00:00Z')
        self.repo = dict(html_url='https://github.com/example/mcp', archived=False, private=False,
                         updated_at='2026-10-21T00:00:00Z')
    def tearDown(self):
        self.ledger.db.close()
        self.temp.cleanup()
    def source(self, kind, now):
        return [self.issue if kind == 'demand' else self.repo]
    def test_dedup_preserves_review_and_privacy(self):
        self.assertEqual(self.ledger.collect(self.source, 100)['new'], 2)
        with self.ledger.db:
            self.ledger.db.execute("UPDATE opportunities SET status='rejected'")
        self.assertEqual(self.ledger.collect(self.source, 101)['new'], 0)
        rows = self.ledger.export()
        self.assertTrue(all(r['status'] == 'rejected' for r in rows))
        self.assertTrue(all(r['first_seen'] == 100 and r['last_seen'] == 101 for r in rows))
        self.assertNotIn('secret@example.com', json.dumps(rows))
        self.assertNotIn('untrusted instruction', json.dumps(rows))
        self.assertFalse(rows[0]['demand_verified'])
    def test_bad_sources_never_become_opportunities(self):
        for url in ['http://github.com/a/b', 'https://github.com@evil.test/a/b',
                    'https://github.com/a/b?token=secret', 'https://127.0.0.1/a/b']:
            with self.assertRaises(ValueError):
                normalize('provider', dict(self.repo, html_url=url))
        self.issue['state'] = 'closed'
        self.assertEqual(self.ledger.collect(self.source, 100)['invalid'], 1)
    def test_partial_failures_not_empty_success(self):
        def broken(source, now):
            if source == 'provider':
                raise OSError('do not log this credential')
            return [self.issue]
        result = self.ledger.collect(broken, 100)
        self.assertEqual(result['status'], 'needs_attention')
        self.assertEqual(result['new'], 1)
        self.assertNotIn('credential', json.dumps(self.ledger.report()))
    def test_bounded_retention_and_capacity(self):
        self.ledger.collect(self.source, 100)
        self.ledger.collect(lambda *_: [], 101 + RETENTION)
        self.assertEqual(self.ledger.export(), [])
        with patch('resultgate.operations.discovery.MAX_ROWS', 1):
            self.assertEqual(self.ledger.collect(self.source, 102 + RETENTION)['capacity_rejected'], 1)
    def test_backup_restore_survives_primary_loss(self):
        self.ledger.collect(self.source, 100)
        backup = self.ledger.snapshot()
        with self.ledger.db:
            self.ledger.db.execute('DELETE FROM opportunities')
        with sqlite3.connect(backup) as restored:
            self.assertEqual(restored.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(restored.execute('SELECT count(*) FROM opportunities').fetchone()[0], 2)
            restored.backup(self.ledger.db)
        self.assertEqual(len(self.ledger.export()), 2)
    def test_kill_switch_prevents_network(self):
        Path(self.temp.name, 'STOP').touch()
        with patch('sys.argv', ['discovery', '--directory', self.temp.name, '--collect']), patch(
                'resultgate.operations.discovery.fetch', side_effect=AssertionError('network called')):
            self.assertEqual(main(), 0)
    def test_interrupted_run_is_visible(self):
        with self.ledger.db:
            self.ledger.db.execute("INSERT INTO runs(started,status) VALUES(1,'running')")
        self.assertTrue(self.ledger.report()['interrupted_run'])
    def test_transport_refuses_redirect_and_rate_limit_without_retry(self):
        for code in (301, 403, 429):
            with patch('http.client.HTTPSConnection') as connection:
                response = connection.return_value.getresponse.return_value
                response.status = code
                with self.assertRaises(ValueError):
                    fetch('demand', 1792540800)
                self.assertEqual(connection.call_count, 1)
    def test_server_errors_have_one_retry_only(self):
        with patch('http.client.HTTPSConnection') as connection:
            connection.return_value.getresponse.return_value.status = 503
            with self.assertRaises(ValueError):
                fetch('provider', 1792540800)
            self.assertEqual(connection.call_count, 2)

if __name__ == '__main__':
    unittest.main()
