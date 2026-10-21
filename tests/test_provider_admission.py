import sqlite3
import time
import unittest
from resultgate.commerce.provider_admission import ProviderAdmission, POLICY_SHA, EVIDENCE

class ProviderAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:'); self.a=ProviderAdmission(self.db)
        now=int(time.time())
        self.r=dict(provider_id='provider_fixture',service_id='analysis_v1',account_id='acct_fixture',
                    price_cents=10000,currency='usd',commission_bps=1500,policy_sha256=POLICY_SHA,
                    accepted_at=now-10,reviewed_at=now-5,review_expires_at=now+3600,reviewer_id='reviewer_fixture')
        self.r.update({k:'a'*64 for k in EVIDENCE})
        self.binding={k:self.r[k] for k in ('provider_id','service_id','account_id','price_cents')}
    def tearDown(self): self.db.close()
    def test_valid_record_never_enables_payments_and_is_idempotent(self):
        first=self.a.record(self.r);self.assertEqual(first,self.a.record(self.r))
        result=self.a.inspect(first['admission_digest'],**self.binding)
        self.assertFalse(result['checkout_enabled']);self.assertEqual(1500,result['commission_bps'])
        self.assertEqual(1,self.db.execute('SELECT count(*) FROM commercial_admissions').fetchone()[0])
    def test_every_missing_evidence_and_old_rate_rejected(self):
        for k in EVIDENCE:
            r=dict(self.r);r.pop(k)
            with self.assertRaises(ValueError):self.a.record(r)
        for change in ({'commission_bps':500},{'policy_sha256':'b'*64},{'price_cents':True},{'currency':'eur'}):
            with self.assertRaises(ValueError):self.a.record(dict(self.r,**change))
    def test_expired_future_or_unbounded_review_rejected(self):
        now=int(time.time())
        for change in ({'review_expires_at':now-1},{'accepted_at':now+10},{'review_expires_at':now+31*86400}):
            with self.assertRaises(ValueError):self.a.record(dict(self.r,**change))
    def test_binding_cannot_change_after_acceptance(self):
        d=self.a.record(self.r)['admission_digest']
        for key,value in [('provider_id','another'),('service_id','another'),('account_id','acct_other'),('price_cents',20000)]:
            with self.assertRaises(ValueError):self.a.inspect(d,**dict(self.binding,**{key:value}))
    def test_revocation_cannot_be_undone_by_replay(self):
        d=self.a.record(self.r)['admission_digest'];self.a.revoke(d);self.a.record(self.r)
        with self.assertRaises(ValueError):self.a.inspect(d,**self.binding)
    def test_record_tampering_rejected(self):
        d=self.a.record(self.r)['admission_digest']
        self.db.execute("UPDATE commercial_admissions SET record=replace(record,'10000','20000')")
        with self.assertRaises(ValueError):self.a.inspect(d,**dict(self.binding,price_cents=20000))
    def test_raw_private_documents_or_secrets_not_accepted(self):
        for extra in ({'api_key':'never-store'},{'identity_document':'never-store'}):
            with self.assertRaises(ValueError):self.a.record(dict(self.r,**extra))
