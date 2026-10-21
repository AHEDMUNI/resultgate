"""Reviewed single-DOI retrieval adapters; no free text, arbitrary URLs or code."""
import re
from urllib.parse import quote
from .catalog import get_provider, fresh
from .transport import ProviderFailure

DOI=re.compile(r'10\.[0-9]{4,9}/[A-Za-z0-9._;()/:+-]{1,180}\Z')

def descriptor(provider_id, doi):
    p=get_provider(provider_id)
    if not p.executable or not fresh(p):
        raise ValueError('no current executable adapter for this provider')
    if not isinstance(doi,str) or not DOI.fullmatch(doi) or '..' in doi or '//' in doi:
        raise ValueError('only a public DOI identifier is accepted; no URLs, secrets or text')
    return {'provider_id':p.id,'method':'GET','url':p.endpoint+quote(doi,safe=''),
            'authentication':'none','data_sent':['public DOI identifier','connection IP','ResultGate User-Agent'],
            'expected_cost_usd':0,'redirects_allowed':False}

def normalize(provider_id, doi, data):
    try:
        if provider_id=='crossref':
            record=data['message']
            actual=record['DOI']
            titles=record.get('title',[])
            title=titles[0] if titles else ''
        elif provider_id=='datacite':
            record=data['data']['attributes']
            actual=record['doi']
            titles=record.get('titles',[])
            title=titles[0]['title'] if titles else ''
        else: raise ValueError()
        if not isinstance(actual,str) or actual.lower()!=doi.lower() or not isinstance(title,str) or not title:
            raise ValueError()
        return {'doi':actual[:256], 'title':title[:2000], 'provider_id':provider_id,
                'evidence_scope':'provider metadata response; not factual or semantic verification',
                'untrusted_data':True}
    except (KeyError,IndexError,TypeError,ValueError):
        raise ProviderFailure('response_schema_mismatch') from None
