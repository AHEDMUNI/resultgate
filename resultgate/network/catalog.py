"""Offline, declarative capability catalog. Not an A2A AgentCard or executable plan."""
import argparse
from copy import deepcopy
import json
import re

_CAPABILITIES = [
    {'id': 'provider_discovery', 'tools': ['discover_providers', 'discover_agents', 'match_task'],
     'mode': 'brokerage_delegation', 'purpose': 'Find reviewed providers for supported capabilities.',
     'external_execution': False},
    {'id': 'doi_metadata', 'tools': ['route_task', 'execute_route', 'track_referral'],
     'mode': 'brokerage', 'purpose': 'Retrieve metadata for an explicitly authorized public DOI.',
     'external_execution': True, 'required_operator_flag': '--allow-public-provider-requests',
     'per_call_consent': 'confirm_public_identifier', 'provider_kind': 'data_api'},
    {'id': 'citation_structuring', 'tools': ['prepare_delegation', 'execute_delegation', 'delegation_status'],
     'mode': 'brokerage_delegation', 'purpose': 'Structure a public citation using the reviewed GROBID demo.',
     'external_execution': True, 'required_operator_flag': '--allow-demo-task-requests',
     'per_call_consent': 'consent_to_send_public_citation', 'provider_kind': 'specialist_ml_demo',
     'verification_scope': 'predeclared surname and year, not full semantic correctness'},
    {'id': 'result_validation', 'tools': ['check_extraction', 'check_citations'],
     'mode': 'default', 'purpose': 'Check supplied extraction contracts and literal citation integrity.',
     'external_execution': False, 'verification_scope': 'caller-supplied evidence only'},
    {'id': 'provider_submission', 'tools': ['submit_provider', 'update_provider', 'suspend_provider', 'discover_registered_providers'],
     'mode': 'local_registry', 'purpose': 'Submit public service metadata for separate ownership and operator review.',
     'external_execution': False, 'automatic_approval': False, 'submitted_provider_execution': False},
]


def catalog(required_capabilities=None):
    """Filter by explicit capability IDs; never send task text or run returned commands.

    Multiple IDs request all corresponding service entries, not a claim that one provider
    can perform them together. Unknown IDs are returned explicitly and never substituted.
    """
    required = [] if required_capabilities is None else required_capabilities
    if (not isinstance(required, list) or len(required) > 16
            or any(not isinstance(c, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', c) for c in required)):
        raise ValueError('at most 16 explicit capability identifiers required')
    requested = set(required)
    known = {c['id'] for c in _CAPABILITIES}
    entries = [deepcopy(c) for c in _CAPABILITIES if not requested or c['id'] in requested]
    return {
        'format': 'resultgate-capability-catalog-v1',
        'standard': False, 'a2a_supported': False,
        'server_name': 'io.github.AHEDMUNI/resultgate',
        'published_package': {'name': 'resultgate-pilot', 'version': '0.3.0'},
        'registry_record': 'https://registry.modelcontextprotocol.io/v0.1/servers/io.github.AHEDMUNI%2Fresultgate/versions/0.3.0',
        'transport': 'mcp_stdio', 'public_execution_endpoint': None,
        'capabilities': entries, 'unsupported_capabilities': sorted(requested-known),
        'all_requested_supported': not bool(requested-known),
        'safe_mcp_configuration': {'command': 'uvx', 'args': ['resultgate-pilot==0.3.0', '--brokerage', '--delegation']},
        'default_tool_count': 2, 'safe_configuration_tool_count': 12, 'local_registry_tool_count': 17,
        'external_execution_enabled_by_configuration': False,
        'operator_installation_approval_required': True,
        'provider_application': 'https://github.com/AHEDMUNI/resultgate/issues/new/choose',
        'payments_enabled': False, 'commission_earned_from_discovery': False,
        'catalog_scope': 'published_local_features_not_global_provider_search',
        'ranking': 'none', 'telemetry': 'none',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capability', action='append', default=[], help='Exact capability ID; repeat for several')
    args = parser.parse_args()
    try:
        result = catalog(args.capability)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
