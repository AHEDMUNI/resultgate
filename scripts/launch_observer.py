#!/usr/bin/env python3
"""Read-only observations. Never infer customers/revenue from HTTP or GitHub activity."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

BASE = 'https://agents.allubiyerbamate.com'
REPO = 'AHEDMUNI/resultgate'
GATES = ('approved_offer', 'public_reach_channel', 'independent_order_path')


def now():
    return dt.datetime.now(dt.timezone.utc)


def clock(readiness, at=None):
    at = at or now()
    missing = [key for key in GATES if not isinstance(readiness.get(key), dict)
               or readiness[key].get('verified') is not True
               or not isinstance(readiness[key].get('evidence_sha256'), str)
               or len(readiness[key]['evidence_sha256']) != 64
               or any(c not in '0123456789abcdef' for c in readiness[key]['evidence_sha256'])]
    if missing:
        return {'state': 'blocked', 'missing': missing, 'started_at': None}
    start = readiness.get('started_at')
    if not start:
        return {'state': 'ready_not_started', 'started_at': None}
    try:
        start = dt.datetime.fromisoformat(start)
        if start.tzinfo is None or start > at:
            raise ValueError('invalid start')
    except (TypeError, ValueError):
        return {'state': 'invalid_start', 'started_at': None}
    end = start + dt.timedelta(hours=72)
    return {'state': 'finished' if at >= end else 'running',
            'started_at': start.isoformat(), 'ends_at': end.isoformat()}


def fetch(url):
    # This helper receives only fixed project URLs from observe(). Never issue URL inputs.
    request = urllib.request.Request(url, headers={'User-Agent': 'ResultGate-Internal-Launch-Observer/1.0',
                                                   'Accept': 'application/json, text/html'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read(1048577)
            if len(data)>1048576: return {'status': response.status, 'error': 'oversize'}, None
            return {'status': response.status, 'sha256': hashlib.sha256(data).hexdigest()}, data
    except urllib.error.HTTPError as e:
        return {'status': e.code}, None
    except Exception as e:
        return {'status': None, 'error': type(e).__name__}, None


def issues_summary(issues):
    counts = {'provider_applications_unverified': 0, 'service_interest_unverified': 0,
              'excluded_internal_or_bot': 0}
    seen = set()
    for issue in issues:
        number = issue.get('number')
        if number in seen or 'pull_request' in issue: continue
        seen.add(number)
        title = issue.get('title', '')
        kind = ('provider_applications_unverified' if title.startswith('[Provider application]') else
                'service_interest_unverified' if title.startswith('[Service interest]') else None)
        if kind is None: continue
        user = issue.get('user') or {}
        labels = {x.get('name') for x in issue.get('labels', []) if isinstance(x, dict)}
        if user.get('login', '').lower()=='ahedmuni' or user.get('type')=='Bot' or 'internal-test' in labels:
            counts['excluded_internal_or_bot'] += 1
        else:
            counts[kind] += 1
    return counts


def observe(readiness):
    result = {'observed_at': now().isoformat(), 'observer': 'internal_not_adoption',
              'clock': clock(readiness), 'public_routes': {},
              'confirmed_visits': None, 'independent_mcp_users': None,
              'verified_independent_orders': None, 'checkout_transitions': None,
              'live_paid_transactions': None, 'live_commission_cents': None,
              'limitations': ['HTTP probes are internal checks, not visits.',
                 'GitHub issue titles are untrusted interest signals, not customers or orders.',
                 'No server logs, private mailbox, authenticated usage or live financial ledger read.',
                 'Missing measurement is null, never fabricated zero.']}
    for path in ('/', '/services', '/request', '/providers', '/agents', '/catalog.json', '/mcp'):
        status, body = fetch(BASE+path)
        result['public_routes'][path] = status
        if path=='/catalog.json' and body:
            try:
                catalog = json.loads(body)
                result['catalog'] = {'listed_services': len(catalog['services']),
                                     'live_checkout_enabled': catalog['live_checkout_enabled'] is True}
            except (KeyError, TypeError, ValueError): result['catalog'] = {'error': 'invalid_catalog'}
    issues, complete = [], False
    for page in range(1, 11):
        status, body = fetch(f'https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}')
        if status.get('status')!=200 or not body: break
        try:
            items=json.loads(body)
            if not isinstance(items, list): break
        except ValueError: break
        issues.extend(items)
        if len(items)<100:
            complete=True
            break
    result['public_intake'] = {'pagination_complete': complete,
                               'scope': 'all_time_observed_not_72h',
                               **issues_summary(issues)}
    if not complete:
        result['public_intake']['warning']='Incomplete observations; counts are not totals.'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readiness', default=str(Path(__file__).resolve().parents[1]/'docs/launch/readiness.json'))
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    readiness=json.loads(Path(args.readiness).read_text())
    result=observe(readiness)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__=='__main__': main()
