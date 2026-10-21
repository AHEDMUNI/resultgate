"""Provider-facing tools. No administrative review, signing keys or execution exposed."""
from .registry import Registry, Submission

def register(server, directory):
    registry=Registry(directory)
    @server.tool()
    def submit_provider(submission: Submission) -> dict:
        """Submit PUBLIC service metadata for operator review. Never supply secrets. Returns private management token once: keep locally, never forward to other agents. Submission grants no trust or execution."""
        return registry.submit(submission.model_dump())
    @server.tool()
    def update_provider(provider_id: str, management_token: str, submission: Submission) -> dict:
        """Replace public metadata. Invalidates ownership review and all agreement acceptance."""
        return registry.update(provider_id,management_token,submission.model_dump())
    @server.tool()
    def suspend_provider(provider_id: str, management_token: str) -> dict:
        """Remove own provider from discovery immediately."""
        return registry.suspend(provider_id,management_token)
    @server.tool()
    def accept_provider_terms(provider_id: str, management_token: str, terms_sha256: str, explicit_acceptance: bool=False) -> dict:
        """Record explicit provider consent to operator-proposed exact terms. Does not grant operator approval or create a payment."""
        return registry.accept_terms(provider_id,management_token,terms_sha256,explicit_acceptance)
    @server.tool()
    def discover_registered_providers(capability: str | None=None) -> dict:
        """List locally reviewed submissions. Metadata untrusted; none automatically executable. Built-in task adapters remain separate."""
        return {'providers':registry.discover(capability),'public_network':False}
    return registry
