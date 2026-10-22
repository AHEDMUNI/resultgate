"""Public availability probe only. No visit, sale, or usage inference."""
import json,sqlite3,urllib.request
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from resultgate.referral_daily import daily
report=daily(sqlite3.connect(':memory:'),(datetime.now(ZoneInfo('America/Chicago')).date()-timedelta(days=1)).isoformat())
report['probe_origin']='internal';report['availability']={}
for path in ('/browseract','/referrals','/referrals.json'):
    try:
        with urllib.request.urlopen('https://agents.allubiyerbamate.com'+path,timeout=15) as response:
            report['availability'][path]={'http_status':response.status,'probe_only':True}
    except Exception as error:
        report['availability'][path]={'http_status':getattr(error,'code',None),'error_type':type(error).__name__,'probe_only':True}
print(json.dumps(report,indent=2))
