"""Private provider admission records. No Stripe calls or payment activation.

Run only inside the operator-controlled financial store. Evidence digests refer to
privately reviewed originals; hashes by themselves are not identity verification.
Never expose this operator API through MCP or a public HTTP route.
"""
import hashlib
import json
import re
import time
from .core import hashed

POLICY = ('ResultGate commercial policy v2: 1500 basis points of eligible paid service '
          'subtotal; due on processor-confirmed payment, no completion condition; '
          'refunds reduce fees proportionately; disputes suspend entitlement, lost '
          'disputes reverse it; provider 8500 basis points before separately agreed '
          'processing costs and adjustments; no joining/monthly/recommendation fee.')
POLICY_SHA = hashlib.sha256(POLICY.encode()).hexdigest()
EVIDENCE = ('signed_agreement_sha256', 'signatory_authority_sha256',
            'service_rights_sha256', 'account_ownership_sha256',
            'scope_refund_support_sha256', 'cost_liability_allocation_sha256')


def validate_offer(record):
    """Validate a reviewer-entered record, never infer external consent."""
    expected = {'provider_id','service_id','account_id','price_cents','currency',
                'commission_bps','policy_sha256','accepted_at','reviewed_at',
                'reviewer_id','review_expires_at', *EVIDENCE}
    if not isinstance(record, dict) or set(record) != expected:
        raise ValueError('exact admission record required')
    for k in ('provider_id','service_id','reviewer_id'):
        if not isinstance(record[k],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',record[k]):
            raise ValueError('invalid record identifier')
    if not isinstance(record['account_id'],str) or not re.fullmatch(r'acct_[A-Za-z0-9]{1,64}',record['account_id']):
        raise ValueError('connected account binding required')
    if type(record['price_cents']) is not int or not 50 <= record['price_cents'] <= 10000000:
        raise ValueError('bounded USD price required')
    if record['currency'] != 'usd' or type(record['commission_bps']) is not int or record['commission_bps'] != 1500 or record['policy_sha256'] != POLICY_SHA:
        raise ValueError('current 15 percent policy required')
    for k in EVIDENCE:
        if not isinstance(record[k],str) or not re.fullmatch(r'[a-f0-9]{64}',record[k]):
            raise ValueError('private evidence digest required')
    now = int(time.time())
    for k in ('accepted_at','reviewed_at','review_expires_at'):
        if type(record[k]) is not int: raise ValueError('integer review timestamp required')
    if not 0 < record['accepted_at'] <= record['reviewed_at'] <= now < record['review_expires_at'] <= record['reviewed_at'] + 30*86400:
        raise ValueError('current bounded review required')
    return hashed(record)


class ProviderAdmission:
    """Append-only reviewed offers; a separate live implementation must enforce them."""
    def __init__(self, db):
        self.db = db
        db.execute('CREATE TABLE IF NOT EXISTS commercial_admissions (digest TEXT PRIMARY KEY, provider TEXT, service TEXT, record TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0)')

    def record(self, record):
        digest = validate_offer(record)
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO commercial_admissions(digest,provider,service,record) VALUES(?,?,?,?)',
                            (digest,record['provider_id'],record['service_id'],json.dumps(record,sort_keys=True)))
        return {'admission_digest':digest,'checkout_enabled':False}

    def revoke(self, digest):
        with self.db:
            if self.db.execute('UPDATE commercial_admissions SET revoked=1 WHERE digest=?',(digest,)).rowcount != 1:
                raise ValueError('unknown admission')

    def inspect(self, digest, *, provider_id, service_id, account_id, price_cents):
        row = self.db.execute('SELECT record,revoked FROM commercial_admissions WHERE digest=?',(digest,)).fetchone()
        if not row or row[1]: raise ValueError('admission unavailable')
        record = json.loads(row[0])
        if validate_offer(record) != digest: raise ValueError('admission integrity mismatch')
        if any(record[k] != v for k,v in {'provider_id':provider_id,'service_id':service_id,'account_id':account_id,'price_cents':price_cents}.items()):
            raise ValueError('offer binding mismatch')
        return {'admission_digest':digest,'commission_bps':1500,'checkout_enabled':False,
                'requires_current_stripe_capabilities':True,'requires_customer_consent':True}
