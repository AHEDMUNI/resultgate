"""Provider submissions are untrusted. Local operator review is a separate boundary."""
from functools import wraps
import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import time
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator
from resultgate.delegation.store import Store

class Submission(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    capabilities: list[str] = Field(min_length=1, max_length=20)
    protocol: str = Field(pattern=r'^(mcp|a2a|api)$')
    endpoint: str = Field(max_length=500)
    auth: str = Field(pattern=r'^(none|api_key|oauth)$')
    requirements: str = Field(max_length=1000)
    pricing: str = Field(min_length=1, max_length=500)
    limits: str = Field(min_length=1, max_length=500)

    @field_validator('capabilities')
    @classmethod
    def bounded_capabilities(cls, values):
        if any(not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', v) for v in values):
            raise ValueError('use capability identifiers')
        return sorted(set(values))

    @field_validator('endpoint')
    @classmethod
    def public_endpoint(cls, value):
        u = urlsplit(value)
        host = u.hostname or ''
        if (u.scheme != 'https' or u.username or u.password or u.query or u.fragment
                or u.port not in (None, 443) or '%' in value or '\\' in value
                or any(ord(c) <= 32 for c in value)
                or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', host)
                or '.' not in host or host.endswith(('.local', '.localhost', '.internal', '.test', '.invalid'))):
            raise ValueError('public HTTPS domain, port 443, no credentials/query/fragment required')
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if all(p.isdigit() for p in host.split('.')):
                raise ValueError('numeric hosts refused')
        else:
            raise ValueError('literal IP refused')
        return value


def sha(value):
    if not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError('reviewed evidence SHA256 required')
    return value

def atomic(fn):
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        with self.store.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                result = fn(self, *args, **kwargs)
                self.db.execute('COMMIT')
                return result
            except Exception:
                self.db.execute('ROLLBACK')
                raise
    return wrapped

class Registry:
    def __init__(self, directory=None):
        self.store = Store(directory)
        self.db = self.store.db
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS providers(id TEXT PRIMARY KEY, owner_hash TEXT, data TEXT, updated REAL);
        CREATE TABLE IF NOT EXISTS network_audit(id TEXT, action TEXT, at REAL);
        ''')
        self.purge()

    def purge(self):
        with self.store.lock:
            cutoff = time.time() - 30 * 86400
            self.db.execute('DELETE FROM providers WHERE updated<?', (cutoff,))
            self.db.execute('DELETE FROM network_audit WHERE at<?', (cutoff,))

    def get(self, pid):
        self.purge()
        row = self.db.execute('SELECT data FROM providers WHERE id=?', (pid,)).fetchone()
        if not row:
            raise ValueError('unknown or expired provider')
        return json.loads(row[0])

    def save(self, p, action):
        self.db.execute('UPDATE providers SET data=?,updated=? WHERE id=?',
                        (json.dumps(p), time.time(), p['id']))
        self.db.execute('INSERT INTO network_audit VALUES(?,?,?)', (p['id'], action, time.time()))

    def authorize(self, pid, token):
        row = self.db.execute('SELECT owner_hash FROM providers WHERE id=?', (pid,)).fetchone()
        if not row or not hmac.compare_digest(row[0], self.store.digest(token)):
            raise ValueError('invalid management credential')

    @atomic
    def submit(self, data):
        spec = Submission.model_validate(data).model_dump()
        with self.store.lock:
            self.purge()
            if self.db.execute('SELECT count(*) FROM providers').fetchone()[0] >= 1000:
                raise ValueError('registry capacity reached')
            pid, token, challenge = secrets.token_hex(16), secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            p = dict(id=pid, submission=spec, state='pending', challenge=challenge,
                     challenge_expires=time.time()+86400, ownership=None, agreement=None,
                     executable=False, untrusted_metadata=True)
            self.db.execute('INSERT INTO providers VALUES(?,?,?,?)',
                            (pid, self.store.digest(token), json.dumps(p), time.time()))
            self.save(p, 'submitted')
            return {'provider': p, 'management_token': token,
                    'ownership_location': f"https://{urlsplit(spec['endpoint']).hostname}/.well-known/resultgate-provider.txt"}

    @atomic
    def update(self, pid, token, data):
        spec = Submission.model_validate(data).model_dump()
        with self.store.lock:
            self.authorize(pid, token)
            p = self.get(pid)
            p.update(submission=spec, state='pending', ownership=None, agreement=None,
                     challenge=secrets.token_urlsafe(32), challenge_expires=time.time()+86400)
            self.save(p, 'resubmitted')
            return p

    @atomic
    def suspend(self, pid, token):
        with self.store.lock:
            self.authorize(pid, token)
            p = self.get(pid); p['state'] = 'suspended'
            self.save(p, 'owner_suspended')
            return p

    @atomic
    def propose_terms(self, pid, terms, kind, rule, amount):
        """LOCAL OPERATOR ONLY: immutable proposal content is hashed; no legal execution."""
        if not isinstance(terms, str) or not 20 <= len(terms) <= 5000:
            raise ValueError('specific written terms required')
        if kind not in {'task','subscription','transaction'} or rule not in {'fixed','basis_points'}:
            raise ValueError('outcome and commission rule required')
        if type(amount) is not int or not 0 < amount <= (10000 if rule == 'basis_points' else 10**12):
            raise ValueError('bounded commission amount required')
        canonical = json.dumps(dict(terms=terms,kind=kind,rule=rule,amount=amount,currency='USD'),sort_keys=True)
        with self.store.lock:
            p = self.get(pid)
            p['agreement'] = {'terms': terms, 'sha256': hashlib.sha256(canonical.encode()).hexdigest(),
                              'kind':kind, 'rule':rule, 'amount':amount, 'currency':'USD',
                              'provider_accepted': False, 'operator_approved': False}
            self.save(p, 'terms_proposed')
            return p['agreement']

    @atomic
    def accept_terms(self, pid, token, terms_sha256, explicit_acceptance=False):
        with self.store.lock:
            self.authorize(pid, token)
            p = self.get(pid); a = p['agreement']
            if explicit_acceptance is not True or not a or a['sha256'] != terms_sha256:
                raise ValueError('explicit acceptance of exact proposed terms required')
            a['provider_accepted'] = True
            self.save(p, 'provider_terms_accepted')
            return a

    @atomic
    def review(self, pid, observed_challenge, evidence_sha256, approve=False):
        """LOCAL OPERATOR ONLY. Independently inspect exact domain challenge and service/terms.
        No URL is fetched here; supplied observations are privileged attestations, not crypto identity.
        """
        with self.store.lock:
            p = self.get(pid)
            if not approve:
                p['state'] = 'rejected'; p['ownership'] = None
            else:
                if time.time() > p['challenge_expires'] or not hmac.compare_digest(p['challenge'], observed_challenge):
                    raise ValueError('ownership challenge missing, wrong or expired')
                p['ownership'] = {'kind': 'operator_reviewed_domain_challenge', 'evidence_sha256': sha(evidence_sha256)}
                p['state'] = 'approved'
            self.save(p, 'operator_reviewed')
            return p

    @atomic
    def approve_agreement(self, pid, evidence_sha256):
        """LOCAL OPERATOR ONLY. No payment; provider consent alone never approves terms."""
        with self.store.lock:
            p = self.get(pid); a = p['agreement']
            if p['state'] != 'approved' or not a or not a['provider_accepted']:
                raise ValueError('reviewed provider and explicit agreement acceptance required')
            a.update(operator_approved=True, evidence_sha256=sha(evidence_sha256))
            self.save(p, 'operator_agreement_reviewed')
            return a

    def discover(self, capability=None):
        self.purge()
        records = [json.loads(r[0]) for r in self.db.execute('SELECT data FROM providers')]
        return [{'id': p['id'], **p['submission'], 'ownership': p['ownership'],
                 'executable': False, 'untrusted_metadata': True,
                 'commission_agreement_approved': bool(p['agreement'] and p['agreement']['operator_approved'])}
                for p in records if p['state'] == 'approved'
                and (capability is None or capability in p['submission']['capabilities'])]

    @atomic
    def delete(self, pid, token):
        with self.store.lock:
            self.authorize(pid, token)
            self.db.execute('DELETE FROM providers WHERE id=?', (pid,))
            self.db.execute('DELETE FROM network_audit WHERE id=?', (pid,))
