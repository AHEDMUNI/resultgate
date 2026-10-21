"""Bounded public GitHub signal collection; every result requires human review.

No API tokens, raw issue bodies, contact harvesting, outreach, shell execution,
LLM calls, provider enrollment or payment calls. Run with Python stdlib only.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import sqlite3
import ssl
import time
from urllib.parse import urlencode

LIMIT = 20
MAX_ROWS = 5000
RETENTION = 90 * 86400
SOURCES = ('demand', 'provider')
URL = re.compile(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/issues/[0-9]+)?\Z')


def fetch(source, now):
    """Two fixed search endpoints; never follow URLs returned by sources."""
    since = datetime.fromtimestamp(now, timezone.utc) - timedelta(days=30)
    if source == 'demand':
        query = f'is:issue is:open "web scraping" "help" in:title,body updated:>={since:%Y-%m-%d}'
        endpoint = '/search/issues'
    elif source == 'provider':
        query = f'topic:mcp-server archived:false pushed:>={since:%Y-%m-%d}'
        endpoint = '/search/repositories'
    else:
        raise ValueError('unsupported source')
    path = endpoint + '?' + urlencode(dict(q=query, per_page=LIMIT, sort='updated', order='desc'))
    # At most one retry for a server error. No retry on rate limits or permission errors.
    for attempt in range(2):
        conn = http.client.HTTPSConnection('api.github.com', timeout=8, context=ssl.create_default_context())
        try:
            conn.request('GET', path, headers={'Accept': 'application/vnd.github+json',
                'User-Agent': 'ResultGate-demand-review/0.1 (https://github.com/AHEDMUNI/resultgate)',
                'X-GitHub-Api-Version': '2022-11-28', 'Accept-Encoding': 'identity'})
            response = conn.getresponse()
            if 500 <= response.status < 600 and attempt == 0:
                continue
            if response.status != 200:
                raise ValueError('github_http_' + str(response.status))
            if 'json' not in response.headers.get('Content-Type', '') or response.headers.get('Content-Encoding', 'identity') != 'identity':
                raise ValueError('invalid_content_type')
            raw = bytearray()
            deadline = time.monotonic() + 20
            while True:
                if time.monotonic() > deadline:
                    raise ValueError('response_timeout')
                chunk = response.read1(8192)
                if not chunk:
                    break
                raw.extend(chunk)
                if len(raw) > 1048576:
                    raise ValueError('response_limit')
            data = json.loads(raw)
            if not isinstance(data, dict) or not isinstance(data.get('items'), list) or data.get('incomplete_results') is not False:
                raise ValueError('incomplete_or_invalid_response')
            return data['items'][:LIMIT]
        finally:
            conn.close()
    raise ValueError('fetch_failed')


def normalize(source, item):
    url = item.get('html_url', '')
    if not isinstance(url, str) or not URL.fullmatch(url):
        raise ValueError('invalid_source_url')
    if source == 'demand':
        if '/issues/' not in url or item.get('state') != 'open' or 'pull_request' in item:
            raise ValueError('not_open_issue')
        text = item.get('title', '')
        # Store no author names, contact information or raw prose; keep a public citation.
        service = 'web_extraction' if isinstance(text, str) and re.search(r'scrap|crawl|extract', text, re.I) else 'technical_help_unclassified'
        who = 'public_issue_requester_unqualified'
    elif source == 'provider':
        if '/issues/' in url or item.get('archived') is not False or item.get('private') is not False:
            raise ValueError('not_public_active_repository')
        service, who = 'mcp_service_unverified', 'public_repository_not_confirmed_service_owner'
    else:
        raise ValueError('unsupported source')
    updated = item.get('updated_at')
    if not isinstance(updated, str):
        raise ValueError('missing_source_time')
    datetime.strptime(updated, '%Y-%m-%dT%H:%M:%SZ')
    return {'id': hashlib.sha256(url.lower().encode()).hexdigest(), 'kind': source,
            'url': url, 'source_updated': updated, 'service': service, 'requester_scope': who,
            'demand_verified': False, 'budget_verified': False, 'provider_match': None,
            'economic_value': 'potential matching and evidence validation; not qualified',
            'commission_agreement': None, 'automatic_response_allowed': False,
            'untrusted_source': True}


class Ledger:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / 'discovery.sqlite', timeout=2)
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS opportunities(id TEXT PRIMARY KEY, kind TEXT,
                data TEXT, first_seen REAL, last_seen REAL, status TEXT DEFAULT 'needs_review');
            CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, started REAL,
                finished REAL, status TEXT, report TEXT);
        ''')
        self.db.commit()

    def collect(self, fetcher=fetch, now=None):
        now = time.time() if now is None else now
        report = {'scope': 'public_signals_not_customers', 'observed_at': now,
                  'sources': {}, 'new': 0, 'seen': 0, 'invalid': 0, 'capacity_rejected': 0,
                  'paid_calls': 0, 'outreach_sent': 0, 'execution_enabled': False}
        with self.db:
            self.db.execute('DELETE FROM opportunities WHERE last_seen<?', (now - RETENTION,))
            self.db.execute('DELETE FROM runs WHERE started<?', (now - RETENTION,))
            cursor = self.db.execute('INSERT INTO runs(started,status) VALUES(?,?)', (now, 'running'))
        run_id = cursor.lastrowid
        for source in SOURCES:
            try:
                items = fetcher(source, now)
                if not isinstance(items, list) or len(items) > LIMIT:
                    raise ValueError('item_limit')
                with self.db:
                    for item in items:
                        try:
                            data = normalize(source, item)
                        except (ValueError, TypeError, AttributeError):
                            report['invalid'] += 1
                            continue
                        previous = self.db.execute('SELECT id FROM opportunities WHERE id=?', (data['id'],)).fetchone()
                        if previous:
                            self.db.execute('UPDATE opportunities SET data=?,last_seen=? WHERE id=?',
                                            (json.dumps(data), now, data['id']))
                        else:
                            if self.db.execute('SELECT count(*) FROM opportunities').fetchone()[0] >= MAX_ROWS:
                                report['capacity_rejected'] += 1
                                continue
                            self.db.execute('INSERT INTO opportunities VALUES(?,?,?,?,?,?)',
                                            (data['id'], source, json.dumps(data), now, now, 'needs_review'))
                            report['new'] += 1
                        report['seen'] += 1
                report['sources'][source] = 'ok'
            except (OSError, ValueError, http.client.HTTPException, RecursionError):
                # No source payload, URLs with credentials, or exception strings in logs.
                report['sources'][source] = 'failed'
        report['status'] = 'ok' if all(x == 'ok' for x in report['sources'].values()) and not report['invalid'] and not report['capacity_rejected'] else 'needs_attention'
        with self.db:
            self.db.execute('UPDATE runs SET finished=?,status=?,report=? WHERE id=?',
                            (time.time(), report['status'], json.dumps(report), run_id))
        return report

    def report(self):
        counts = dict(self.db.execute('SELECT kind,count(*) FROM opportunities GROUP BY kind'))
        latest = self.db.execute('SELECT report,status FROM runs ORDER BY id DESC LIMIT 1').fetchone()
        return {'counts': counts, 'latest_run': json.loads(latest[0]) if latest and latest[0] else None,
                'interrupted_run': bool(latest and latest[1] == 'running'),
                'independent_customers': 'not_measured', 'commission_due': 'not_measured',
                'cash_received': 'not_measured', 'payments_enabled': False}

    def snapshot(self):
        """Single rolling backup, validated before replacing it. Never copies live DB bytes."""
        temp = self.directory / 'snapshot.tmp'
        target = self.directory / 'snapshot.sqlite'
        try:
            with sqlite3.connect(temp) as destination:
                self.db.backup(destination)
                if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('snapshot_integrity_failed')
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()
        return target

    def export(self):
        return [dict(json.loads(raw), status=status, first_seen=first, last_seen=last)
                for raw, status, first, last in self.db.execute(
                    'SELECT data,status,first_seen,last_seen FROM opportunities ORDER BY first_seen DESC')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--collect', action='store_true', help='Two public read-only API queries; no credentials')
    parser.add_argument('--export', action='store_true', help='Public source URLs only; local operator review')
    args = parser.parse_args()
    os.umask(0o077)
    directory = Path(args.directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / 'worker.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'status': 'already_running'}))
            return 0
        if args.collect and (directory / 'STOP').exists():
            print(json.dumps({'status': 'stopped_by_operator'}))
            return 0
        ledger = Ledger(directory)
        try:
            report = ledger.collect() if args.collect else ledger.report()
            if args.collect:
                ledger.snapshot()
            print(json.dumps(ledger.export() if args.export else report, sort_keys=True))
            return int(args.collect and report['status'] != 'ok')
        finally:
            ledger.db.close()


if __name__ == '__main__':
    raise SystemExit(main())
