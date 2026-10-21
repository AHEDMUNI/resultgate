"""Prepare then explicitly execute one free public request. No automatic fallback or retries."""
import hashlib
import json
import re
import secrets
import time
from .adapters import descriptor, normalize
from .referrals import Ledger
from .transport import fetch_json, ProviderFailure

class Broker:
    def __init__(self, allow_network=False):
        self.allow_network=allow_network
        self.ledger=Ledger()

    def route(self,provider_id,doi,request_id):
        spec=descriptor(provider_id,doi)
        if not isinstance(request_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',request_id):
            raise ValueError('request_id must be an opaque 1..128 character identifier')
        ledger=self.ledger
        key=ledger.digest(request_id)
        fingerprint=ledger.digest(provider_id+'\0'+doi)
        with ledger.lock:
            ledger.purge()
            existing=ledger.keys.get(key)
            if existing:
                if ledger.events[existing]['_fingerprint']!=fingerprint:
                    raise ValueError('request_id conflict')
                route_id=existing
            else:
                if len(ledger.events)>=1000: raise ValueError('session route limit reached')
                route_id=secrets.token_hex(16)
                ledger.keys[key]=route_id
                ledger.events[route_id]={'route_id':route_id,'provider_id':provider_id,'status':'prepared',
                    'execution_evidence':None,'commission_usd':0,'commission_status':'no_agreement',
                    'usage_class':'unverified_caller','independent_use_verified':False,
                    '_key':key,'_fingerprint':fingerprint,'_created':time.monotonic()}
        return {'referral':ledger.view(route_id),'handoff':spec,'execution_tool':'execute_route',
                'consent_required':'operator network opt-in AND confirm_public_identifier=true',
                'expires_in_seconds_max':3600}

    def execute(self,route_id,doi,confirm_public_identifier=False):
        if not self.allow_network or confirm_public_identifier is not True:
            raise ValueError('network disabled or explicit public-identifier consent missing')
        ledger=self.ledger
        with ledger.lock:
            event=ledger.view(route_id)
            spec=descriptor(event['provider_id'],doi)
            stored=ledger.events[route_id]
            if stored['_fingerprint']!=ledger.digest(event['provider_id']+'\0'+doi):
                raise ValueError('route input mismatch')
            if stored['status']!='prepared':
                return {'referral':event,'duplicate':True,'result':None}
            stored['status']='executing'
        # Lock is released while networking; retries see executing and cannot dispatch twice.
        result=None
        try:
            data=fetch_json(spec['url'])
            result=normalize(event['provider_id'],doi,data)
            evidence={'kind':'validated_provider_response','sha256':hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()}
            status='succeeded'
        except ProviderFailure as exc:
            status='failed'
            evidence={'kind':'provider_failure','code':exc.code}
        except Exception:
            # Never expose upstream payloads, URLs or exception details in MCP errors.
            status='failed'
            evidence={'kind':'internal_failure','code':'adapter_error'}
        with ledger.lock:
            stored['status']=status
            stored['execution_evidence']=evidence
        return {'referral':ledger.view(route_id),'duplicate':False,'result':result}
