import unittest
import test_market
from test_network import PROOF
from resultgate.network.settlement import SettlementSandbox

class SettlementTests(unittest.TestCase):
    setUp = test_market.MarketTests.setUp
    tearDown = test_market.MarketTests.tearDown
    create = test_market.MarketTests.create
    through = test_market.MarketTests.through

    def test_direct_once_balanced_and_refund_reversal(self):
        tid=self.through(); ledger=SettlementSandbox(self.m)
        self.assertFalse(ledger.accrue(tid)['duplicate'])
        self.assertTrue(SettlementSandbox(self.m).accrue(tid)['duplicate'])
        report=ledger.report()
        self.assertTrue(report['balanced']);self.assertFalse(report['real_debt_created'])
        self.assertEqual(report['postings']['hypothetical_commission_receivable'],1000000)
        self.o.advance(tid,'refund','refunded',evidence_sha256=PROOF)
        self.assertEqual(ledger.report()['unreconciled_or_blocked'],1)
        self.assertFalse(ledger.reverse(tid)['duplicate']);self.assertTrue(ledger.reverse(tid)['duplicate'])
        self.assertTrue(all(v==0 for v in ledger.report()['postings'].values()))
        self.assertEqual(ledger.report()['unreconciled_or_blocked'],0)

    def test_marketplace_split_and_conflicting_replay(self):
        tid=self.through();ledger=SettlementSandbox(self.m)
        ledger.accrue(tid,route='marketplace',fee_micros=300000)
        r=ledger.report();self.assertTrue(r['balanced'])
        self.assertEqual(r['postings']['hypothetical_provider_payable'],-8700000)
        with self.assertRaises(ValueError):ledger.accrue(tid,route='marketplace',fee_micros=400000)
        with self.assertRaises(ValueError):ledger.accrue(tid,route='direct')
        with self.assertRaises(ValueError):ledger.reverse(tid)

    def test_ungated_task_and_negative_net_rejected(self):
        tid=self.through('verified');ledger=SettlementSandbox(self.m)
        with self.assertRaises(ValueError):ledger.accrue(tid)
        self.assertEqual(ledger.report()['entries'],0)
        self.m.advance(self.provider,tid,'payment','transaction_proven',evidence_sha256=PROOF,
                       simulated_transaction_id_sha256=PROOF,simulated_value_micros=10000000)
        self.o.advance(tid,'assess','commission_eligible')
        for fee in [True,-1,9000001]:
            with self.assertRaises(ValueError):ledger.accrue(tid,route='marketplace',fee_micros=fee)
        with self.assertRaises(ValueError):ledger.accrue(tid,fee_micros=1)

    def test_agreement_revocation_blocks_new_and_flags_existing(self):
        tid=self.through();ledger=SettlementSandbox(self.m);ledger.accrue(tid)
        self.r.review(self.pid,'','',False)
        with self.assertRaises(ValueError):ledger.accrue(tid)
        self.assertEqual(ledger.report()['unreconciled_or_blocked'],1)
        self.assertFalse(ledger.report()['revenue_verified'])

    def test_deletion_and_retention_never_claim_current_eligibility(self):
        tid=self.through();ledger=SettlementSandbox(self.m);ledger.accrue(tid)
        self.m.delete(self.requester,tid)
        self.assertEqual(ledger.report()['unreconciled_or_blocked'],1)
        self.r.db.execute('UPDATE settlement_simulations SET created=0')
        ledger.purge();self.assertEqual(ledger.report()['entries'],0)
