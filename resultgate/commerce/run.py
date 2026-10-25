"""Start isolated loopback sandbox. Never replaces the production gateway."""
import argparse
import os
from pathlib import Path
from ..network.registry import Registry
from ..network.market import Market
from .core import Commerce
from .http import create_app
from .stripe_test import StripeTest


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--directory',required=True)
    p.add_argument('--port',type=int,default=8776); p.add_argument('--stripe-test',action='store_true')
    p.add_argument('--return-origin',default='https://agents.allubiyerbamate.com')
    a=p.parse_args()
    if not 1024<=a.port<=65535: p.error('invalid port')
    if not (Path(a.directory)/'identity.key').is_file(): p.error('existing operator-initialized sandbox directory required')
    stripe=StripeTest(os.environ.get('STRIPE_TEST_SECRET_KEY',''),a.return_origin,enabled=True) if a.stripe_test else None
    app=create_app(Commerce(Market(Registry(a.directory))),stripe,os.environ.get('STRIPE_TEST_WEBHOOK_SECRET'))
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=a.port,access_log=False,proxy_headers=False,limit_concurrency=8)


if __name__=='__main__': main()
