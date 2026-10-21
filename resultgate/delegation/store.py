"""Optional private SQLite event store; no task content. Local operator is trust boundary."""
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time

COHORTS={'internal','external_unverified','independent_verified'}
class Store:
    def __init__(self,directory=None):
        self.lock=threading.RLock()
        if directory is None:
            self.secret=secrets.token_bytes(32)
            self.db=sqlite3.connect(':memory:',check_same_thread=False,isolation_level=None)
        else:
            path=Path(directory)
            if path.is_symlink(): raise ValueError('symlink directory refused')
            path.mkdir(mode=0o700,parents=True,exist_ok=True)
            os.chmod(path,0o700)
            key=path/'identity.key'; database=path/'delegation.sqlite3'
            for f in (key,database):
                if f.is_symlink(): raise ValueError('symlink refused')
            if not key.exists():
                fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as stream: stream.write(secrets.token_bytes(32))
            os.chmod(key,0o600)
            self.secret=key.read_bytes()
            if len(self.secret)!=32: raise ValueError('invalid local identity')
            fd=os.open(database,os.O_WRONLY|os.O_CREAT,0o600);os.close(fd)
            os.chmod(database,0o600)
            self.db=sqlite3.connect(database,check_same_thread=False,isolation_level=None,timeout=5)
        self.db.execute('PRAGMA secure_delete=ON')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, request_hash TEXT UNIQUE, data TEXT NOT NULL, created REAL);
          CREATE TABLE IF NOT EXISTS events (task_id TEXT, state TEXT, at REAL);
          CREATE TABLE IF NOT EXISTS agreements (id TEXT PRIMARY KEY, data TEXT NOT NULL, created REAL);
          CREATE TABLE IF NOT EXISTS commissions (task_id TEXT PRIMARY KEY, amount_micros INTEGER, mode TEXT, status TEXT);
        ''')
        self.purge()
    def digest(self,value):
        return hmac.digest(self.secret,value.encode(),'sha256').hex()
    def transaction(self):
        return self.db
    def get(self,task_id):
        row=self.db.execute('SELECT data FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not row: raise ValueError('unknown or expired task')
        return json.loads(row[0])
    def save(self,task):
        self.db.execute('UPDATE tasks SET data=? WHERE id=?',(json.dumps(task,sort_keys=True),task['id']))
    def event(self,task,state):
        task['state']=state
        self.db.execute('INSERT INTO events VALUES (?,?,?)',(task['id'],state,time.time()))
        self.save(task)
    def purge(self):
        with self.lock:
            cutoff=time.time()-30*86400
            self.db.execute('BEGIN IMMEDIATE')
            try:
                self.db.execute('DELETE FROM commissions WHERE task_id IN (SELECT id FROM tasks WHERE created<?)',(cutoff,))
                self.db.execute('DELETE FROM events WHERE task_id IN (SELECT id FROM tasks WHERE created<?)',(cutoff,))
                self.db.execute('DELETE FROM tasks WHERE created<?',(cutoff,))
                self.db.execute('DELETE FROM agreements WHERE created<?',(cutoff,))
                self.db.execute('COMMIT')
            except Exception:
                self.db.execute('ROLLBACK');raise
    def delete(self,task_id):
        with self.lock:
            task=self.get(task_id)
            if task['state'] in {'dispatching','cancel_requested'}: raise ValueError('resolve in-flight task before deletion')
            self.db.execute('BEGIN IMMEDIATE')
            try:
                for table,column in [('events','task_id'),('commissions','task_id'),('tasks','id')]:
                    self.db.execute(f'DELETE FROM {table} WHERE {column}=?',(task_id,))
                self.db.execute('COMMIT')
            except Exception:
                self.db.execute('ROLLBACK');raise
    def summary(self):
        self.purge()
        tasks=[json.loads(row[0]) for row in self.db.execute('SELECT data FROM tasks')]
        return {'tasks_by_cohort':{c:sum(t['cohort']==c for t in tasks) for c in COHORTS},
                'verified_tasks':sum(t['state']=='verified' for t in tasks),
                'eligible_referrals':sum(t['state']=='commission_eligible' and t['cohort']=='independent_verified' for t in tasks),
                'commissions':[{'mode':r[0],'status':r[1],'count':r[2],'amount_micros':r[3]} for r in self.db.execute('SELECT mode,status,count(*),sum(amount_micros) FROM commissions GROUP BY mode,status')],
                'payments_enabled':False,'retention_days':30}
