"""Human-friendly local request preparation. No paid execution."""
import argparse
import json
from .service import Intake, catalog


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory')
    p.add_argument('--request-key')
    p.add_argument('--url')
    p.add_argument('--plan', choices=['free', 'hobby_monthly'], default='free')
    p.add_argument('--permission-confirmed', action='store_true')
    a = p.parse_args()
    if not a.url:
        print(json.dumps(catalog(), indent=2))
        return
    if not a.directory or not a.request_key:
        p.error('a URL requires --directory and --request-key')
    store = Intake(a.directory)
    try:
        print(json.dumps(store.prepare(a.request_key, a.url, a.permission_confirmed, a.plan), indent=2))
    finally:
        store.db.close()


if __name__ == '__main__':
    main()
