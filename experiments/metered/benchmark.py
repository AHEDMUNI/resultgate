"""Repeatable internal synthetic microbenchmark, not hosted capacity."""
import json
import secrets
import statistics
import time
from .service import ShadowService

def main():
    token=secrets.token_urlsafe(32)
    service=ShadowService(token,10000)
    payload={'records':[{'id':i,'value':'x'*80} for i in range(100)],'expected_count':100,
             'job_status':'completed','next_cursor':None,'truncated':False}
    times=[]
    for i in range(1000):
        start=time.perf_counter_ns()
        service.call(token,'extraction',payload,str(i))
        times.append((time.perf_counter_ns()-start)/1e6)
    print(json.dumps({'kind':'internal_synthetic_in_process','operations':1000,
        'records_per_request':100,'p50_ms':round(statistics.median(times),3),
        'p95_ms':round(sorted(times)[949],3),'total_seconds':round(sum(times)/1000,3),
        'external_uses':0,'revenue_usd':0}))

if __name__=='__main__':main()
