#!/usr/bin/env python3
"""Read-only launch inventory. Never print service command lines or environments."""
import json
import subprocess


def command(*args):
    p=subprocess.run(args, capture_output=True, text=True, timeout=20)
    return p.stdout.strip() if p.returncode==0 else 'unavailable'

report={'application_service':command('systemctl','is-active','resultgate.service'),
        'discovery_timer_active':command('systemctl','is-active','resultgate-discovery.timer'),
        'discovery_timer_enabled':command('systemctl','is-enabled','resultgate-discovery.timer'),
        'application_not_restarted':True}
code='''import hashlib, importlib.metadata, json
from pathlib import Path
d=importlib.metadata.distribution("resultgate")
s=json.loads(d.read_text("direct_url.json") or "{}")
print(json.dumps({"installed_version":d.version,"installed_vcs_commit":s.get("vcs_info",{}).get("commit_id"),"gateway_sha256":hashlib.sha256(Path(d.locate_file("resultgate/network/gateway.py")).read_bytes()).hexdigest(),"commit_note":"null means installation metadata does not prove a git commit"}))'''
try:
    result=command('/opt/resultgate/venv/bin/python','-I','-c',code)
    report['installed_application']=json.loads(result)
except Exception:
    report['installed_application']={'status':'unavailable'}
print(json.dumps(report,indent=2))
