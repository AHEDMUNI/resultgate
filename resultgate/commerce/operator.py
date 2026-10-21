"""Local sandbox operator actions, never callable through MCP."""
import argparse
import json
from ..network.registry import Registry
from ..network.market import Market
from .core import Commerce, CommerceOperator


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',required=True)
    sub=p.add_subparsers(dest='action',required=True)
    review=sub.add_parser('review-provider'); review.add_argument('provider_id'); review.add_argument('test_account'); review.add_argument('evidence_sha')
    approve=sub.add_parser('approve-order'); approve.add_argument('order_id'); approve.add_argument('owner_hash'); approve.add_argument('quote_sha'); approve.add_argument('cap_cents',type=int); approve.add_argument('expires',type=float)
    grant=sub.add_parser('grant'); grant.add_argument('owner_hash'); grant.add_argument('service_id'); grant.add_argument('cap_cents',type=int); grant.add_argument('expires',type=float)
    use=sub.add_parser('use-grant'); use.add_argument('order_id'); use.add_argument('grant_id')
    revoke=sub.add_parser('revoke-grant'); revoke.add_argument('grant_id')
    a=p.parse_args(); r=Registry(a.directory); op=CommerceOperator(Commerce(Market(r)))
    try:
        if a.action=='review-provider': value=op.review_provider(a.provider_id,a.test_account,a.evidence_sha)
        elif a.action=='approve-order': value=op.approve_order(a.order_id,a.owner_hash,a.quote_sha,a.cap_cents,a.expires)
        elif a.action=='grant': value=op.grant(a.owner_hash,a.service_id,a.cap_cents,a.expires)
        elif a.action=='use-grant': value=op.use_grant(a.order_id,a.grant_id)
        else: value=op.revoke_grant(a.grant_id)
        print(json.dumps({'mode':'test','result':value}))
    finally: r.db.close()


if __name__=='__main__': main()
