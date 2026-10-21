"""Private local operator commands, Stripe sandbox only. Never expose as MCP tools."""
import argparse
import getpass
import json
import os
from pathlib import Path
import httpx
from ..network.registry import Registry
from ..network.market import Market
from .core import Commerce
from .stripe_test import StripeTest
from .connect_test import ConnectTest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',required=True)
    p.add_argument('--return-origin',required=True,help='Operator-approved HTTPS sandbox return origin')
    p.add_argument('--stripe-test',action='store_true',required=True)
    sub=p.add_subparsers(dest='action',required=True)
    for name in ('create-account','onboarding-link','review-provider','reconcile','refund'):
        child=sub.add_parser(name); child.add_argument('id')
        if name=='review-provider': child.add_argument('evidence_sha')
        if name=='refund': child.add_argument('cumulative_cents',type=int)
    a=p.parse_args()
    if not (Path(a.directory)/'identity.key').is_file(): p.error('existing separate sandbox registry required')
    secret=os.environ.get('STRIPE_TEST_SECRET_KEY') or getpass.getpass('Stripe TEST key (hidden; never saved): ')
    registry=None
    try:
        stripe=StripeTest(secret,a.return_origin,enabled=a.stripe_test)
        registry=Registry(a.directory); op=ConnectTest(Commerce(Market(registry)),stripe)
        if a.action=='create-account': result=op.create_account(a.id)
        elif a.action=='onboarding-link': result=op.onboarding_link(a.id)
        elif a.action=='review-provider': result=op.review(a.id,a.evidence_sha)
        elif a.action=='refund': result=op.refund(a.id,a.cumulative_cents)
        else: result=op.reconcile(a.id)
        print(json.dumps(result))
    except (ValueError,KeyError,TypeError,httpx.HTTPError):
        p.exit(1,'Blocked: sandbox prerequisites, object binding or Stripe operation failed. Inspect in Stripe Sandbox; never retry an ambiguous refund under a new identifier.\n')
    finally:
        if registry: registry.db.close()


if __name__=='__main__': main()
