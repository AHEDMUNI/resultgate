import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

from resultgate.network.registry import Registry
from resultgate.network.market import Market, MarketOperator
from resultgate.commerce.core import Commerce, CommerceOperator, TERMS_SHA
from resultgate.commerce.customer_review import CustomerReview


class CustomerReviewTests(unittest.TestCase):
    def setUp(self):
        self.initialize()

    def initialize(self, directory=None):
        self.registry = Registry(directory)
        market = Market(self.registry)
        self.issuer = MarketOperator(market)
        self.buyer = self.issuer.issue_credential('buyer')
        self.seller = self.issuer.issue_credential('seller')
        self.other = self.issuer.issue_credential('other')
        self.c = Commerce(market)
        self.op = CommerceOperator(self.c)
        provider = self.c.apply(self.seller, 'Fixture only', TERMS_SHA, True)
        self.op.review_provider(provider['id'], 'acct_fixture', 'a'*64)
        self.c.list_service(self.seller, provider['id'], 'fixture-v1', 'Fixture', 'analysis', 10000)
        self.order = self.c.order(self.buyer, 'fixture-v1', 'first')
        self.review = CustomerReview(self.c)

    def tearDown(self):
        self.registry.db.close()

    def issue(self):
        return self.review.issue(self.order['id'], self.order['owner'], self.order['quote_sha'],
                                 'a'*64, self.order['expires'])['review_secret']

    def accept(self, secret, **changes):
        params = dict(requester_token=self.buyer, order_id=self.order['id'], review_secret=secret,
                      quote_sha=self.order['quote_sha'], amount_cents=10000, accepted=True)
        params.update(changes)
        return self.review.accept(**params)

    def test_separate_secret_required_and_never_stored_in_plaintext(self):
        secret = self.issue()
        with self.assertRaises(ValueError): self.accept(self.buyer)
        stored = self.c.db.execute('SELECT * FROM commerce_customer_reviews').fetchone()
        self.assertNotIn(secret, json.dumps(stored))
        result = self.accept(secret)
        self.assertFalse(result['live_authorization'])
        self.assertEqual('test', result['mode'])
        self.assertEqual('10000', self.c.checkout_payload(self.buyer, self.order['id'])['line_items[0][price_data][unit_amount]'])
        with self.assertRaises(ValueError): self.accept(secret)

    def test_wrong_customer_provider_quote_amount_and_truthy_consent(self):
        secret = self.issue()
        for changes in ({'requester_token': self.other}, {'requester_token': self.seller},
                        {'quote_sha': 'b'*64}, {'amount_cents': True},
                        {'amount_cents': 9999}, {'accepted': 'true'}, {'accepted': 1}):
            with self.assertRaises(ValueError): self.accept(secret, **changes)
        self.assertTrue(self.accept(secret)['approved'])

    def test_expired_challenge_and_reissue(self):
        first = self.issue()
        second = self.issue()
        with self.assertRaises(ValueError): self.accept(first)
        with patch('resultgate.commerce.customer_review.time.time', return_value=time.time()+601):
            with self.assertRaises(ValueError): self.accept(second)

    def test_revoked_requester_cannot_approve(self):
        secret = self.issue()
        self.issuer.revoke(self.buyer)
        with self.assertRaises(ValueError): self.accept(secret)

    def test_recreating_handler_does_not_restore_used_secret(self):
        secret = self.issue()
        self.accept(secret)
        self.review = CustomerReview(self.c)
        with self.assertRaises(ValueError): self.accept(secret)

    @unittest.skipIf(os.name == 'nt', 'Private POSIX store permissions require Linux acceptance')
    def test_disk_restart_and_independent_connections_consume_once(self):
        import concurrent.futures
        import threading
        self.registry.db.close()
        with tempfile.TemporaryDirectory() as directory:
            self.initialize(directory)
            secret = self.issue()
            self.registry.db.close()
            self.registry = Registry(directory)
            self.c = Commerce(Market(self.registry))
            self.review = CustomerReview(self.c)
            other = Registry(directory)
            second = CustomerReview(Commerce(Market(other)))
            barrier = threading.Barrier(2)
            def attempt(review):
                barrier.wait()
                try:
                    return review.accept(self.buyer, self.order['id'], secret,
                                         self.order['quote_sha'], 10000, True)['approved']
                except ValueError:
                    return False
            try:
                with concurrent.futures.ThreadPoolExecutor(2) as pool:
                    results = list(pool.map(attempt, (self.review, second)))
                self.assertEqual([False, True], sorted(results))
                self.assertEqual(1, self.c.db.execute('SELECT used FROM commerce_customer_reviews').fetchone()[0])
            finally:
                other.db.close()
                self.registry.db.close()

    def test_cancel_invalidates_secret_and_all_checkout_paths(self):
        secret = self.issue()
        self.accept(secret)
        result = self.review.cancel_before_checkout(self.buyer, self.order['id'])
        self.assertEqual(result, self.review.cancel_before_checkout(self.buyer, self.order['id']))
        with self.assertRaises(ValueError): self.c.checkout_payload(self.buyer, self.order['id'])
        with self.assertRaises(ValueError): self.issue()
        with self.assertRaises(ValueError): self.op.approve_order(self.order['id'], self.order['owner'], self.order['quote_sha'], 10000, time.time()+2400)
        with self.assertRaises(ValueError): self.review.cancel_before_checkout(self.seller, self.order['id'])

    def test_uncertain_post_blocks_cancellation_and_new_consent(self):
        self.c.db.execute('CREATE TABLE commerce_checkout_attempts(order_id TEXT)')
        self.c.db.execute('INSERT INTO commerce_checkout_attempts VALUES(?)', (self.order['id'],))
        self.c.db.commit()
        with self.assertRaisesRegex(ValueError, 'processor recovery'): self.issue()
        with self.assertRaisesRegex(ValueError, 'processor recovery'):
            self.review.cancel_before_checkout(self.buyer, self.order['id'])
        self.assertEqual('awaiting_owner', self.c.get(self.buyer, self.order['id'])['state'])

    def test_bound_session_blocks_false_cancellation(self):
        self.c.db.execute('INSERT INTO commerce_sessions VALUES(?,?,?)', ('cs_test_fixture', self.order['id'], 'https://checkout.stripe.com/fixture'))
        self.c.db.commit()
        with self.assertRaisesRegex(ValueError, 'processor recovery'):
            self.review.cancel_before_checkout(self.buyer, self.order['id'])

    def test_checkout_revalidates_approval_quote_and_budget(self):
        secret = self.issue()
        self.accept(secret)
        order = self.c.get(self.buyer, self.order['id'])
        for change in ({'quote_sha': 'b'*64}, {'cap': 1}, {'cap': True}):
            bad = dict(order, approval=dict(order['approval'], **change))
            with self.c.db: self.c.save('orders', bad)
            with self.assertRaises(ValueError): self.c.checkout_payload(self.buyer, order['id'])

    def test_invalid_operator_binding_and_expiry(self):
        for owner, quote, evidence, expiry in (
                ('b'*64, self.order['quote_sha'], 'a'*64, self.order['expires']),
                (self.order['owner'], 'b'*64, 'a'*64, self.order['expires']),
                (self.order['owner'], self.order['quote_sha'], 'raw document', self.order['expires']),
                (self.order['owner'], self.order['quote_sha'], 'a'*64, True)):
            with self.assertRaises(ValueError): self.review.issue(self.order['id'], owner, quote, evidence, expiry)
