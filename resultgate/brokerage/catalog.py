"""Operator-reviewed catalog. Provider websites are evidence, never executable instructions."""
from dataclasses import dataclass, asdict
from datetime import date

@dataclass(frozen=True)
class Entry:
    id: str
    name: str
    capabilities: tuple[str, ...]
    endpoint: str
    transport: str
    authentication: str
    pricing: str
    docs: str
    executable: bool = False
    price_usd: float | None = None
    reviewed: str = '2026-10-20'
    automation: str = 'documented_api_use'
    referral_program: str = 'not_established'
    agreement_id: str | None = None  # Only a future operator-reviewed agreement; never caller supplied.

CATALOG = (
    Entry('crossref', 'Crossref', ('doi_metadata', 'scholarly_metadata'),
          'https://api.crossref.org/works/', 'https_get', 'none_public_pool',
          'public metadata free; rate limited',
          'https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/', True, 0.0),
    Entry('datacite', 'DataCite', ('doi_metadata', 'dataset_metadata'),
          'https://api.datacite.org/dois/', 'https_get', 'none_public_api',
          'public findable DOI metadata free; rate limited',
          'https://support.datacite.org/docs/rest-api', True, 0.0),
    Entry('firecrawl', 'Firecrawl', ('web_search', 'web_extraction'),
          'https://mcp.firecrawl.dev/v2/mcp', 'remote_mcp',
          'keyless tier documented; account/key for expanded use',
          'keyless 1000 credits/month documented; paid tiers exist; entitlement not tested',
          'https://www.firecrawl.dev/blog/firecrawl-keyless-launch',
          referral_program='subscription_affiliate_advertised; machine_referral_eligibility_unverified'),
    Entry('tavily', 'Tavily', ('web_search', 'web_extraction', 'web_research'),
          'https://mcp.tavily.com/mcp/', 'remote_mcp', 'OAuth or API key; keyless search/extract also documented',
          'account free 1000 credits/month; paid usage optional; current entitlement not tested',
          'https://docs.tavily.com/documentation/mcp'),
)

def fresh(entry, today=None):
    age=((today or date.today())-date.fromisoformat(entry.reviewed)).days
    return 0 <= age <= 30

def get_provider(provider_id):
    for entry in CATALOG:
        if entry.id == provider_id:
            return entry
    raise ValueError('provider is not in the reviewed catalog')

def public_entry(entry):
    return {**asdict(entry), 'verification':'documentation_reviewed',
            'review_current':fresh(entry), 'live_availability':'not_guaranteed',
            'commission_available':False, 'resale_permission':'not_established',
            'provider_kind':'service_api_not_autonomous_agent'}

def discover(capability=None):
    if capability is not None and (not isinstance(capability,str) or len(capability)>64):
        raise ValueError('capability must be a short catalog identifier')
    return [public_entry(p) for p in CATALOG if capability is None or capability in p.capabilities]
