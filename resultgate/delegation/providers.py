"""Specialist adapters: no provider-defined executable code or arbitrary endpoints."""
from typing import Protocol
from urllib.parse import urlencode
import http.client
import socket
import time
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from resultgate.brokerage.transport import PinnedHTTPS, ProviderFailure
import ipaddress

class CitationTask(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    description: str=Field(min_length=1,max_length=500)
    required_capabilities: list[str]=Field(min_length=1,max_length=4)
    citation: str=Field(min_length=10,max_length=2000)
    expected_surname: str=Field(min_length=1,max_length=80)
    expected_year: int=Field(ge=1500,le=2100)

PROVIDERS=[
 {'id':'grobid_demo','name':'GROBID project demo','kind':'specialist_ml_service_not_autonomous_agent',
  'capabilities':['citation_structuring'],'transport':'https_form_post','auth':'none',
  'endpoint':'https://grobidorg-grobid.hf.space/api/processCitation','cost':'free demonstration only',
  'source':'https://grobid.readthedocs.io/en/latest/getting_started/',
  'reviewed':'2026-10-20','executable':True,'production_allowed':False,'commission_agreement':None},
 {'id':'claix_a2a','name':'Claix','kind':'provider_declared_a2a_document_agent_not_independently_executed',
  'capabilities':['document_extraction'],'transport':'a2a_jsonrpc_message_send','auth':'API key required',
  'endpoint':'https://claix.dev/a2a','cost':'trial advertised; entitlement unverified',
  'source':'https://www.claix.dev/documentation/a2a','reviewed':'2026-10-20',
  'executable':False,'production_allowed':None,'commission_agreement':None}]

class Adapter(Protocol):
    """Future reviewed MCP/A2A adapters implement this interface, not arbitrary URLs."""
    def execute(self, task: CitationTask) -> dict: ...

def validate(task):
    if not 0 <= (date.today()-date(2026,10,20)).days <= 30:
        raise ValueError('provider review expired; operator review required')
    parsed=CitationTask.model_validate(task)
    if parsed.required_capabilities!=['citation_structuring']:
        raise ValueError('unsupported capability set')
    return parsed

def parse_result(raw):
    if b'\x00' in raw or len(raw)>131072 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ProviderFailure('unsafe_or_oversize_xml')
    # Reject declarations before parsing; standard parser does not load external entities.
    try:
        root=ET.fromstring(raw,forbid_dtd=True,forbid_entities=True,forbid_external=True)
        if root.tag.split('}')[-1]!='biblStruct': raise ValueError()
        surnames=[]; years=[]; titles=[]
        for node in root.iter():
            tag=node.tag.split('}')[-1]
            if tag=='surname' and node.text: surnames.append(node.text[:80])
            if tag=='date' and node.get('when'): years.append(node.get('when')[:10])
            if tag=='title' and node.text: titles.append(node.text[:300])
        if not surnames or not years: raise ValueError()
        return {'surnames':surnames[:20],'years':years[:10],'titles':titles[:10],
                'untrusted_data':True,'provider_kind':'specialist_ml_service_not_autonomous_agent'}
    except (ET.ParseError,ValueError,DefusedXmlException):
        raise ProviderFailure('invalid_structured_output') from None

class GrobidAdapter:
    def execute(self,task):
        host='grobidorg-grobid.hf.space'
        conn=None
        try:
            addresses=list(dict.fromkeys(a[4][0] for a in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)))
            if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
                raise ProviderFailure('non_public_address')
            conn=PinnedHTTPS(host,addresses[0])
            conn.timeout=12
            body=urlencode({'citations':task.citation,'consolidateCitations':'0','includeRawCitations':'0'}).encode()
            conn.request('POST','/api/processCitation',body=body,headers={
                'Content-Type':'application/x-www-form-urlencoded','Accept':'application/xml',
                'Accept-Encoding':'identity','User-Agent':'ResultGate-delegation-demo/0.1 (https://github.com/AHEDMUNI/resultgate)'})
            response=conn.getresponse()
            if response.status!=200: raise ProviderFailure('http_'+str(response.status))
            if 'xml' not in response.headers.get('Content-Type','').lower(): raise ProviderFailure('unexpected_content_type')
            if response.headers.get('Content-Encoding','identity')!='identity': raise ProviderFailure('unexpected_encoding')
            raw=bytearray(); deadline=time.monotonic()+20
            while True:
                if time.monotonic()>deadline: raise ProviderFailure('timeout')
                chunk=response.read1(8192)
                if not chunk: break
                raw.extend(chunk)
                if len(raw)>131072: raise ProviderFailure('response_too_large')
            return parse_result(bytes(raw))
        except ProviderFailure: raise
        except TimeoutError: raise ProviderFailure('timeout') from None
        except (OSError,http.client.HTTPException): raise ProviderFailure('connection_error') from None
        finally:
            if conn is not None: conn.close()

def verify(task,result):
    return task.expected_surname.casefold() in [s.casefold() for s in result['surnames']] and str(task.expected_year) in [y[:4] for y in result['years']]
