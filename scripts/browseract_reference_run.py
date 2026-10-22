#!/usr/bin/env python3
"""Internal direct-HTTP reference only; a scraping practice site, never BrowserAct."""
import json, re, time, sys, hashlib
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urljoin, urlsplit
from datetime import datetime, timezone
from html import unescape
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from resultgate.browseract_demo import Report, validate
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('Unexpected redirect')
def fetch(url):
    if urlsplit(url).hostname!='books.toscrape.com': raise ValueError('Only practice source allowed')
    with build_opener(NoRedirect()).open(Request(url,headers={'User-Agent':'ResultGate-internal-reference/1.0'}),timeout=25) as r:
        body=r.read(1_000_001)
        if len(body)>1_000_000: raise ValueError('Source too large')
        return body.decode('utf-8')
def extract(url, text):
    row={'source_url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'error':None,
         'product':None,'price':None,'currency':None,'availability':None}
    title=re.search(r'<h1>(.*?)</h1>',text,re.S)
    price=re.search(r'<p class="price_color">£([0-9]+\.[0-9]{2})</p>',text)
    stock=re.search(r'<p class="instock availability">(.*?)</p>',text,re.S)
    if title and price and stock and 'In stock' in stock[1]:
        row.update(product=unescape(title[1]),price=price[1],currency='GBP',availability='in_stock')
    else: row['error']='Required displayed field missing or ambiguous'
    return row
if __name__=='__main__':
    start=time.perf_counter(); out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
    home=fetch('https://books.toscrape.com/')
    if 'scraping' not in home.lower(): raise ValueError('Practice-site notice not found')
    urls=list(dict.fromkeys(urljoin('https://books.toscrape.com/',p) for p in re.findall(r'<h3><a href="([^"]+)"',home)))[:20]
    if len(urls)!=20: raise ValueError('Expected exactly 20 products')
    rows=[]; snapshots=[]
    for i,url in enumerate(urls):
        try:
            body=fetch(url); rows.append(extract(url,body))
            (out/f'source-{i+1:02}.html').write_text(body)
            snapshots.append({'url':url,'file':f'source-{i+1:02}.html','sha256':hashlib.sha256(body.encode()).hexdigest()})
        except Exception as e:
            rows.append({'source_url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'error':type(e).__name__})
    duration=time.perf_counter()-start
    # Re-fetch fixed positions for reproducible samples; parser agreement is not independent human validation.
    samples=[]
    for i in (0,4,9,14,19):
        try: samples.append(extract(urls[i],fetch(urls[i])))
        except Exception: pass
    report={'expected_urls':urls,'rows':rows,'sample_rows':samples,'origin':'internal','engine':'direct_http'}
    (out/'report.json').write_text(json.dumps(report,indent=2))
    (out/'validation.json').write_text(json.dumps(validate(Report(**report)),indent=2))
    (out/'manifest.json').write_text(json.dumps({'source_permission':'https://books.toscrape.com/ - scraping practice site; fictional products/prices, not merchant offers',
        'engine':'direct_http','origin':'internal','collection_seconds':round(duration,3),
        'human_setup_seconds':None,'human_interventions':None,'browseract_runtime_seconds':None,
        'comparison':'BrowserAct vs direct integration not measured; no performance advantage claimed.', 'snapshots':snapshots},indent=2))
    print(json.dumps({'rows':len(rows),'errors':sum(bool(r.get('error')) for r in rows),'seconds':round(duration,3),'directory':str(out)}))
