#!/usr/bin/env python3
"""One private, resumable $100 Stripe Sandbox acceptance; never a live sale.

No public listener, account creation, API-key file, shell interpolation or real money.
Run via exec in dedicated SSH. Existing production Python dependencies are read only.
"""
import fcntl
from contextlib import contextmanager
import termios
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import resource
import subprocess
import sys
import traceback
import tarfile
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stripe_sandbox_onboarding import read_test_key, finish, diagnostic

ACCOUNT = 'acct_1UT33gDkMsAxFBbN'
ORIGIN = 'https://agents.allubiyerbamate.com'
CLI_SHA = '59ac00af3ca11a02f76232642d6d534c5c0e9e433889b86006f5046d33baf657'
CLI_URL = 'https://github.com/stripe/stripe-cli/releases/download/v1.54.1/stripe_1.54.1_linux_x86_64.tar.gz'


@contextmanager
def quiet_terminal():
    fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY)
    previous=termios.tcgetattr(fd); private=list(previous)
    private[3] &= ~(termios.ECHO|termios.ECHONL)
    try:
        termios.tcsetattr(fd,termios.TCSAFLUSH,private)
        yield
    finally:
        termios.tcflush(fd,termios.TCIFLUSH)
        termios.tcsetattr(fd,termios.TCSANOW,previous)
        os.close(fd)


def save(path, data):
    temporary = path.with_suffix('.tmp')
    with open(temporary, 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2); out.flush(); os.fsync(out.fileno())
    os.replace(temporary, path)


def cli_binary(directory):
    """Pinned official release and published SHA256; executable is in private state."""
    target = directory / 'stripe-1.54.1'
    receipt = directory / 'stripe-executable.sha256'
    if target.exists():
        if target.is_symlink() or not receipt.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != receipt.read_text():
            raise RuntimeError('cli_integrity_failed')
        return str(target)
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RuntimeError('cli_platform_unsupported')
    print('Preparing pinned Stripe CLI (no key requested yet).', flush=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(CLI_URL, timeout=45) as response:
        blob = response.read(25 * 1024 * 1024 + 1)
    if hashlib.sha256(blob).hexdigest() != CLI_SHA:
        raise RuntimeError('cli_integrity_failed')
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz') as archive:
        member = archive.getmember('stripe')
        if not member.isfile() or member.size > 50 * 1024 * 1024:
            raise RuntimeError('cli_archive_invalid')
        executable = archive.extractfile(member).read()
    target.write_bytes(executable); target.chmod(0o700)
    receipt.write_text(hashlib.sha256(executable).hexdigest())
    return str(target)


class Receiver(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def do_POST(self):
        try:
            self.connection.settimeout(5)
            length = int(self.headers.get('Content-Length', '0'))
            if self.path != '/webhook' or not 0 < length <= 262144 or not self.server.signing:
                raise ValueError('invalid webhook envelope')
            from resultgate.commerce.stripe_test import verify_webhook
            event = verify_webhook(self.rfile.read(length), self.headers.get('Stripe-Signature'), self.server.signing)
            obj = event['data']['object']; kind = event['type']
            # Ignore other Sandbox activity; never apply another customer's event.
            relevant = (kind == 'checkout.session.completed' and obj.get('client_reference_id') == self.server.order)
            if kind == 'charge.refunded':
                row = self.server.commerce.db.execute('SELECT id FROM commerce_payments WHERE order_id=?', (self.server.order,)).fetchone()
                relevant = bool(row and obj.get('payment_intent') == row[0])
            if relevant:
                result = self.server.commerce.event(event)
                # Replay the SAME Stripe-signed event; require idempotent ledger handling.
                if not self.server.commerce.event(event).get('duplicate'):
                    raise ValueError('event replay not idempotent')
                record = {'id': event['id'], 'type': kind, 'signature_verified': True, 'duplicate_replay_verified': True}
                self.server.events[event['id']] = record
                save(self.server.directory / 'signed-events.json', list(self.server.events.values()))
                print('SIGNED EVENT VERIFIED: ' + event['id'] + ' ' + kind, flush=True)
            self.send_response(200); self.end_headers(); self.wfile.write(b'OK')
        except Exception:
            self.send_response(400); self.end_headers(); self.wfile.write(b'Rejected')


def start_listener(binary, key, server, config_directory):
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL', 'SSL_CERT_FILE', 'SSL_CERT_DIR')}
    # Secret is never in argv or a shell. Child environment is process-local;
    # same-UID/root processes remain a trust boundary. CLI config is ephemeral.
    env.update(STRIPE_API_KEY=key, STRIPE_DEVICE_NAME='resultgate-sandbox-acceptance',
               HOME=config_directory, XDG_CONFIG_HOME=config_directory,
               STRIPE_CLI_TELEMETRY_OPTOUT='1', STRIPE_CLI_SKIP_UPDATE_CHECK='1')
    proc = subprocess.Popen([binary, 'listen', '--forward-to', 'http://127.0.0.1:18776/webhook',
                             '--events', 'checkout.session.completed,charge.refunded'],
                            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    ready = threading.Event()
    def capture():
        # Do not log/print raw CLI output: includes the webhook signing secret.
        for line in proc.stdout:
            match = re.search(r'whsec_[A-Za-z0-9]+', line)
            if match:
                server.signing = match.group(); ready.set()
    threading.Thread(target=capture, daemon=True).start()
    if not ready.wait(45):
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        raise RuntimeError('stripe_listener_not_ready')
    return proc


def pump(server, proc, predicate, seconds):
    deadline = time.monotonic() + seconds
    while not predicate():
        if proc.poll() is not None: raise RuntimeError('stripe_listener_stopped')
        if time.monotonic() >= deadline: raise RuntimeError('signed_event_timeout_resume_same_run')
        server.handle_request()


def matched_report(op, order, server, proc, expected_fee, expected_provider):
    # Bounded read-only retry for Stripe object propagation; never retries a mutation.
    report = None
    for _ in range(8):
        report = op.reconcile(order)
        if report['matched']:
            if report['net_commission_cents'] != expected_fee or report['provider_net_before_costs_cents'] != expected_provider:
                raise RuntimeError('unexpected_reconciled_amounts')
            return report
        until = time.monotonic() + 2
        while time.monotonic() < until:
            if proc.poll() is not None: raise RuntimeError('stripe_listener_stopped')
            server.handle_request()
    raise RuntimeError('stripe_ledger_mismatch_review_report')


def execute(directory):
    # Dependency checks before requesting a secret; never modifies production venv.
    from resultgate.network.registry import Registry
    from resultgate.network.market import Market, MarketOperator
    from resultgate.commerce.core import Commerce, CommerceOperator, TERMS_SHA, hashed
    from resultgate.commerce.stripe_test import StripeTest
    from resultgate.commerce.connect_test import ConnectTest
    state_path = directory / 'run.json'
    if state_path.exists() and json.loads(state_path.read_text()).get('complete'):
        print('ALREADY COMPLETE — no new Checkout or refunds.', flush=True)
        print((directory / 'report.json').read_text(), flush=True)
        return
    binary = cli_binary(directory)
    server = HTTPServer(('127.0.0.1', 18776), Receiver)
    server.timeout = 1
    server.signing = None
    registry = None; proc = None
    try:
        key = read_test_key()
        registry = Registry(str(directory / 'registry'))
        c = Commerce(Market(registry)); stripe = StripeTest(key, ORIGIN, enabled=True); op = ConnectTest(c, stripe)
        server.commerce = c; server.directory = directory
        event_path = directory / 'signed-events.json'
        server.events = {e['id']: e for e in json.loads(event_path.read_text())} if event_path.exists() else {}
        if state_path.exists():
            state = json.loads(state_path.read_text())
        else:
            issuer = MarketOperator(c.market)
            state = {'mode': 'test', 'account': ACCOUNT, 'seller': issuer.issue_credential('acceptance-seller'),
                     'buyer': issuer.issue_credential('acceptance-buyer'), 'complete': False}
            save(state_path, state)
        if state.get('account') != ACCOUNT or state.get('mode') != 'test': raise RuntimeError('run_binding_invalid')
        print('SAFE PROGRESS: validating existing Sandbox account and private ledger.',flush=True)
        provider = c.apply(state['seller'], 'Owner-authorized Stripe Sandbox acceptance only', TERMS_SHA, True)
        op.adopt_account(provider['id'], ACCOUNT)
        op.review(provider['id'], hashed({'scope':'owner-authorized test only','account':ACCOUNT,'terms':TERMS_SHA}))
        c.list_service(state['seller'],provider['id'],'sandbox-acceptance-100','SANDBOX ONLY - ResultGate payment acceptance','sandbox_acceptance',10000)
        order = c.order(state['buyer'],'sandbox-acceptance-100','acceptance-one')
        state['order_id'] = order['id']; save(state_path,state); server.order = order['id']
        payment = lambda: c.db.execute('SELECT id,refunded FROM commerce_payments WHERE order_id=?',(order['id'],)).fetchone()
        with tempfile.TemporaryDirectory(prefix='resultgate-stripe-cli-') as config:
            print('SAFE PROGRESS: connecting Stripe signed-event listener.',flush=True)
            proc = start_listener(binary, key, server, config)
            print('SAFE PROGRESS: signed-event listener ready.',flush=True)
            if not payment():
                prior = c.db.execute('SELECT url FROM commerce_sessions WHERE order_id=?',(order['id'],)).fetchone()
                if prior:
                    checkout_url = prior[0]
                else:
                    if not order.get('approval'):
                        CommerceOperator(c).approve_order(order['id'],order['owner'],order['quote_sha'],10000,min(order['expires'],time.time()+3000))
                    # Fixed root return pages already exist; no new public financial route.
                    class AcceptanceStripe(StripeTest):
                        def request(self, method, path, data=None, key=None):
                            if method=='POST' and path=='/v1/checkout/sessions':
                                data=dict(data,success_url=ORIGIN+'/',cancel_url=ORIGIN+'/')
                            return super().request(method,path,data,key)
                    print('SAFE PROGRESS: requesting existing-order Checkout from Stripe.',flush=True)
                    adapter = AcceptanceStripe(key,ORIGIN,enabled=True)
                    checkout_url = adapter.checkout(c,state['buyer'],order['id'])['checkout_url']
                print('PRIVATE SANDBOX CHECKOUT — open in browser; do not screenshot URL:',flush=True)
                print(checkout_url,flush=True)
                print('Use test card 4242 4242 4242 4242, future expiry, any test CVC. Waiting up to 20 minutes.',flush=True)
                pump(server,proc,lambda: bool(payment()),1200)
            report_path = directory / 'report.json'
            reports = json.loads(report_path.read_text()) if report_path.exists() else {'mode':'test','account':ACCOUNT,'order_id':order['id'],'stages':{},'real_revenue_cents':0}
            for target, commission, provider_cents, label in ((0,500,9500,'paid'),(4000,300,5700,'partial_refund'),(10000,0,0,'full_refund')):
                if label in reports['stages']: continue
                print('SAFE PROGRESS: '+label,flush=True)
                current = payment()[1]
                if current > target: raise RuntimeError('stage_evidence_missing_review_before_resume')
                if target and current < target:
                    refund = op.refund(order['id'],target)
                    # Persist refund ID immediately before waiting for Stripe's signed event.
                    state.setdefault('refunds',{})[label]=refund; save(state_path,state)
                    pump(server,proc,lambda: payment()[1]>=target,180)
                    # Same cumulative request must not create a second refund.
                    op.refund(order['id'],target)
                report = matched_report(op,order['id'],server,proc,commission,provider_cents)
                ledger = [json.loads(r[0]) for r in c.db.execute('SELECT postings FROM commerce_ledger WHERE order_id=?',(order['id'],))]
                sums = {k:sum(row.get(k,0) for row in ledger) for k in ('test_processor_clearing','test_provider_entitlement','test_platform_commission')}
                if any(sum(row.values()) != 0 for row in ledger) or sums['test_platform_commission'] != -commission or sums['test_provider_entitlement'] != -provider_cents:
                    raise RuntimeError('ledger_postings_mismatch')
                report['checkout_session']=c.db.execute('SELECT id FROM commerce_sessions WHERE order_id=?',(order['id'],)).fetchone()[0]
                report['ledger_totals_cents']=sums
                report['refund']=state.get('refunds',{}).get(label)
                reports['stages'][label]=report
                reports['signed_events']=list(server.events.values())
                save(report_path,reports)
                print('SAFE STAGE REPORT: '+json.dumps({'stage':label,**report}),flush=True)
            state['complete']=True; save(state_path,state)
            print('SAFE FINAL REPORT (IDs and test amounts only):',flush=True)
            print(json.dumps(reports,indent=2),flush=True)
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
        server.server_close()
        if registry:registry.db.close()


def main():
    if not sys.stdin.isatty() or '--exec-session' not in sys.argv:
        raise RuntimeError('dedicated_interactive_exec_session_required')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0)); os.umask(0o077)
    directory=Path.home()/'.local/state/resultgate-stripe-sandbox-acceptance'
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid(): raise RuntimeError('unsafe_state_directory')
    directory.chmod(0o700)
    with open(directory/'run.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with quiet_terminal():
            execute(directory)


if __name__=='__main__':
    try:
        main()
    except (KeyboardInterrupt,EOFError):
        print('Stopped safely; preserve the same run directory. No live operation.',flush=True)
    except Exception as error:
        # Only fixed local labels/classes; never interpolate network bodies/keys/URLs.
        allowed={'cli_integrity_failed','cli_platform_unsupported','cli_archive_invalid','stripe_listener_not_ready',
                 'stripe_listener_stopped','signed_event_timeout_resume_same_run','unexpected_reconciled_amounts',
                 'stripe_ledger_mismatch_review_report','run_binding_invalid','stage_evidence_missing_review_before_resume',
                 'ledger_postings_mismatch','unsafe_state_directory','dedicated_interactive_exec_session_required'}
        code=('sandbox_python_dependency_missing' if isinstance(error,ModuleNotFoundError) else
              str(error) if isinstance(error,RuntimeError) and str(error) in allowed else diagnostic(error))
        if type(error).__name__=='StripeRequestRejected' and isinstance(getattr(error,'safe',None),dict):
            print('SAFE STRIPE ERROR: '+json.dumps(error.safe),flush=True)
        frames=traceback.extract_tb(error.__traceback__)
        locations=[{'file':Path(f.filename).name,'line':f.lineno} for f in frames if Path(f.filename).name in ('stripe_sandbox_acceptance.py','stripe_test.py','core.py','connect_test.py')]
        print('SAFE ERROR LOCATION: '+json.dumps(locations),flush=True)
        print('STOPPED: '+code+'; preserve the same run directory; do not start a new order.',flush=True)
    finally:
        try: finish()
        except (KeyboardInterrupt,EOFError,OSError): pass
