"""Read-only Stripe account inspection. Never creates accounts or payments.

Use a separately provisioned Accounts-read restricted key from a private file.
This report is not commercial approval and cannot enable Checkout.
"""
import os
import re
import stat

import httpx


def read_restricted_key(path):
    """No stdin, environment, argv secret, echo or permissive getpass fallback."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) & 0o077 or info.st_nlink != 1):
            raise ValueError('private_owner_only_regular_file_required')
        raw = os.read(fd, 513)
        if len(raw) > 512:
            raise ValueError('invalid_restricted_key')
        key = raw.decode('ascii').strip()
        if not re.fullmatch(r'rk_live_[A-Za-z0-9]{16,}', key):
            raise ValueError('live_read_restricted_key_required')
        return key
    finally:
        os.close(fd)


def summarize(account, expected_id=None):
    """Only allowlisted operational flags/counts; no identity data or API errors."""
    if not isinstance(account, dict) or account.get('object') != 'account':
        raise ValueError('invalid_account_response')
    aid = account.get('id', '')
    if not re.fullmatch(r'acct_[A-Za-z0-9]+', aid) or (expected_id and aid != expected_id):
        raise ValueError('account_binding_mismatch')
    flags = {k: account.get(k) if type(account.get(k)) is bool else None
             for k in ('charges_enabled', 'payouts_enabled', 'details_submitted')}
    req = account.get('requirements')
    counts = {}
    for field in ('currently_due', 'eventually_due', 'past_due', 'pending_verification', 'errors'):
        value = req.get(field) if isinstance(req, dict) else None
        counts[field] = len(value) if isinstance(value, list) else None
    caps = account.get('capabilities') or {}
    capability = {k: caps.get(k) if caps.get(k) in ('active', 'inactive', 'pending', 'unrequested') else None
                  for k in ('card_payments', 'transfers')}
    controller = account.get('controller') or {}
    fees = (controller.get('fees') or {}).get('payer')
    losses = (controller.get('losses') or {}).get('payments')
    return {'account_id': aid, 'observed_via': 'restricted_live_read_only', **flags,
            'requirement_counts': counts, 'capabilities': capability,
            'disabled_reason_present': bool(req.get('disabled_reason')) if isinstance(req, dict) else None,
            'fees_payer': fees if fees in ('application', 'account', 'application_express', 'application_custom') else None,
            'payments_loss_liability': losses if losses in ('application', 'stripe') else None,
            'connect_eligibility_confirmed': False,
            'provider_contract_verified': False, 'checkout_enabled': False}


def inspect_account(key, account_id=None, transport=None):
    if not isinstance(key, str) or not re.fullmatch(r'rk_live_[A-Za-z0-9]{16,}', key):
        raise ValueError('live_read_restricted_key_required')
    if account_id is not None and not re.fullmatch(r'acct_[A-Za-z0-9]+', account_id):
        raise ValueError('invalid_account_id')
    path = '/v1/account' if account_id is None else '/v1/accounts/' + account_id
    # No redirects/proxies, no mutation method, bounded response and deadline.
    with httpx.Client(timeout=15, trust_env=False, follow_redirects=False, transport=transport) as client:
        with client.stream('GET', 'https://api.stripe.com' + path,
                           headers={'Authorization': 'Bearer ' + key}) as response:
            if response.status_code != 200:
                raise ValueError('stripe_account_read_failed')
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > 1048576:
                    raise ValueError('stripe_response_too_large')
    import json
    return summarize(json.loads(data), account_id)


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file', required=True, help='Path only; never put the key in this argument')
    parser.add_argument('--account-id', help='Verified LIVE connected account; omit for platform account')
    args = parser.parse_args()
    try:
        report = inspect_account(read_restricted_key(args.key_file), args.account_id)
    except Exception:
        # Never print an exception, request, response, key or filesystem contents.
        print('{"status":"blocked","reason":"private_configuration_or_account_read_failed"}')
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
