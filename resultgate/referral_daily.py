"""Private operator evidence report; missing measurement is never zero usage."""
import argparse,json,sqlite3
from datetime import date,datetime
from zoneinfo import ZoneInfo
from .referral_selector import catalog
STAGES={'reach':'arrival','recommendation':'request','handoff':'referral_handoff','usage':'usage','attributed_transaction':'attributed_transaction','commission_pending':'commission_pending','commission_approved':'commission_approved','payout_received':'payout_received','commission_reversed':'commission_reversed'}
def daily(db,day):
    date.fromisoformat(day)
    result={'day':day,'timezone':'America/Chicago','scope':'manually supplied evidence only','experiment_clock':'not_started_no_verified_active_acquisition_channel','providers':{},'unassigned_legacy_records':0,'limitations':['No provider feeds or web analytics connected. Total metrics unavailable, not zero.','Recorded events are not unique customers. Internal, ALLUBI and unknown origins never count as independent.','Evidence references are operator attestations, not authenticated payment proofs. Financial stages must not be added together.']}
    for p in catalog()['providers']:
        result['providers'][p['id']]={stage:{'total':None,'coverage':'unavailable','recorded_events':{origin:0 for origin in ('internal','allubi','unknown','independent_verified')},'recorded_amount_cents':{}} for stage in STAGES}
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'").fetchone()
    if not exists: return result
    for payload,recorded in db.execute('SELECT payload,recorded_at FROM events'):
        e=json.loads(payload); when=datetime.fromisoformat(e.get('occurred_at',recorded))
        if when.astimezone(ZoneInfo('America/Chicago')).date().isoformat()!=day: continue
        provider=e.get('provider_id')
        if not provider:
            result['unassigned_legacy_records']+=1; continue
        for stage,kind in STAGES.items():
            if e['kind']!=kind: continue
            item=result['providers'][provider][stage];item['recorded_events'][e['origin']]+=1
            if e.get('amount_cents'):
                item['recorded_amount_cents'][e['origin']]=item['recorded_amount_cents'].get(e['origin'],0)+e['amount_cents']
    return result
if __name__=='__main__':
    import os
    os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--day',required=True);a=p.parse_args()
    # Read only: never silently create an empty measurement database.
    from pathlib import Path
    with sqlite3.connect(Path(a.db).resolve().as_uri()+'?mode=ro',uri=True) as db: print(json.dumps(daily(db,a.day),indent=2))
