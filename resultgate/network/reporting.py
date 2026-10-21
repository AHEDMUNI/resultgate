"""Read-only local receipt-ledger dashboard. No server, invoices, payments or claims."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import sqlite3
import time

STATES = {'routed', 'completed', 'verified', 'commission_eligible', 'failed', 'cancelled', 'refunded', 'disputed'}
COHORTS = ('internal', 'external_unverified', 'independent_operator_attested')


def _gate(row, provider, now):
    """Recheck current eligibility without altering recorded history or creating entitlement."""
    if row.get('state') != 'commission_eligible':
        return 'not_recorded_eligible'
    if not provider or provider.get('state') != 'approved':
        return 'provider_unavailable_or_revoked'
    agreement = provider.get('agreement') or {}
    if not agreement.get('provider_accepted') or not agreement.get('operator_approved'):
        return 'agreement_not_approved'
    if agreement.get('sha256') != row.get('agreement_sha256'):
        return 'agreement_changed'
    if not isinstance(row.get('expires'), (int, float)) or not now <= row['expires']:
        return 'expired'
    if not row.get('acceptance_evidence') or not row.get('evidence_sha256') or not row.get('outcome_hash'):
        return 'missing_success_or_acceptance_evidence'
    if not row.get('internal') and not row.get('independent_evidence'):
        return 'independence_not_attested'
    expected_mode = 'simulation' if row.get('internal') else 'operator_attested'
    if row.get('mode') != expected_mode:
        return 'mode_mismatch'
    if (row.get('kind'), row.get('rule'), row.get('amount')) != (agreement.get('kind'), agreement.get('rule'), agreement.get('amount')):
        return 'economics_mismatch'
    amount = row.get('amount'); value = row.get('value_micros')
    if type(amount) is not int or amount <= 0 or type(value) is not int or value < 0:
        return 'invalid_amount'
    if row.get('kind') in {'subscription', 'transaction'} and value == 0:
        return 'not_paid_conversion'
    if row.get('rule') not in {'fixed', 'basis_points'}:
        return 'invalid_rule'
    expected = amount if row['rule'] == 'fixed' else amount * value // 10000
    if type(row.get('commission_micros')) is not int or row['commission_micros'] != expected:
        return 'amount_mismatch'
    return 'currently_eligible'


def build_report(directory, now=None):
    """Read a consistent SQLite snapshot, excluding expired rows without purging them.

    Does not instantiate Store/Registry, initialize schemas, renew records or assess commissions.
    The filesystem-owning local operator remains trusted; this is not fraud-proof accounting.
    """
    now = time.time() if now is None else now
    root = Path(directory)
    database = root / 'delegation.sqlite3'
    if root.is_symlink() or database.is_symlink() or not database.is_file():
        raise ValueError('existing non-symlink local database required')
    db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'network_referrals', 'providers'} <= tables:
            raise ValueError('network receipt ledger has not been initialized')
        cutoff = now - 30 * 86400
        providers = {r[0]: json.loads(r[1]) for r in db.execute('SELECT id,data FROM providers WHERE updated>=?', (cutoff,))}
        rows = [json.loads(r[0]) for r in db.execute('SELECT data FROM network_referrals WHERE created>=?', (cutoff,))]
        groups = {c: {'referrals': 0, 'states': {}, 'currently_eligible_count': 0,
                      'currently_eligible_microusd': 0, 'recorded_eligible_but_blocked': 0} for c in COHORTS}
        gates = Counter()
        for row in rows:
            cohort = ('internal' if row.get('internal') else
                      ('independent_operator_attested' if row.get('independent_evidence') else 'external_unverified'))
            group = groups[cohort]
            group['referrals'] += 1
            state = row.get('state') if row.get('state') in STATES else 'unknown'
            group['states'][state] = group['states'].get(state, 0) + 1
            gate = _gate(row, providers.get(row.get('provider_id')), now)
            if state == 'commission_eligible':
                gates[gate] += 1
                if gate == 'currently_eligible':
                    group['currently_eligible_count'] += 1
                    group['currently_eligible_microusd'] += row['commission_micros']
                else:
                    group['recorded_eligible_but_blocked'] += 1
        return {'format': 'resultgate-commission-report-v1',
                'generated_at': datetime.fromtimestamp(now, timezone.utc).isoformat(),
                'scope': 'network_receipt_ledger_only', 'currency': 'USD',
                'groups': groups, 'eligibility_gates': dict(sorted(gates.items())),
                'retention_days': 30, 'payments_enabled': False, 'invoices_created': 0,
                'amount_due_asserted': False, 'revenue_verified': False,
                'warning': 'Local operator-attested records, not proof of legal debt, settled revenue or independent adoption. Internal figures are simulations. Legacy delegation commissions are a separate ledger.'}
    finally:
        db.close()


def render_html(report):
    """Static escaped aggregates only: no JavaScript, remote assets or provider/customer IDs."""
    rows = []
    for cohort, values in report['groups'].items():
        states = ', '.join(f'{k}: {v}' for k, v in sorted(values['states'].items())) or 'none'
        cells = [cohort, values['referrals'], states, values['currently_eligible_count'],
                 values['currently_eligible_microusd'], values['recorded_eligible_but_blocked']]
        rows.append('<tr>' + ''.join('<td>' + escape(str(v)) + '</td>' for v in cells) + '</tr>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>ResultGate local commission review</title>'
            '<style>body{font:16px system-ui;margin:2rem;color:#172033}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.6rem;text-align:left}aside{padding:1rem;background:#fff1ce}</style>'
            '<h1>ResultGate local commission review</h1><aside>' + escape(report['warning']) + '</aside>'
            '<p>Payments disabled. No invoice or amount-due claim. Generated ' + escape(report['generated_at']) + '</p>'
            '<table><thead><tr><th>Cohort</th><th>Referrals</th><th>Recorded states</th><th>Currently eligible</th><th>Eligible microUSD</th><th>Recorded eligible, now blocked</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table><p>1 USD = 1,000,000 microUSD. Amounts are not collected revenue.</p>'
            '<h2>Eligibility gates</h2><pre>' + escape(json.dumps(report['eligibility_gates'], indent=2)) + '</pre></html>')


def write_private(path, content):
    """Create new private report, refusing overwrite including symlink destinations."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--format', choices=['json', 'html'], default='json')
    parser.add_argument('--output', help='New private file; omission writes to stdout')
    parser.add_argument('--consent-export', action='store_true')
    args = parser.parse_args()
    if not args.consent_export:
        parser.error('--consent-export required: this exports limited financial metadata')
    report = build_report(args.directory)
    content = render_html(report) if args.format == 'html' else json.dumps(report, indent=2) + '\n'
    if args.output:
        write_private(args.output, content)
    else:
        print(content)


if __name__ == '__main__':
    main()
