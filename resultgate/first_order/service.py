"""Real request intake and evidence checks, with paid execution deliberately unavailable.

This local store is single-owner, not a public multi-tenant authorization system.
Approval is operator-only; no MCP tool can create, expand or bypass it.
"""
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from urllib.parse import urlsplit

PRICE_CHECKED = 1792540800  # 2026-10-21 UTC
TERMS = 'public-page-markdown-v1'
BLOCKERS = ['provider_agreement_unconfirmed', 'verified_payment_attribution_unavailable',
            'paid_executor_not_enabled']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def public_url(value):
    if not isinstance(value, str) or len(value) > 2048 or re.search(r'[\s\\\x00-\x1f]', value):
        raise ValueError('public HTTPS URL required')
    p = urlsplit(value)
    host = p.hostname or ''
    if (p.scheme != 'https' or p.username or p.password or p.port not in (None, 443)
            or p.query or p.fragment or '.' not in host or host.endswith(('.local', '.internal', '.localhost'))):
        raise ValueError('HTTPS public hostname without query, credentials or fragment required')
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r'[a-zA-Z0-9.-]+', host):
            raise ValueError('invalid hostname') from None
    else:
        raise ValueError('IP literals not accepted')
    return value


def catalog():
    return {'service': 'public-page-markdown', 'scope': 'one permitted public HTML page',
            'execution_enabled': False, 'agreement_status': 'unconfirmed',
            'checked_at': '2026-10-21', 'resultgate_fee_usd': 0,
            'ranking_basis': 'native markdown output, then full monthly entry price; no commission weighting',
            'providers': [
                {'id': 'firecrawl', 'rank': 1, 'reason': 'Native markdown; lower paid entry price',
                 'monthly_subscription_usd': 19, 'included_credits': 5000,
                 'free_option': '1000 credits/month, provider eligibility applies',
                 'pricing_source': 'https://www.firecrawl.dev/pricing',
                 'advertised_commission': '25% for 12 months then 15%; NOT agreed with ResultGate',
                 'affiliate_source': 'https://www.firecrawl.dev/affiliates'},
                {'id': 'scraperapi', 'rank': 2, 'reason': 'Raw HTML alternative; requires separate markdown conversion',
                 'monthly_subscription_usd': 49, 'included_credits': 100000,
                 'pricing_source': 'https://www.scraperapi.com/pricing/',
                 'advertised_commission': '50% advertised; written rate and eligibility unconfirmed',
                 'affiliate_source': 'https://www.scraperapi.com/affiliate-terms/'}],
            'quality': 'No comparative benchmark or provider SLA independently verified',
            'disclosure': 'No active referral agreement. No referral link or commission is currently applied.',
            'blockers': BLOCKERS.copy()}


class Intake:
    def __init__(self, directory, clock=time.time):
        self.clock = clock
        path = Path(directory)
        if path.is_symlink():
            raise ValueError('private directory required')
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.stat().st_mode & 0o077:
            raise ValueError('directory must have mode 0700')
        dbpath = path / 'first-order.sqlite3'
        if dbpath.is_symlink():
            raise ValueError('database symlink rejected')
        fd = os.open(dbpath, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        os.chmod(dbpath, 0o600)
        self.db = sqlite3.connect(dbpath)
        self.db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, request_key TEXT UNIQUE, spec TEXT, quote TEXT, approval TEXT)')

    def prepare(self, request_key, url, permission_confirmed=False, plan="free"):
        if plan not in ("free", "hobby_monthly"):
            raise ValueError("explicit supported billing plan required")
        if not isinstance(request_key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', request_key):
            raise ValueError('opaque request key required')
        url = public_url(url)
        if permission_confirmed is not True:
            raise ValueError('confirm permission to collect this public page')
        # No URL or content is stored. Permission is caller-declared, not independently verified.
        spec = digest({'url': url, 'terms': TERMS, 'plan': plan})
        row = self.db.execute('SELECT spec,quote FROM requests WHERE request_key=?', (request_key,)).fetchone()
        if row:
            if row[0] != spec:
                raise ValueError('idempotency conflict')
            return json.loads(row[1])
        if self.db.execute('SELECT count(*) FROM requests').fetchone()[0] >= 1000:
            raise ValueError('local intake capacity reached; operator review required')
        quote = {'request_id': secrets.token_hex(16), 'task_sha256': spec, 'terms_version': TERMS,
                 'provider': 'firecrawl', 'currency': 'USD', 'plan': plan, 'subscription_first_month_micros': 0 if plan == 'free' else 19000000,
                 'billing': ('Free allowance only; no purchase or top-up.' if plan == 'free' else
                             'Customer pays provider directly; recurring $19/month if subscribing; cancel at provider.'),
                 'usage': 'One basic HTML scrape normally consumes 1 credit; no auto top-up or purchase authorized.',
                 'resultgate_fee_micros': 0, 'expires_at': self.clock() + 3600,
                 'price_stale': self.clock() > PRICE_CHECKED + 30*86400,
                 'state': 'awaiting_owner_approval', 'execution_enabled': False,
                 'blockers': BLOCKERS.copy(), 'disclosure': catalog()['disclosure']}
        quote['quote_sha256'] = digest(quote)
        with self.db:
            self.db.execute('INSERT INTO requests VALUES(?,?,?,?,NULL)',
                            (quote['request_id'], request_key, spec, json.dumps(quote)))
        return quote

    def get(self, request_id):
        row = self.db.execute('SELECT quote,approval FROM requests WHERE id=?', (request_id,)).fetchone()
        if not row:
            raise ValueError('unknown request')
        quote = json.loads(row[0])
        approval = json.loads(row[1]) if row[1] else None
        approved = bool(approval and self.clock() < approval['expires_at'] and self.clock() < quote['expires_at'])
        return {'quote': quote, 'owner_approval_current': approved,
                'execution_enabled': False, 'blockers': BLOCKERS.copy(), 'revenue_micros': 0}

    def approve(self, request_id, quote_sha256, max_cost_micros, expires_at):
        # Trusted owner CLI only. Exact quote scope, never a general spending grant.
        quote = self.get(request_id)['quote']
        if (quote_sha256 != quote['quote_sha256'] or quote['price_stale']
                or type(max_cost_micros) is not int or max_cost_micros < quote['subscription_first_month_micros']
                or not self.clock() < expires_at <= quote['expires_at']):
            raise ValueError('quote, budget or expiry mismatch')
        approval = {'quote_sha256': quote_sha256, 'max_cost_micros': max_cost_micros,
                    'expires_at': expires_at, 'scope': TERMS}
        with self.db:
            self.db.execute('UPDATE requests SET approval=? WHERE id=?', (json.dumps(approval), request_id))
        return self.get(request_id)

    def revoke(self, request_id):
        self.get(request_id)
        with self.db:
            self.db.execute('UPDATE requests SET approval=NULL WHERE id=?', (request_id,))
        return self.get(request_id)


def request_template(url):
    """An official API-shaped plan, not a callable transport or execution permission."""
    return {'method': 'POST', 'endpoint': 'https://api.firecrawl.dev/v2/scrape',
            'body': {'url': public_url(url), 'formats': ['markdown'], 'onlyMainContent': True},
            'execution_enabled': False, 'credential_handling': 'Never submit keys to intake or commit them',
            'blockers': BLOCKERS.copy()}


def verify_result(url, response):
    public_url(url)
    if not isinstance(response, dict) or len(json.dumps(response).encode()) > 1024*1024:
        raise ValueError('bounded provider response required')
    data = response.get('data')
    if not isinstance(data, dict):
        data = {}
    metadata = data.get('metadata')
    if not isinstance(metadata, dict):
        metadata = {}
    markdown = data.get('markdown')
    checks = {'provider_success': response.get('success') is True,
              'source_matches': metadata.get('sourceURL') == url,
              'http_ok': type(metadata.get('statusCode')) is int and 200 <= metadata['statusCode'] < 300,
              'nonempty_markdown': isinstance(markdown, str) and bool(markdown.strip()),
              'no_reported_error': not metadata.get('error') and not response.get('error')}
    return {'status': 'contract_pass' if all(checks.values()) else 'needs_review', 'checks': checks,
            'evidence_sha256': digest(response), 'persisted_content': False,
            'unverified': ['origin/authenticity of supplied response', 'semantic accuracy',
                           'completeness against live page', 'permission', 'payment', 'commission'],
            'payment_proven': False, 'commission_earned': False}
