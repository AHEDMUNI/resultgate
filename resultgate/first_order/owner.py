"""Owner-only local review; never expose as an MCP tool or public HTTP endpoint."""
import argparse
import json
from .service import Intake


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', required=True)
    p.add_argument('action', choices=['show', 'approve', 'revoke'])
    p.add_argument('request_id')
    p.add_argument('--quote-sha256')
    p.add_argument('--max-cost-micros', type=int)
    p.add_argument('--expires-at', type=float)
    a = p.parse_args()
    store = Intake(a.directory)
    if a.action == 'approve':
        if None in (a.quote_sha256, a.max_cost_micros, a.expires_at):
            p.error('approval requires quote hash, maximum cost and expiry')
        result = store.approve(a.request_id, a.quote_sha256, a.max_cost_micros, a.expires_at)
    elif a.action == 'revoke':
        result = store.revoke(a.request_id)
    else:
        result = store.get(a.request_id)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
