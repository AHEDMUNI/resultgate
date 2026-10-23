"""Public availability probe only. No visit, sale, or usage inference."""
import argparse,json,sqlite3,urllib.request
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from resultgate.referral_daily import daily
def build_report(day, db_path=None, probe=True):
    # Public Actions has no customer evidence. A private operator may supply an
    # existing database; missing paths fail rather than becoming empty reports.
    uri=Path(db_path).resolve().as_uri()+'?mode=ro' if db_path else ':memory:'
    with sqlite3.connect(uri,uri=bool(db_path)) as db:
        report=daily(db,day)
    report['evidence_source']='private_operator_database' if db_path else 'unavailable'
    report['generated_at']=datetime.now(ZoneInfo('America/Chicago')).isoformat()
    report['probe_origin']='internal';report['availability']={}
    report['availability_scope']='current internal probes, not observations from the reporting day'
    if probe:
        for path in ('/browseract','/referrals','/referrals.json'):
            try:
                req=urllib.request.Request('https://agents.allubiyerbamate.com'+path,
                    headers={'User-Agent':'ResultGate-Internal-Availability/1.0'})
                with urllib.request.urlopen(req,timeout=15) as response:
                    report['availability'][path]={'http_status':response.status,'probe_only':True}
            except Exception as error:
                report['availability'][path]={'http_status':getattr(error,'code',None),'error_type':type(error).__name__,'probe_only':True}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',help='Existing private evidence database; never upload it to public Actions')
    p.add_argument('--day',default=(datetime.now(ZoneInfo('America/Chicago')).date()-timedelta(days=1)).isoformat())
    p.add_argument('--no-probe',action='store_true')
    args=p.parse_args()
    print(json.dumps(build_report(args.day,args.db,not args.no_probe),indent=2))
