"""Explicit opt-in, local-only measurement; never sends data over a network."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3

class LocalUsage:
    def __init__(self, directory):
        self.path = Path(directory).expanduser()
        self.path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path.is_symlink():
            raise ValueError('usage directory must not be a symlink')
        os.chmod(self.path, 0o700)
        identity = self.path / 'identity.json'
        if not identity.exists():
            # Exclusive creation avoids overwriting identity from another local process.
            try:
                with identity.open('x') as f:
                    os.chmod(identity, 0o600)
                    json.dump({'installation_id':secrets.token_hex(16), 'key':secrets.token_hex(32)},f)
            except FileExistsError:
                pass
        if identity.is_symlink():
            raise ValueError('usage identity must not be a symlink')
        self.identity = json.loads(identity.read_text())
        self.dbpath = self.path / 'counts.sqlite3'
        if self.dbpath.is_symlink():
            raise ValueError('usage database must not be a symlink')
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS tasks (digest TEXT PRIMARY KEY, day TEXT, tool TEXT, outcome TEXT)')
            self.purge(db)
        os.chmod(self.dbpath, 0o600)

    def connect(self):
        return sqlite3.connect(self.dbpath, timeout=5)

    def purge(self, db):
        # Keep today and the preceding 29 UTC dates; this is a retention window, not a cohort.
        cutoff = (datetime.now(timezone.utc).date() - timedelta(days=29)).isoformat()
        db.execute('DELETE FROM tasks WHERE day < ?', (cutoff,))

    def record(self, tool, outcome, context):
        if context is None or context['purpose'] != 'real_task':
            return
        if tool not in ('extraction','citations') or outcome not in ('pass','fail','unknown'):
            raise ValueError('invalid measurement category')
        # Purpose is caller-declared; it is not independent proof of real-world use.
        digest=hmac.new(bytes.fromhex(self.identity['key']),context['task_id'].encode(),hashlib.sha256).hexdigest()
        day=datetime.now(timezone.utc).date().isoformat()
        with self.connect() as db:
            self.purge(db)
            # One task counts once across tools and retries. First outcome retained.
            db.execute('INSERT OR IGNORE INTO tasks VALUES (?,?,?,?)',(digest,day,tool,outcome))

    def export(self):
        with self.connect() as db:
            self.purge(db)
            rows=db.execute('SELECT day,tool,outcome,COUNT(*) FROM tasks GROUP BY day,tool,outcome ORDER BY day,tool,outcome').fetchall()
        return {'format':'resultgate-local-summary-v1', 'installation_id':self.identity['installation_id'],
                'verification':'self_reported_not_independently_verified', 'retention_days':30,
                'daily':[dict(zip(('day','tool','outcome','task_count'),r)) for r in rows],
                'external_qualified_uses':None,
                'note':'No source text, URL, raw task ID, task hash, IP or secret included. Share only after review. Counts can be fabricated and are not payment evidence.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',help='Explicit local opt-in measurement directory')
    parser.add_argument('--export',action='store_true',required=True)
    args=parser.parse_args()
    print(json.dumps(LocalUsage(args.directory).export(),indent=2))

if __name__=='__main__':
    main()
