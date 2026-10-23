"""Private on-host report; never upload runtime output to public Actions/GitHub."""
import argparse
from collections import Counter
from datetime import date, datetime
import gzip
import json
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

EVENTS = {'catalog_html', 'catalog_json', 'browseract_handoff'}
ORIGINS = {'internal_declared', 'bot_declared', 'unknown'}


def report(day, folder=Path('/var/log/nginx'), local_db=None):
    date.fromisoformat(day)
    counts = Counter()
    files = sorted(folder.glob('resultgate-referral.log*'))
    errors = skipped = 0
    for path in files:
        if path.is_symlink() or not path.is_file():
            errors += 1
            continue
        try:
            opener = gzip.open if path.suffix == '.gz' else open
            with opener(path, 'rt', encoding='utf-8') as source:
                for line in source:
                    try:
                        item = json.loads(line)
                        if set(item) != {'at', 'event', 'origin', 'status'}:
                            raise ValueError()
                        if item['event'] not in EVENTS or item['origin'] not in ORIGINS:
                            raise ValueError()
                        expected = {302} if item['event']=='browseract_handoff' else {200, 304}
                        if type(item['status']) is not int or item['status'] not in expected:
                            raise ValueError()
                        when = datetime.fromisoformat(item['at'])
                        if when.tzinfo is None:
                            raise ValueError()
                        if when.astimezone(ZoneInfo('America/Chicago')).date().isoformat() == day:
                            counts[(item['event'], item['origin'])] += 1
                    except (ValueError, TypeError, KeyError):
                        skipped += 1
        except (OSError, EOFError, UnicodeError):
            errors += 1
    local = None
    if local_db:
        try:
            uri = Path(local_db).resolve().as_uri()+'?mode=ro'
            with sqlite3.connect(uri, uri=True) as db:
                rows = db.execute('SELECT tool,origin,n FROM tool_counts WHERE day=?', (day,)).fetchall()
            allowed = {'list_referral_providers','recommend_referral_service','prepare_referral_task'}
            local = [dict(tool=t,origin=o,completed_calls=n) for t,o,n in rows
                     if t in allowed and o in {'internal_declared','unknown'} and type(n)==int and n>=0]
        except (OSError, sqlite3.Error):
            local = None
    return dict(day=day, timezone='America/Chicago', generated_at=datetime.now(ZoneInfo('UTC')).isoformat(),
        coverage='observed_log_records_only' if files and not errors and not skipped else 'unavailable_or_partial',
        files_found=len(files), unreadable_files=errors, rejected_lines=skipped,
        observed_requests={e:{o:counts[e,o] for o in sorted(ORIGINS)} for e in sorted(EVENTS)} if files else None,
        local_tool_counts=local, remote_local_tool_usage=None, independent_visitors=None,
        browseract_confirmed_clicks=None, registrations=None, attributed_purchases=None,
        approved_commission=None, cash_payout=None, experiment_started_at=None,
        limitations=['Unknown is not independent or human. User-agent buckets are spoofable; undeclared bots/internal probes remain unknown.',
        'Handoff counts successful GET redirects, including prefetches, not provider-confirmed clicks or registrations.',
        'No identifiers join stages. Counts are requests, not sessions or unique users. Local counters are opt-in and never sent to ResultGate.',
        'Provider stages require timestamped private dashboard observations. No affiliate reporting API is assumed.',
        'Zero observed records does not establish full-day coverage. Verify deployment time, log continuity and rotation.'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--day', required=True)
    p.add_argument('--local-db')
    a = p.parse_args()
    print(json.dumps(report(a.day, local_db=a.local_db), indent=2))
