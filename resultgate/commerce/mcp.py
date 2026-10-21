"""Authenticated opt-in stdio tools for marketplace sandbox; no operator tools."""
import argparse
import os
from mcp.server.fastmcp import FastMCP
from ..network.registry import Registry
from ..network.market import Market
from .core import Commerce, TERMS, TERMS_SHA


def build(commerce, token, stripe=None):
    commerce.actor(token)
    server=FastMCP('ResultGate marketplace sandbox',instructions=
        'General service marketplace. Fixed 5% on confirmed eligible payment, adjusted for refunds/disputes. '
        'TEST ONLY. No service completion gate. No real revenue. Owner approval is outside agent tools.')
    def quota(): commerce.market.consume_request(token)

    @server.tool()
    def provider_terms() -> dict:
        """Read versioned 5% sandbox terms; no joining/subscription or requester recommendation fees."""
        quota(); return {'terms':TERMS,'sha256':TERMS_SHA,'mode':'test'}

    @server.tool()
    def apply_as_provider(name: str, terms_sha256: str, authorized_signatory: bool=False) -> dict:
        """Record invited tenant's sandbox application and acceptance. Operator must verify authority/ownership."""
        quota(); return commerce.apply(token,name,terms_sha256,authorized_signatory)

    @server.tool()
    def publish_test_service(provider_id: str, service_id: str, title: str, capability: str, price_cents: int) -> dict:
        """Publish an immutable test service only for an approved provider owned by this tenant."""
        quota(); return commerce.list_service(token,provider_id,service_id,title,capability,price_cents)

    @server.tool()
    def search_services(capability: str | None=None) -> dict:
        """Compare reviewed services by exact capability and price. No commission-based ranking or fabricated ratings."""
        quota(); return commerce.search(token,capability)

    @server.tool()
    def create_purchase_order(service_id: str, request_key: str) -> dict:
        """Create a deduplicated test order with frozen price, provider and terms; requires owner approval before Checkout."""
        quota(); return commerce.order(token,service_id,request_key)

    @server.tool()
    def get_purchase_order(order_id: str) -> dict:
        """Read only orders accessible to this tenant. Payment success is not proof of service quality."""
        quota(); return commerce.get(token,order_id)

    @server.tool()
    def create_test_checkout(order_id: str) -> dict:
        """Create Stripe TEST Checkout only after trusted owner approval. Never accepts live keys or charges real money."""
        quota()
        if stripe is None: return {'blocked':'Stripe sandbox not configured','live_enabled':False}
        return stripe.checkout(commerce,token,order_id)

    @server.tool()
    def provider_dashboard() -> dict:
        """Read this provider's test orders and adjusted 5% commission; real revenue is always zero."""
        quota(); return commerce.dashboard(token)
    return server


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--directory',required=True)
    a=p.parse_args()
    # Existing operator-initialized identity store; tokens are environment-only.
    c=Commerce(Market(Registry(a.directory)))
    build(c,os.environ.get('RESULTGATE_REQUESTER_TOKEN','')).run(transport='stdio')


if __name__=='__main__': main()
