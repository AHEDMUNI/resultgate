"""Private local snapshot/restore. Offline operator tooling, not a cloud backup service."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import time

DATABASE = 'delegation.sqlite3'
KEY = 'identity.key'
MANIFEST = 'snapshot.json'
MARKER = 'RESTORE-RECONCILIATION-REQUIRED.json'


def _path(value):
    path = Path(os.path.abspath(value))
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError('symlink path refused')
    return path


def _regular(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('regular file required')


def _key(path):
    _regular(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        value = stream.read(33)
    if len(value) != 32:
        raise ValueError('invalid identity key')
    return value


def _hash(path):
    _regular(path)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _write(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def _db(path):
    _regular(path)
    conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
    conn.execute('PRAGMA query_only=ON')
    return conn


def _copy_database(source, destination):
    _write(destination, b'')
    src = _db(source)
    dst = sqlite3.connect(destination)
    try:
        # SQLite backup API captures a consistent DB including committed WAL data.
        deadline = time.monotonic() + 30
        def progress(status, remaining, total):
            if time.monotonic() > deadline:
                raise ValueError('backup time budget exceeded')
        src.backup(dst, pages=256, progress=progress, sleep=0.05)
        if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('database integrity failed')
    finally:
        dst.close()
        src.close()
    with destination.open('rb') as stream:
        os.fsync(stream.fileno())


def _finish(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def snapshot(source, destination):
    """Create a NEW private directory. Operator must prevent identity-key rotation."""
    source = _path(source); destination = _path(destination)
    if not source.is_dir() or destination.exists():
        raise ValueError('existing source and new destination required')
    secret = _key(source / KEY)
    _regular(source / DATABASE)
    destination.mkdir(mode=0o700)  # Parent must already exist; no merging/overwriting.
    try:
        _copy_database(source / DATABASE, destination / DATABASE)
        if _key(source / KEY) != secret:
            raise ValueError('identity changed during snapshot')
        _write(destination / KEY, secret)
        manifest = {'format': 'resultgate-local-snapshot-v1', 'created_at': time.time(),
                    'database_sha256': _hash(destination / DATABASE),
                    'identity_sha256': hashlib.sha256(secret).hexdigest(),
                    'restore_requires_reconciliation': True}
        _write(destination / MANIFEST, json.dumps(manifest, sort_keys=True).encode())
        _finish(destination)
    except Exception:
        shutil.rmtree(destination)
        raise
    return {'snapshot_created': True, 'private_files': True, 'cloud_backup': False}


def restore(source, destination, *, acknowledge_offline_reconciliation=False):
    """Restore to a NEW offline directory only. Store startup refuses the quarantine marker until operator reconciliation."""
    if acknowledge_offline_reconciliation is not True:
        raise ValueError('offline reconciliation acknowledgement required')
    source = _path(source); destination = _path(destination)
    if not source.is_dir() or destination.exists():
        raise ValueError('existing snapshot and new destination required')
    for name in (DATABASE, KEY, MANIFEST):
        _regular(source / name)
    if (source / MANIFEST).stat().st_size > 16384:
        raise ValueError('invalid manifest')
    manifest = json.loads((source / MANIFEST).read_text())
    secret = _key(source / KEY)
    if (not isinstance(manifest, dict) or manifest.get('format') != 'resultgate-local-snapshot-v1'
            or manifest.get('restore_requires_reconciliation') is not True
            or manifest.get('database_sha256') != _hash(source / DATABASE)
            or manifest.get('identity_sha256') != hashlib.sha256(secret).hexdigest()):
        raise ValueError('snapshot integrity failed')
    destination.mkdir(mode=0o700)
    try:
        _copy_database(source / DATABASE, destination / DATABASE)
        _write(destination / KEY, secret)
        _write(destination / MARKER, json.dumps({
            'reconciliation_required': True, 'external_dispatch_authorized': False,
            'reason': 'Snapshot may omit later dispatches. Reconcile provider records before enabling workers.',
            'enforcement': 'Store_startup_blocked_until_operator_reconciliation',
        }, sort_keys=True).encode())
        _finish(destination)
    except Exception:
        shutil.rmtree(destination)
        raise
    return {'restored': True, 'reconciliation_required': True,
            'runtime_dispatch_interlock': 'Registry_Store_startup_only', 'external_dispatch_authorized': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['snapshot', 'restore'])
    p.add_argument('--source', required=True)
    p.add_argument('--destination', required=True)
    p.add_argument('--acknowledge-offline-reconciliation', action='store_true')
    args = p.parse_args()
    try:
        value = (snapshot(args.source, args.destination) if args.action == 'snapshot'
                 else restore(args.source, args.destination,
                              acknowledge_offline_reconciliation=args.acknowledge_offline_reconciliation))
        print(json.dumps(value))
    except (ValueError, OSError, sqlite3.Error):
        p.exit(1, 'Recovery operation failed; no dispatch authorized.\n')


if __name__ == '__main__':
    main()
