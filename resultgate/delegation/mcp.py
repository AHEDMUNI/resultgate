"""Additional tools; administrative attestations and commission writes stay off MCP."""
from typing import Any
from .engine import Delegator
from .providers import PROVIDERS, CitationTask

def register(server,directory=None,allow_network=False,internal=False):
    engine=Delegator(directory,allow_network,internal)
    @server.tool()
    def discover_agents(required_capabilities: list[str]) -> dict[str,Any]:
        """Discover reviewed task processors. Reports service vs provider-declared agent honestly. No network calls."""
        if not 1<=len(required_capabilities)<=4: raise ValueError('1..4 capabilities required')
        return {'providers':[p for p in PROVIDERS if set(required_capabilities)<=set(p['capabilities'])],
                'automatic_provider_onboarding':False}
    @server.tool()
    def prepare_delegation(task: CitationTask, request_id: str) -> dict[str,Any]:
        """Prepare citation structuring with fixed predeclared surname/year criteria. Nothing sent. Store hashes only. Reuse request ID after uncertainty; no automatic retry."""
        return engine.plan(task.model_dump(),request_id)
    @server.tool()
    def execute_delegation(task_id: str, task: CitationTask, consent_to_send_public_citation: bool=False) -> dict[str,Any]:
        """Explicitly send the citation only to GROBID's free DEMO. Do not supply secrets/private content. Requires operator flag. Not a standalone AI agent; output is untrusted. No commissions from API success."""
        return engine.execute(task_id,task.model_dump(),consent_to_send_public_citation)
    @server.tool()
    def delegation_status(task_id: str) -> dict[str,Any]:
        """Read durable state when enabled. Outcome-unknown requires reconciliation, never blind retry."""
        return engine.status(task_id)
    @server.tool()
    def cancel_delegation(task_id: str) -> dict[str,Any]:
        """Cancel locally and block eligibility. Remote processing cannot be stopped on this synchronous provider."""
        return engine.block(task_id,'cancelled')
    return engine
