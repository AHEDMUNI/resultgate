#!/usr/bin/env python3
"""Existing Express Sandbox account only. No account creation, payments or persistence.

Run interactively on the operator's machine/server. Key is read from /dev/tty with
getpass and retained only for these requests. Do not pipe input or capture output:
the returned single-use onboarding link is private. No third-party dependencies.
"""
import argparse
import getpass
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


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--account',required=True)
    p.add_argument('--status-only',action='store_true')
    a=p.parse_args()
    if not re.fullmatch(r'acct_[A-Za-z0-9]+',a.account): p.error('invalid account ID')
    if not sys.stdin.isatty(): p.error('interactive terminal required; never pipe a key')
    key=getpass.getpass('Paste Sandbox sk_test_ key (hidden; not saved): ')
    if not re.fullmatch(r'sk_test_[A-Za-z0-9]+',key): p.error('Only sk_test_ keys accepted. No live keys.')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def request(path, params=None):
        data=urllib.parse.urlencode(params).encode() if params is not None else None
        req=urllib.request.Request('https://api.stripe.com'+path,data=data,headers={'Authorization':'Bearer '+key})
        try:
            with opener.open(req,timeout=20) as response:
                raw=response.read(1024*1024+1)
        except urllib.error.HTTPError as error:
            raise ValueError('Stripe HTTP '+str(error.code)+'; check Sandbox/key/account permissions in dashboard') from None
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
    try: main()
    except (ValueError,KeyError,TypeError,urllib.error.URLError):
        sys.exit('Stopped safely: check Sandbox account/permissions/network. No account created or payment attempted.')
