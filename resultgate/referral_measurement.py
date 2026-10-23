"""Operator-only local evidence log. No public telemetry or provider API claims."""
import argparse, json, sqlite3
from pathlib import Path
from datetime import datetime, timezone
EVENTS={'arrival','request','usage','referral_handoff','referral_click','registration_confirmed','commission_approved','commission_reversed','payout_received','attributed_transaction','commission_pending'}
ORIGINS={'internal','allubi','unknown','independent_verified'}
def record(db, event):
    if set(event)-{'id','kind','origin','evidence_ref','subject','amount_cents','currency','provider_id','occurred_at'}: raise ValueError('Unexpected fields; never log secrets or URLs with tokens')
    if event.get('kind') not in EVENTS or event.get('origin') not in ORIGINS: raise ValueError('Invalid classification')
    if 'provider_id' in event and event['provider_id'] not in {'browseract','searchapi','pdfco','make','apify','firecrawl'}: raise ValueError('Invalid provider')
    if 'occurred_at' in event:
        when=datetime.fromisoformat(event['occurred_at'])
        if when.tzinfo is None or when > datetime.now(timezone.utc): raise ValueError('Require actual past timezone-aware evidence time')
    import re
    for k in ('id','subject','evidence_ref'):
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}',event.get(k,'')): raise ValueError('Use opaque evidence identifiers, not private content')
    financial=event['kind'] in {'commission_approved','commission_reversed','payout_received','commission_pending','attributed_transaction'}
    amount=event.get('amount_cents',0)
    if type(amount)!=int or amount<0 or (financial and (amount==0 or event.get('currency')!='USD')): raise ValueError('Financial evidence requires positive integer USD cents')
    if not financial and amount: raise ValueError('Non-financial events cannot carry revenue')
    db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL, recorded_at TEXT NOT NULL)')
    payload=json.dumps(event,sort_keys=True)
    old=db.execute('SELECT payload FROM events WHERE id=?',(event['id'],)).fetchone()
    if old:
        if old[0]!=payload: raise ValueError('Conflicting duplicate evidence ID')
        return False
    db.execute('INSERT INTO events VALUES (?,?,?)',(event['id'],payload,datetime.now(timezone.utc).isoformat())); db.commit(); return True

def summary(db):
    db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL, recorded_at TEXT NOT NULL)')
    groups={o:{'counts':dict.fromkeys(sorted(EVENTS),0),'approved_cents':0,'reversed_cents':0,'paid_out_cents':0} for o in sorted(ORIGINS)}
    for (payload,) in db.execute('SELECT payload FROM events'):
        e=json.loads(payload); g=groups[e['origin']]; g['counts'][e['kind']]+=1
        key={'commission_approved':'approved_cents','commission_reversed':'reversed_cents','payout_received':'paid_out_cents'}.get(e['kind'])
        if key: g[key]+=e['amount_cents']
    return {'groups':groups,'evidence_policy':'Operator must inspect private provider statement for approval and bank/payment receipt for payout. This log does not authenticate uploads. Counts are events, not unique customers. Clicks are not sales.'}
if __name__=='__main__':
    import os
    os.umask(0o077)
    p=argparse.ArgumentParser(); p.add_argument('--db',required=True); p.add_argument('--event'); args=p.parse_args()
    with sqlite3.connect(args.db) as db:
        if args.event: record(db,json.loads(Path(args.event).read_text()))
        print(json.dumps(summary(db),indent=2))
