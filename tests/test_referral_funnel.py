import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
from resultgate.referral_daily import daily
from resultgate.referral_measurement import record


class FunnelTests(unittest.TestCase):
    def test_handoff_click_registration_and_purchase_are_distinct(self):
        db=sqlite3.connect(':memory:')
        for i,kind in enumerate(('referral_handoff','referral_click','registration_confirmed','attributed_transaction')):
            event=dict(id=f'e{i}',subject='same-person',evidence_ref=f'proof{i}',
                       kind=kind,origin='independent_verified',provider_id='browseract',
                       occurred_at='2026-10-21T12:00:00+00:00')
            if kind=='attributed_transaction':event.update(amount_cents=1600,currency='USD')
            record(db,event)
            self.assertFalse(record(db,event))
        report=daily(db,'2026-10-21')['providers']['browseract']
        for stage in ('handoff','click','registration','attributed_transaction'):
            self.assertEqual(report[stage]['recorded_events']['independent_verified'],1)
            self.assertIsNone(report[stage]['total'])
        for stage in ('commission_pending','commission_approved','payout_received'):
            self.assertEqual(report[stage]['recorded_events']['independent_verified'],0)
            self.assertIsNone(report[stage]['total'])

    def test_internal_click_and_local_midnight_are_not_independent_or_previous_day(self):
        db=sqlite3.connect(':memory:')
        record(db,dict(id='click',subject='self-test',evidence_ref='test',kind='referral_click',
            origin='internal',provider_id='browseract',occurred_at='2026-10-22T05:01:00+00:00'))
        previous=daily(db,'2026-10-21')['providers']['browseract']['click']
        current=daily(db,'2026-10-22')['providers']['browseract']['click']
        self.assertEqual(previous['recorded_events']['internal'],0)
        self.assertEqual(current['recorded_events']['internal'],1)
        self.assertEqual(current['recorded_events']['independent_verified'],0)
        self.assertIsNone(current['total'])

    def test_private_report_reads_evidence_and_missing_database_fails(self):
        spec=importlib.util.spec_from_file_location('daily_status',Path(__file__).resolve().parents[1]/'scripts/referral_daily_status.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'events.sqlite'
            with self.assertRaises(sqlite3.OperationalError):
                module.build_report('2026-10-21',path,False)
            self.assertFalse(path.exists())
            with sqlite3.connect(path) as db:
                record(db,dict(id='r',subject='unknown',evidence_ref='proof',kind='request',
                    origin='unknown',provider_id='browseract',occurred_at='2026-10-21T15:00:00+00:00'))
            report=module.build_report('2026-10-21',path,False)
            self.assertEqual(report['evidence_source'],'private_operator_database')
            self.assertEqual(report['providers']['browseract']['recommendation']['recorded_events']['unknown'],1)
            self.assertIsNone(report['providers']['browseract']['recommendation']['total'])
