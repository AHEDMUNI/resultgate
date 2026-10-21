"""Private sandbox customer review, separate from agent/requester credentials.

An operator hands the one-time secret to an independently authenticated customer
through a private channel. This module does not perform identity verification and
must not be exposed through MCP. No live payment authorization is created.
"""
import re
import secrets
import time

from ..network.registry import atomic
from .core import fee, order_rate


class CustomerReview:
    def __init__(self, commerce):
        self.c = commerce
        self.store, self.db = commerce.store, commerce.db
        self.db.execute('''CREATE TABLE IF NOT EXISTS commerce_customer_reviews (
            token_hash TEXT PRIMARY KEY, order_id TEXT NOT NULL, owner TEXT NOT NULL,
            quote TEXT NOT NULL, evidence TEXT NOT NULL, expires INTEGER NOT NULL,
            consent_expires INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)''')

    def _pending(self, order):
        if order['mode'] != 'test' or order['state'] != 'awaiting_owner' or order['approval']:
            raise ValueError('unapproved pending sandbox order required')
        if self.db.execute('SELECT 1 FROM commerce_sessions WHERE order_id=?', (order['id'],)).fetchone():
            raise ValueError('existing session requires processor recovery')
        # The journal exists only once the adapter has attempted Checkout. An
        # uncertain POST may have created a session even without a local binding.
        exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='commerce_checkout_attempts'").fetchone()
        if exists and self.db.execute('SELECT 1 FROM commerce_checkout_attempts WHERE order_id=?', (order['id'],)).fetchone():
            raise ValueError('checkout attempt requires processor recovery')
        order_rate(order)

    @atomic
    def issue(self, order_id, owner_hash, quote_sha, identity_review_sha256, consent_expires):
        """Trusted operator only; evidence is a private attestation, not verified ID."""
        order = self.c.load('orders', order_id)
        self._pending(order)
        now = int(time.time())
        if (owner_hash != order['owner'] or quote_sha != order['quote_sha']
                or not isinstance(identity_review_sha256, str)
                or not re.fullmatch(r'[a-f0-9]{64}', identity_review_sha256)
                or type(consent_expires) is not int
                or not now + 1800 < consent_expires <= order['expires']):
            raise ValueError('bound customer identity, quote and consent lifetime required')
        if self.db.execute('SELECT count(*) FROM commerce_customer_reviews').fetchone()[0] >= 10000:
            raise ValueError('customer review capacity reached')
        # Reissuing invalidates every earlier unused challenge for this order.
        self.db.execute('UPDATE commerce_customer_reviews SET used=1 WHERE order_id=?', (order_id,))
        secret = secrets.token_hex(32)
        self.db.execute('INSERT INTO commerce_customer_reviews VALUES(?,?,?,?,?,?,?,0)',
                        (self.store.digest(secret), order_id, owner_hash, quote_sha,
                         identity_review_sha256, now + 600, consent_expires))
        return {'review_secret': secret, 'expires_at': now + 600, 'mode': 'test'}

    @atomic
    def accept(self, requester_token, order_id, review_secret, quote_sha, amount_cents, accepted):
        """Requires both requester ownership and the separate customer secret."""
        order = self.c.get(requester_token, order_id)
        if order['owner'] != self.c.actor(requester_token):
            raise ValueError('requester required')
        self._pending(order)
        fee(amount_cents)
        if (accepted is not True or amount_cents != order['amount'] or quote_sha != order['quote_sha']
                or not isinstance(review_secret, str) or not re.fullmatch(r'[a-f0-9]{64}', review_secret)):
            raise ValueError('exact quote, amount and explicit acceptance required')
        row = self.db.execute('SELECT order_id,owner,quote,evidence,expires,consent_expires,used FROM commerce_customer_reviews WHERE token_hash=?',
                              (self.store.digest(review_secret),)).fetchone()
        now = time.time()
        if (not row or row[6] or row[:3] != (order_id, order['owner'], quote_sha)
                or row[4] <= now or row[5] <= now + 1800 or order['expires'] <= now):
            raise ValueError('customer review unavailable or expired')
        self.db.execute('UPDATE commerce_customer_reviews SET used=1 WHERE token_hash=?',
                        (self.store.digest(review_secret),))
        order['approval'] = {'source': 'separate_customer_review_test', 'quote_sha': quote_sha,
                             'cap': amount_cents, 'expires': row[5],
                             'identity_review_sha256': row[3], 'accepted_at': int(now)}
        self.c.save('orders', order)
        return {'order_id': order_id, 'mode': 'test', 'approved': True, 'live_authorization': False}

    @atomic
    def cancel_before_checkout(self, requester_token, order_id):
        """No processor request; never claim an issued Checkout URL is cancelled."""
        order = self.c.get(requester_token, order_id)
        if order['owner'] != self.c.actor(requester_token):
            raise ValueError('requester required')
        if order['state'] == 'cancelled_test':
            return {'order_id': order_id, 'state': 'cancelled_test', 'mode': 'test'}
        check = dict(order, approval=None)
        self._pending(check)
        order.update(state='cancelled_test', approval=None)
        self.c.save('orders', order)
        self.db.execute('UPDATE commerce_customer_reviews SET used=1 WHERE order_id=?', (order_id,))
        return {'order_id': order_id, 'state': 'cancelled_test', 'mode': 'test'}
