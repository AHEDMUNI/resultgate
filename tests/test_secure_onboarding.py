import importlib.util
import os
import pathlib
import pty
import select
import tempfile
import time
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class SecureInputTests(unittest.TestCase):
    def test_real_pty_rejects_invalid_input_without_echo_or_exit(self):
        pid,fd=pty.fork()
        if pid==0:
            try:
                m=module('stripe_sandbox_onboarding')
                m.read_test_key()
            except EOFError: pass
            finally: os._exit(0)
        output=b''
        def until(needle):
            nonlocal output
            deadline=time.monotonic()+5
            while needle not in output:
                if time.monotonic()>deadline: self.fail('terminal reader timed out')
                if select.select([fd],[],[],0.2)[0]: output+=os.read(fd,4096)
        try:
            until(b'READY FOR HIDDEN')
            os.write(fd,'اختبار_عربي_SECRET_FIXTURE\nPASTED_SECOND_LINE_SECRET\n'.encode('utf-8'))
            until(b'Input rejected')
            # Ensure next no-echo prompt has been emitted before ending the reader.
            while output.count(b'READY FOR HIDDEN')<2:
                if select.select([fd],[],[],1)[0]:output+=os.read(fd,4096)
                else:self.fail('reader did not retry')
            self.assertNotIn('اختبار_عربي'.encode('utf-8'),output)
            self.assertNotIn(b'UnicodeDecodeError',output)
            self.assertNotIn(b'PASTED_SECOND_LINE_SECRET',output)
            os.write(fd,b'EXIT\n')
            _,status=os.waitpid(pid,0);self.assertEqual(0,status)
        finally:os.close(fd)

    def test_history_redaction_keeps_other_commands_and_no_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory)/'history'
            p.write_bytes(b'ls\n#123\nsk_test_FAKE_ONLY\necho ok\nrk_live_FAKE_ONLY\n')
            self.assertEqual(2,module('redact_bash_keys').scrub(p))
            self.assertEqual(b'ls\necho ok\n',p.read_bytes())
            self.assertEqual([p],list(pathlib.Path(directory).iterdir()))
            self.assertEqual(0,module('redact_bash_keys').scrub(p))

    def test_history_symlink_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            p=pathlib.Path(directory)/'history';p.write_text('ls\n')
            link=pathlib.Path(directory)/'link';link.symlink_to(p)
            with self.assertRaises(ValueError):module('redact_bash_keys').scrub(link)

    def test_finish_handles_unicode_and_malformed_utf8(self):
        from unittest.mock import patch
        m=module('stripe_sandbox_onboarding')
        with patch.object(m,'hidden_input',side_effect=['عربي', '\ufffd', ValueError('input_too_long'), '']), patch('builtins.print'):
            m.finish()

    def test_diagnostics_never_expose_exception_content(self):
        m=module('stripe_sandbox_onboarding')
        for error in (ValueError('sk_test_FAKE'), OSError('sk_test_FAKE'),
                      m.urllib.error.URLError('sk_test_FAKE'), RuntimeError('sk_test_FAKE')):
            self.assertNotIn('sk_test', m.diagnostic(error))
        self.assertEqual('stripe_connection_failed',m.diagnostic(m.urllib.error.URLError('private')))
        self.assertEqual('stripe_http_401',m.diagnostic(RuntimeError('stripe_http_401')))

    def test_account_validation_distinguishes_fixed_failure_codes(self):
        m=module('stripe_sandbox_onboarding')
        for account, code in (({'id':'acct_other'},'account_id_mismatch'),
                              ({'id':'acct_selected','type':'standard'},'account_not_express'),
                              ({'id':'acct_selected','type':'express','country':'CA'},'account_country_not_us')):
            with self.assertRaises(RuntimeError) as raised: m.validate_account(account,'acct_selected')
            self.assertEqual(code,m.diagnostic(raised.exception))

    def test_controller_diagnostic_is_explicit_allowlist(self):
        m=module('stripe_sandbox_onboarding')
        result=m.safe_controller({'controller':{'secret':'DO_NOT_PRINT','stripe_dashboard':{'type':'express','secret':'DO_NOT_PRINT'},'requirement_collection':'stripe','fees':{'payer':'application'}}})
        self.assertEqual('express',result['dashboard_type'])
        self.assertNotIn('DO_NOT_PRINT',str(result))
