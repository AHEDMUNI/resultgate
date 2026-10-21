#!/usr/bin/env python3
"""Publish only ResultGate static routes; preserve MCP; fail closed on unknown nginx layout."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

HOST = 'agents.allubiyerbamate.com'
PAGES = {'/':'index.html','/terms':'terms.html','/privacy':'privacy.html',
         '/refunds':'refunds.html','/providers':'providers.html','/contact':'contact.html',
         '/resultgate-site.css':'resultgate-site.css'}
ROOT_404 = re.compile(r'location\s+/\s*\{\s*return\s+404\s*;\s*\}')


def replacement(content, root):
    if len(re.findall(r'^\s*server_name\s+',content,re.M))!=1 or not re.search(r'\bserver_name\s+agents\.allubiyerbamate\.com\s*;',content):
        raise ValueError('Expected one dedicated agents hostname; refusing shared configuration')
    if 'ssl_certificate ' not in content or not re.search(r'location\s*=\s*/mcp\s*\{',content):
        raise ValueError('Expected existing TLS and exact MCP route')
    if content.count('# RESULTGATE BUSINESS START'):
        raise ValueError('Business site already configured; review update instead of reinstalling')
    if len(ROOT_404.findall(content))!=1:
        raise ValueError('Expected exactly one default 404 route; no configuration changed')
    blocks=['# RESULTGATE BUSINESS START']
    for url,name in PAGES.items():
        blocks.append('''location = %s {
        alias %s/%s;
        default_type %s;
        limit_except GET { deny all; }
        add_header Strict-Transport-Security "max-age=31536000" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer" always;
        add_header Content-Security-Policy "default-src 'none'; style-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'" always;
        add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
        add_header Cache-Control "no-cache" always;
    }''' % (url,root,name,'text/css' if name.endswith('.css') else 'text/html'))
    blocks += ['# RESULTGATE BUSINESS END','location / { return 404; }']
    return ROOT_404.sub(lambda _: '\n    '.join(blocks),content,count=1)


def run(*args):
    return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()


def probe(path):
    return run('curl','--silent','--show-error','--max-time','15','--resolve',HOST+':443:127.0.0.1',
               '--output','/dev/null','--write-out','%{http_code}','https://'+HOST+path)


def main():
    if os.geteuid()!=0: raise SystemExit('Run with sudo; no SSH key is required by this script.')
    source=Path(__file__).resolve().parents[1]/'web/business'
    contents={n:(source/n).read_bytes() for n in PAGES.values()}
    if any(len(v)>100000 for v in contents.values()): raise SystemExit('Unexpected asset size')
    release=hashlib.sha256(b''.join(contents[n] for n in sorted(contents))).hexdigest()[:16]
    destination=Path('/var/www/resultgate-business')/release
    candidates=set()
    for folder in ('/etc/nginx/sites-enabled','/etc/nginx/conf.d'):
        for path in Path(folder).glob('*'):
            if not path.is_file(): continue
            content=path.read_text()
            if re.search(r'\bserver_name\s+agents\.allubiyerbamate\.com\s*;',content) and 'ssl_certificate ' in content:
                candidates.add(path.resolve())
    if len(candidates)!=1: raise SystemExit('Cannot identify one dedicated TLS config. Nothing changed.')
    config=candidates.pop(); before=config.read_text(); after=replacement(before,str(destination))
    run('nginx','-t')
    if probe('/mcp')!='401': raise SystemExit('MCP baseline was not 401. Nothing changed.')
    destination.mkdir(parents=True,exist_ok=True,mode=0o755)
    os.chmod(destination.parent,0o755); os.chmod(destination,0o755)
    for name,data in contents.items():
        target=destination/name
        if target.is_symlink(): raise SystemExit('Unexpected asset symlink')
        target.write_bytes(data); target.chmod(0o644)
    backup_dir=Path('/var/backups/resultgate-business'); backup_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,backup_name=tempfile.mkstemp(prefix='nginx-',suffix='.conf',dir=backup_dir); os.close(fd)
    backup=Path(backup_name); shutil.copy2(config,backup)
    if config.read_text()!=before: raise SystemExit('Config changed concurrently; no config overwritten.')
    try:
        config.write_text(after)
        run('nginx','-t'); run('systemctl','reload','nginx')
        for path in PAGES:
            if probe(path)!='200': raise ValueError('Static route check failed: '+path)
        if probe('/mcp')!='401' or probe('/healthz')!='404' or probe('/v1/capabilities')!='404':
            raise ValueError('Gateway boundary check failed')
    except Exception:
        shutil.copy2(backup,config)
        run('nginx','-t'); run('systemctl','reload','nginx')
        raise SystemExit('Verification failed; previous nginx config restored. Inspect privately before retrying.') from None
    print('SUCCESS: all 7 public static routes HTTP 200; MCP HTTP 401; private routes HTTP 404.')
    print('No application restart, payment activation, DNS or other hostname changes.')
    print('URL: https://'+HOST+'/')
    print('Rollback backup: '+str(backup))
    print('Config: '+str(config))


if __name__=='__main__': main()
