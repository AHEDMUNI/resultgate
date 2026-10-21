"""Opt-in intake and explainable recommendations. No dispatch, payments or URL fetches."""
import hashlib
import json
import re
import secrets
import time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .registry import Submission, atomic, sha


def revision(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


class Application(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,100}$')
    public_metadata_consent: Literal[True]
    service: Submission

    @field_validator('public_metadata_consent', mode='before')
    @classmethod
    def explicit_consent(cls, value):
        if value is not True:
            raise ValueError('explicit boolean consent required')
        return value


class ApplicationId(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    application_id: str = Field(pattern=r'^[a-f0-9]{32}$')


class Recommend(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    need: str = Field(default='', max_length=2000)
    capabilities: list[str] = Field(default_factory=list, max_length=16)
    currency: Literal['USD', 'EUR', 'GBP'] = 'USD'
    unit: Literal['task', 'page', '1000_requests', 'month'] = 'task'
    max_price_micros: int | None = Field(default=None, ge=0, le=10**12)
    limit: int = Field(default=5, ge=1, le=10)

    @field_validator('capabilities')
    @classmethod
    def capabilities_valid(cls, values):
        if any(not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', c) for c in values):
            raise ValueError('explicit capability IDs required')
        return sorted(set(values))


class PriceReview(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    currency: Literal['USD', 'EUR', 'GBP']
    unit: Literal['task', 'page', '1000_requests', 'month']
    price_micros: int = Field(ge=0, le=10**12)
    evidence_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    valid_until: float = Field(allow_inf_nan=False)


# Explicit, deliberately small vocabulary. Text is never sent to a model or stored.
VOCABULARY = {
    'web_scraping': ('scrape', 'scraping', 'استخراج بيانات', 'استخراج البيانات', 'جمع بيانات'),
    'web_search': ('web search', 'search the web', 'بحث الويب', 'بحث على الانترنت'),
    'citation_structuring': ('citation', 'citations', 'استشهاد', 'مراجع علمية'),
    'doi_metadata': ('doi',),
    'result_validation': ('validate', 'validation', 'تدقيق', 'تحقق'),
}


class Marketplace:
    def __init__(self, market):
        self.market = market
        self.registry = market.registry
        self.store, self.db = market.store, market.db
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS provider_applications(
          id TEXT PRIMARY KEY, tenant_hash TEXT NOT NULL, request_hash TEXT NOT NULL,
          spec_hash TEXT NOT NULL, data TEXT NOT NULL, created REAL NOT NULL,
          UNIQUE(tenant_hash, request_hash));
        CREATE TABLE IF NOT EXISTS provider_price_reviews(
          provider_id TEXT PRIMARY KEY, revision TEXT NOT NULL, data TEXT NOT NULL);
        ''')
        self.purge()

    @atomic
    def purge(self):
        self.db.execute('DELETE FROM provider_applications WHERE created<?', (time.time()-30*86400,))
        self.db.execute("DELETE FROM provider_price_reviews WHERE provider_id NOT IN (SELECT id FROM providers)")

    def _actor(self, token):
        actor = self.market._auth(token)
        if actor['role'] != 'requester':
            raise ValueError('invited requester credential required')
        return actor

    @atomic
    def apply(self, token, **kwargs):
        actor = self._actor(token)
        data = Application.model_validate(kwargs).model_dump()
        tenant = actor['tenant_hash']
        spec = data['service']
        digest, request = revision(spec), self.store.digest(data['request_id'])
        self.db.execute('DELETE FROM provider_applications WHERE created<?', (time.time()-30*86400,))
        existing = self.db.execute('SELECT spec_hash,data FROM provider_applications WHERE tenant_hash=? AND request_hash=?', (tenant, request)).fetchone()
        if existing:
            if existing[0] != digest:
                raise ValueError('request ID cannot change the service')
            return {**json.loads(existing[1]), 'duplicate': True}
        count = self.db.execute('SELECT count(*) FROM provider_applications WHERE tenant_hash=?', (tenant,)).fetchone()[0]
        total = self.db.execute('SELECT count(*) FROM provider_applications').fetchone()[0]
        if count >= 5 or total >= 1000:
            raise ValueError('application capacity reached')
        record = {'application_id': secrets.token_hex(16), 'state': 'pending_review',
                  'service': spec, 'provider_id': None, 'execution_enabled': False,
                  'metadata_is_untrusted': True, 'review_evidence_sha256': None}
        self.db.execute('INSERT INTO provider_applications VALUES(?,?,?,?,?,?)',
                        (record['application_id'], tenant, request, digest, json.dumps(record), time.time()))
        return {**record, 'duplicate': False}

    def _application(self, application_id):
        ApplicationId(application_id=application_id)
        row = self.db.execute('SELECT tenant_hash,data FROM provider_applications WHERE id=? AND created>=?', (application_id, time.time()-30*86400)).fetchone()
        if not row:
            raise ValueError('invalid or inaccessible application')
        return row[0], json.loads(row[1])

    def status(self, token, application_id):
        actor = self._actor(token)
        owner, record = self._application(application_id)
        if owner != actor['tenant_hash']:
            raise ValueError('invalid or inaccessible application')
        return record

    def recommend(self, token, **kwargs):
        self._actor(token)
        query = Recommend.model_validate(kwargs)
        needed = query.capabilities or sorted({cap for cap, words in VOCABULARY.items()
                     if any(re.search(r'(?<!\w)' + re.escape(word) + r'(?!\w)', query.need.casefold()) for word in words)})
        result = {'mode': 'advisory_only', 'execution_enabled': False,
                  'interpreted_capabilities': needed, 'interpretation': 'explicit_ids' if query.capabilities else 'limited_bilingual_keyword_rules',
                  'ranking_policy': 'matched capabilities descending, comparable reviewed price ascending, provider ID tie-break; commission never boosts rank',
                  'scope': 'this_operator_reviewed_registry_only', 'recommendations': [],
                  'need_stored': False, 'quality_and_reputation': 'unknown_without_independent_outcomes'}
        if not needed:
            return {**result, 'clarification_required': True, 'reason': 'Specify capability IDs; natural-language intent was not recognized.'}
        ranked = []
        for provider in self.registry.discover():
            matched = sorted(set(needed) & set(provider['capabilities']))
            if not matched:
                continue
            spec = {key: provider[key] for key in Submission.model_fields}
            price = None
            row = self.db.execute('SELECT revision,data FROM provider_price_reviews WHERE provider_id=?', (provider['id'],)).fetchone()
            if row and row[0] == revision(spec):
                candidate = json.loads(row[1])
                if candidate['valid_until'] > time.time() and candidate['currency'] == query.currency and candidate['unit'] == query.unit:
                    price = candidate
            if query.max_price_micros is not None and (price is None or price['price_micros'] > query.max_price_micros):
                continue
            entry = {'provider_id': provider['id'], 'name': provider['name'], 'matched_capabilities': matched,
                     'missing_capabilities': sorted(set(needed)-set(matched)), 'price': price,
                     'price_disclaimer': 'reviewed declaration, not binding quote; tax/overages and task-specific cost unverified',
                     'commercial_relationship': 'agreement_recorded' if provider['commission_agreement_approved'] else 'no_approved_agreement_recorded',
                     'quality': None, 'verified_independent_jobs': None,
                     'reasons': ['Operator reviewed domain ownership; not a quality guarantee', f'{len(matched)} of {len(needed)} capability declarations match'],
                     'warnings': ['Provider metadata remains untrusted', 'No execution or payment authorization granted']}
            ranked.append(((-len(matched), price is None, price['price_micros'] if price else 0, provider['id']), entry))
        result['recommendations'] = [entry for _, entry in sorted(ranked)[:query.limit]]
        return {**result, 'clarification_required': False}


class MarketplaceOperator:
    """Local-only review. Never add these methods to HTTP/MCP tool dispatch."""
    def __init__(self, marketplace):
        self.portal = marketplace
        self.store, self.db = marketplace.store, marketplace.db

    def pending(self):
        return [json.loads(row[0]) for row in self.db.execute(
            'SELECT data FROM provider_applications WHERE created>=? ORDER BY created LIMIT 1000',
            (time.time()-30*86400,)) if json.loads(row[0])['state'] == 'pending_review']

    @atomic
    def decide(self, application_id, evidence_sha256, provider_id=None):
        _, record = self.portal._application(application_id)
        if record['state'] != 'pending_review':
            raise ValueError('already reviewed; submit a new application for changes')
        sha(evidence_sha256)
        if provider_id is not None:
            provider = self.portal.registry.get(provider_id)
            if provider['state'] != 'approved' or provider['submission'] != record['service']:
                raise ValueError('independently approved matching registry provider required')
        record.update(state='approved_listing' if provider_id else 'rejected', provider_id=provider_id,
                      review_evidence_sha256=evidence_sha256)
        self.db.execute('UPDATE provider_applications SET data=? WHERE id=?', (json.dumps(record), application_id))
        return record

    @atomic
    def review_price(self, provider_id, **kwargs):
        data = PriceReview.model_validate(kwargs).model_dump()
        if not time.time() < data['valid_until'] <= time.time() + 7*86400:
            raise ValueError('price review must expire within seven days')
        provider = self.portal.registry.get(provider_id)
        if provider['state'] != 'approved':
            raise ValueError('reviewed provider required')
        self.db.execute('INSERT OR REPLACE INTO provider_price_reviews VALUES(?,?,?)',
                        (provider_id, revision(provider['submission']), json.dumps(data)))
        return data
