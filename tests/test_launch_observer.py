import datetime as dt
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('observer',Path(__file__).resolve().parents[1]/'scripts/launch_observer.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class ObservationTests(unittest.TestCase):
    def test_no_clock_without_verified_offer_channel_and_order(self):
        self.assertEqual(m.clock({})['state'],'blocked')
        r={k:{'verified':True,'evidence_sha256':'a'*64} for k in m.GATES}
        self.assertEqual(m.clock(r)['state'],'ready_not_started')
        r['approved_offer']['verified']='true'
        self.assertEqual(m.clock(r)['state'],'blocked')

    def test_window_and_invalid_timestamps(self):
        r={k:{'verified':True,'evidence_sha256':'a'*64} for k in m.GATES}
        r['started_at']='2026-10-21T12:00:00+00:00'
        self.assertEqual(m.clock(r,dt.datetime(2026,10,24,12,tzinfo=dt.timezone.utc))['state'],'finished')
        self.assertEqual(m.clock(r,dt.datetime(2026,10,22,12,tzinfo=dt.timezone.utc))['state'],'running')
        r['started_at']='2026-10-21T12:00:00'
        self.assertEqual(m.clock(r)['state'],'invalid_start')

    def test_issues_are_unverified_and_internal_tests_excluded(self):
        def issue(n,login,kind='User'):
            return {'number':n,'title':'[Service interest] request','user':{'login':login,'type':kind}}
        data=[issue(1,'AHEDMUNI'),issue(2,'visitor'),issue(2,'visitor'),issue(3,'robot','Bot')]
        got=m.issues_summary(data)
        self.assertEqual(got['service_interest_unverified'],1)
        self.assertEqual(got['excluded_internal_or_bot'],2)
        self.assertNotIn('confirmed_customers',got)
