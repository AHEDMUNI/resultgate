"""Local-only administration: JSON on stdin avoids credentials in process arguments."""
import argparse
import json
import sys
from .registry import Registry

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',required=True)
    parser.add_argument('action',choices=['inspect','propose','review','approve-agreement'])
    args=parser.parse_args()
    data=json.loads(sys.stdin.read(16385))
    r=Registry(args.directory)
    if args.action=='inspect': result=r.get(data['provider_id'])
    elif args.action=='propose':
        result=r.propose_terms(data['provider_id'],data['terms'],data['kind'],data['rule'],data['amount'])
    elif args.action=='review':
        result=r.review(data['provider_id'],data.get('observed_challenge',''),data.get('evidence_sha256',''),data.get('approve') is True)
    else: result=r.approve_agreement(data['provider_id'],data['evidence_sha256'])
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
