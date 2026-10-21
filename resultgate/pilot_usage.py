"""Optional local aggregate export. Never sends data or verifies external adoption."""
import argparse
import json
from .delegation.store import Store

def export_summary(store, consent=False):
    if consent is not True:
        raise ValueError('explicit export consent required')
    summary=store.summary()
    return {'format':'resultgate-pilot-summary-v1',
            'installation_pseudonym':store.digest('pilot-installation-v1'),
            'task_counts':summary['tasks_by_cohort'],
            'verified_task_count':summary['verified_tasks'],
            'evidence_level':'self_reported_unverified',
            'independent_adoption_proven':False,'payments_enabled':False,
            'retention_days':30}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',required=True)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--export',action='store_true')
    group.add_argument('--delete-task')
    parser.add_argument('--consent',action='store_true')
    args=parser.parse_args()
    if args.export and not args.consent: parser.error('--export requires --consent')
    store=Store(args.directory)
    try:
        if args.export: print(json.dumps(export_summary(store,args.consent),indent=2))
        else:
            store.delete(args.delete_task)
            print(json.dumps({'deleted':True}))
    finally: store.db.close()

if __name__=='__main__': main()
