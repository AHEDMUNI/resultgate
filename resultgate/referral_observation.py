"""Opt-in local aggregate counts; never network telemetry or customer evidence."""
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TOOLS = {'list_referral_providers', 'recommend_referral_service', 'prepare_referral_task'}


def observe(tool):
    path = os.environ.get('RESULTGATE_LOCAL_METRICS_DB')
    if not path:
        return 'disabled'
    if tool not in TOOLS:
        raise ValueError('Unsupported counter')
    # Caller controls local path. Never follow a symlink or share a database.
    target = Path(path)
    if not target.is_absolute() or target.is_symlink():
        return 'unavailable'
    origin = os.environ.get('RESULTGATE_LOCAL_METRICS_ORIGIN', 'unknown')
    if origin not in ('internal_declared', 'unknown'):
        origin = 'unknown'
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    except FileExistsError:
        if os.name == 'posix' and target.stat().st_mode & 0o077:
            return 'unavailable'
    except OSError:
        return 'unavailable'
    try:
        with sqlite3.connect(target, timeout=1) as db:
            db.execute('CREATE TABLE IF NOT EXISTS tool_counts (day TEXT,tool TEXT,origin TEXT,n INTEGER,PRIMARY KEY(day,tool,origin))')
            db.execute('INSERT INTO tool_counts VALUES (?,?,?,1) ON CONFLICT(day,tool,origin) DO UPDATE SET n=n+1',
                       (datetime.now(ZoneInfo('America/Chicago')).date().isoformat(), tool, origin))
        return 'local_only'
    except (OSError, sqlite3.Error):
        return 'unavailable'
