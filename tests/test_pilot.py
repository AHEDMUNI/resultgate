import tempfile
import unittest
from resultgate.delegation.store import Store
from resultgate.pilot_usage import export_summary
from resultgate.network.registry import Registry
from test_network import DATA, PROOF

class PilotTests(unittest.TestCase):
    def test_export_requires_consent(self):
        s=Store()
        with self.assertRaises(ValueError):export_summary(s)
        s.db.close()
    def test_export_minimal_and_not_verified(self):
        s=Store();r=export_summary(s,True)
        self.assertFalse(r['independent_adoption_proven'])
        self.assertEqual(set(r['task_counts']),{'internal','external_unverified','independent_verified'})
        self.assertEqual(len(r['installation_pseudonym']),64)
        self.assertNotIn('tasks',r);s.db.close()
    def test_pseudonym_stable_and_scoped(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d);a=export_summary(s,True);s.db.close()
            s=Store(d);self.assertEqual(a['installation_pseudonym'],export_summary(s,True)['installation_pseudonym']);s.db.close()
        s=Store();self.assertNotEqual(a['installation_pseudonym'],export_summary(s,True)['installation_pseudonym']);s.db.close()
    def test_revocation_clears_agreement(self):
        r=Registry();x=r.submit(DATA);p=x['provider'];pid=p['id']
        r.review(pid,p['challenge'],PROOF,True)
        a=r.propose_terms(pid,'SIMULATION: fixed amount on accepted task only','task','fixed',1)
        r.accept_terms(pid,x['management_token'],a['sha256'],True);r.approve_agreement(pid,PROOF)
        r.review(pid,'','',False)
        self.assertEqual(r.discover(),[]);self.assertIsNone(r.get(pid)['agreement'])
        r.review(pid,p['challenge'],PROOF,True)
        self.assertFalse(r.discover()[0]['commission_agreement_approved']);r.db.close()
