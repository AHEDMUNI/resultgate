"""Exact capability matching, with explainable ranking and no guessed prices."""
from .catalog import CATALOG, fresh, public_entry

def match(required, free_only=True):
    if not isinstance(required,list) or not 1 <= len(required) <= 16 or any(not isinstance(c,str) or not 1 <= len(c) <= 64 for c in required):
        raise ValueError('provide 1..16 capability identifiers')
    required=set(required)
    results=[]
    for p in CATALOG:
        if not fresh(p) or not required.issubset(p.capabilities):
            continue
        if free_only and p.price_usd != 0:
            continue
        results.append({**public_entry(p), 'match_reason':'all requested capabilities documented',
                        'ranking_basis':'executable adapter, then known price, then stable ID'})
    return sorted(results,key=lambda p:(not p['executable'],p['price_usd'] is None,p['price_usd'] or 0,p['id']))
