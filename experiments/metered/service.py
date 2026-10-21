"""Bounded, in-memory shadow billing. NOT a production billing ledger."""
import hmac
import json
import re
import secrets
import threading
from collections import Counter
from resultgate.extraction import audit_extraction, MAX_BYTES
from resultgate.citations import audit_citations
from resultgate.models import ExtractionInput, CitationInput

class Rejected(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

class ShadowService:
    # No caller can set the cohort or credit balance through API/MCP.
    def __init__(self, token, credits=100):
        if not isinstance(token, str) or len(token) < 32:
            raise ValueError('Use a random token of at least 32 characters')
        if type(credits) is not int or not 0 <= credits <= 10000:
            raise ValueError('credits must be an integer in 0..10000')
        self._token = token.encode()
        self._secret = secrets.token_bytes(32)
        self._lock = threading.Lock()
        self._events = {}
        self.credits = credits

    def authorize(self, token):
        if not isinstance(token, str) or not hmac.compare_digest(token.encode(), self._token):
            raise Rejected(401, 'authentication required')

    def call(self, token, tool, payload, request_id):
        self.authorize(token)
        if tool not in ('extraction', 'citations'):
            raise Rejected(404, 'unknown tool')
        if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', request_id):
            raise Rejected(422, 'request_id must be an opaque identifier, 1..128 characters')
        try:
            raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            if len(raw) > MAX_BYTES:
                raise Rejected(413, 'payload exceeds 1 MiB')
            model = ExtractionInput if tool == 'extraction' else CitationInput
            model.model_validate(payload)
        except Rejected:
            raise
        except (ValueError, TypeError, RecursionError):
            raise Rejected(422, 'invalid input') from None
        key = hmac.digest(self._secret, request_id.encode(), 'sha256')
        fingerprint = hmac.digest(self._secret, tool.encode() + b'\0' + raw, 'sha256')
        with self._lock:
            old = self._events.get(key)
            if old is not None and old[0] != fingerprint:
                raise Rejected(409, 'request_id was used for a different operation')
            if old is None and self.credits == 0:
                raise Rejected(429, 'trial credits exhausted; real payments are disabled')
            # Run before committing a unit; invalid inputs and execution errors consume none.
            try:
                result = (audit_extraction if tool == 'extraction' else audit_citations)(payload)
            except (ValueError, TypeError, RecursionError):
                raise Rejected(422, 'invalid input') from None
            if old is None:
                self._events[key] = (fingerprint, tool, result['status'])
                self.credits -= 1
            return {'result': result, 'billing': {'mode': 'shadow_only',
                'unit_price_usd_micros': 1000, 'units_this_request': int(old is None),
                'duplicate': old is not None, 'remaining_trial_units': self.credits,
                'money_collected_usd_micros': 0}}

    def summary(self):
        with self._lock:
            return {'mode': 'shadow_only', 'cohort': 'internal',
                'completed_unique_operations': len(self._events),
                'outcomes': dict(Counter(event[2] for event in self._events.values())),
                'hypothetical_usd_micros': len(self._events) * 1000,
                'money_collected_usd_micros': 0, 'verified_external_uses': 0}
