#!/usr/bin/env python3
"""Existing Express Sandbox account only. No account creation, payments or persistence.

Run interactively on the operator's machine/server. Key is read from /dev/tty with
strict no-echo input and retained only for these requests. Do not pipe input or capture output:
the returned single-use onboarding link is private. No third-party dependencies.
"""
import argparse
import os
import termios
import resource
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def hidden_input(prompt):
    """Linux controlling terminal only; no getpass fallback to echoed stdin."""
    fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
    previous = termios.tcgetattr(fd)
    private = list(previous)
    private[3] &= ~(termios.ECHO | termios.ECHONL)
    try:
        termios.tcsetattr(fd, termios.TCSAFLUSH, private)
        os.write(fd, prompt.encode())
        data = bytearray()
        while True:
            char = os.read(fd, 1)
            if not char: raise EOFError()
            if char in (b'\n', b'\r'): break
            data.extend(char)
            if len(data) > 512: raise ValueError('input_too_long')
        return data.decode('ascii')
    finally:
        # Discard buffered multiline paste before any possible shell is resumed.
        termios.tcflush(fd, termios.TCIFLUSH)
        termios.tcsetattr(fd, termios.TCSANOW, previous)
        os.write(fd, b'\n')
        os.close(fd)


def read_test_key():
    while True:
        key = hidden_input('READY FOR HIDDEN SANDBOX KEY (or type EXIT): ')
        if key == 'EXIT': raise EOFError()
        if re.fullmatch(r'sk_test_[A-Za-z0-9_]+', key): return key
        print('Input rejected; still INSIDE the secure reader. Test secret only; value not printed.', flush=True)


def finish():
    print('Reader finished. Type EXIT to close this SSH session; do not paste another key.', flush=True)
    while hidden_input('Hidden input; EXIT to close: ') != 'EXIT':
        print('Input discarded without display.', flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--account',required=True)
    p.add_argument('--status-only',action='store_true')
    p.add_argument('--exec-session',action='store_true')
    p.add_argument('--input-self-test',action='store_true')
    a=p.parse_args()
    if not re.fullmatch(r'acct_[A-Za-z0-9]+',a.account): p.error('invalid account ID')
    if not sys.stdin.isatty(): p.error('interactive terminal required; never pipe a key')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if not a.exec_session: p.error('Run via exec python3 with --exec-session; do not use the old command')
    if a.input_self_test:
        value = hidden_input('SELF TEST: type DEMO_ONLY then Enter (NO API key): ')
        print('SELF_TEST_OK' if value == 'DEMO_ONLY' else 'SELF_TEST_FAILED')
        return
    key=read_test_key()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def request(path, params=None):
        data=urllib.parse.urlencode(params).encode() if params is not None else None
        req=urllib.request.Request('https://api.stripe.com'+path,data=data,headers={'Authorization':'Bearer '+key})
        try:
            with opener.open(req,timeout=20) as response:
                raw=response.read(1024*1024+1)
        except urllib.error.HTTPError as error:
            raise RuntimeError('stripe_http_'+str(error.code)) from None
        if len(raw)>1024*1024: raise ValueError('oversized Stripe response')
        result=json.loads(raw)
        if not isinstance(result,dict) or result.get('livemode') is True: raise ValueError('invalid/test-only response required')
        return result
    account=request('/v1/accounts/'+a.account)
    if account.get('id') != a.account or account.get('type') != 'express' or account.get('country') != 'US':
        raise ValueError('Expected the selected existing US Express account')
    requirements=account.get('requirements') or {}
    safe={'account':account['id'],'mode':'test','account_created':False,
          'charges_enabled':account.get('charges_enabled'),'payouts_enabled':account.get('payouts_enabled'),
          'details_submitted':account.get('details_submitted'),'capabilities':account.get('capabilities'),
          'requirements':{k:requirements.get(k) for k in ('currently_due','eventually_due','past_due','pending_verification','disabled_reason')}}
    print('SAFE STATUS (may be shared):'); print(json.dumps(safe,indent=2))
    if a.status_only: return
    # Existing public informational page; never interprets returning as verification.
    result=request('/v1/account_links',{'account':a.account,'type':'account_onboarding',
        'return_url':'https://agents.allubiyerbamate.com/providers',
        'refresh_url':'https://agents.allubiyerbamate.com/providers'})
    link=urllib.parse.urlsplit(result.get('url',''))
    if link.scheme != 'https' or link.netloc != 'connect.stripe.com' or result.get('expires_at',0) <= time.time():
        raise ValueError('unexpected onboarding link')
    print('PRIVATE LINK — open yourself; do not screenshot or share:')
    print(result['url'])
    print('Use Stripe test data only. If link expires, rerun this command. Return page is informational, not approval.')


if __name__=='__main__':
    try:
        main()
        finish()
    except RuntimeError as error:
        # Only locally generated HTTP status, never Stripe response text or a key.
        code=str(error)
        print(code if re.fullmatch(r'stripe_http_[0-9]{3}',code) else 'operation_failed', flush=True)
        try: finish()
        except (EOFError, KeyboardInterrupt, OSError, termios.error): pass
    except (ValueError, KeyError, TypeError, urllib.error.URLError, OSError, termios.error):
        print('Stopped: terminal/network/response validation failed; no payment attempted.', flush=True)
        try: finish()
        except (EOFError, KeyboardInterrupt, OSError, termios.error): pass
    except (EOFError, KeyboardInterrupt):
        print('Secure session closed.', flush=True)
