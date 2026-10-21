"""Offline A/B: competent direct client vs actual ResultGate Trial, simulated I/O only.
Run as `python -m scripts.broker_value_benchmark`. No key, network or provider task.
"""
import argparse
from decimal import Decimal
import json
import sqlite3
import statistics
import tempfile
import time
from unittest.mock import patch

from resultgate.delegation.browser_use_trial import (
    Trial, TrialError, PageFacts, stop_session_browsers, TASK, SCHEMA,
)

RID = '11111111-1111-4111-8111-111111111111'
SID = '22222222-2222-4222-8222-222222222222'
BID = '33333333-3333-4333-8333-333333333333'
HTML = '<html><h1>Public fixture</h1><p>Test text.</p></html>'
FACTS = {'title': '', 'heading': 'Public fixture', 'documentation_example': False}
SCENARIOS = ('success', 'wrong_output', 'provider_failure', 'ambiguous_create', 'cleanup_failure')


class SimulatedProvider:
    """Bounded deterministic responses; unknown requests fail rather than reach a network."""
    def __init__(self, scenario):
        if scenario not in SCENARIOS:
            raise ValueError('unknown scenario')
        self.scenario = scenario
        self.calls = []

    def request(self, method, path, payload=None, *, page=False):
        self.calls.append((method, path))
        if page and method == 'GET' and path == '/html':
            return HTML
        if method == 'GET' and path == '/api/v2/billing/account':
            return {'isFreeTier': True, 'totalCreditsBalanceUsd': 1, 'activeSessionCount': 0}
        if method == 'POST' and path == '/api/v4/runs':
            if self.scenario == 'ambiguous_create':
                raise TrialError('transport_failed')
            return {'id': RID, 'sessionId': SID}
        state = 'failed' if self.scenario == 'provider_failure' else 'completed'
        if method == 'GET' and path == '/api/v4/runs/' + RID + '/status':
            return {'status': state}
        if method == 'GET' and path == '/api/v4/runs/' + RID:
            facts = dict(FACTS)
            if self.scenario == 'wrong_output':
                facts['heading'] = 'invented heading'
            return {'id': RID, 'sessionId': SID, 'status': state, 'output': facts, 'totalCostUsd': '0.004661'}
        if method == 'GET' and path == '/api/v4/browsers?agentSessionId=' + SID + '&pageSize=100':
            return {'items': [{'id': BID, 'agentSessionId': SID, 'status': 'active'}], 'totalItems': 1}
        if path == '/api/v4/browsers/' + BID and method in {'GET', 'PATCH'}:
            if self.scenario == 'cleanup_failure':
                raise TrialError('transport_failed')
            return {'id': BID, 'agentSessionId': SID, 'status': 'stopped'}
        if method == 'GET' and path == '/api/v4/sessions/' + SID + '/cost':
            return {'sessionId': SID, 'totalCostUsd': '0.005671'}
        raise AssertionError('unexpected simulated request')


class CompetentDirectClient:
    """A narrow bespoke direct integration with durable no-retry and verification.

    Shares the HTML parser and ownership-safe cleanup helper for equivalent policy;
    it does not call Trial. This is an illustrative baseline, not a production SDK.
    """
    def __init__(self, directory, transport):
        self.transport = transport
        self.db = sqlite3.connect(directory + '/direct.sqlite3', isolation_level=None)
        self.db.execute('CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY CHECK(id=1), record TEXT)')

    def run(self):
        old = self.db.execute('SELECT record FROM journal WHERE id=1').fetchone()
        if old:
            return json.loads(old[0])
        credit = self.transport.request('GET', '/api/v2/billing/account')
        if credit['isFreeTier'] is not True or credit['activeSessionCount'] != 0 or Decimal(str(credit['totalCreditsBalanceUsd'])) < Decimal('0.50'):
            raise TrialError('preflight_blocked')
        parser = PageFacts()
        parser.feed(self.transport.request('GET', '/html', page=True))
        expected = parser.facts()
        result = {'verified': False, 'browser_stopped': False}
        try:
            self.db.execute('INSERT INTO journal VALUES(1,?)', (json.dumps(result),))
        except sqlite3.IntegrityError:
            return json.loads(self.db.execute('SELECT record FROM journal WHERE id=1').fetchone()[0])
        try:
            created = self.transport.request('POST', '/api/v4/runs', {
                'task': TASK, 'model': 'gpt-5.6-luna', 'maxCostUsd': '0.10',
                'browserSettings': {'profileId': None, 'proxyCountryCode': None, 'record': False, 'extensionIds': []},
                'agentmail': False, 'keepAlive': 120, 'outputSchema': SCHEMA})
        except TrialError:
            return result  # Reserved slot stays consumed; manual reconciliation required.
        rid, sid = created['id'], created['sessionId']
        state = self.transport.request('GET', '/api/v4/runs/' + rid + '/status')['status']
        if state == 'completed':
            answer = self.transport.request('GET', '/api/v4/runs/' + rid)
            output = answer.get('output')
            result['verified'] = (answer.get('id') == rid and answer.get('sessionId') == sid
                                  and answer.get('status') == 'completed'
                                  and isinstance(output, dict) and set(output) == set(expected)
                                  and all(type(output[k]) is type(v) and output[k] == v for k, v in expected.items()))
        try:
            result['browser_stopped'] = stop_session_browsers(self.transport, sid)
        except TrialError:
            pass
        cost = self.transport.request('GET', '/api/v4/sessions/' + sid + '/cost')
        if cost['sessionId'] != sid:
            raise TrialError('cost_binding_failed')
        self.db.execute('UPDATE journal SET record=? WHERE id=1', (json.dumps(result),))
        return result


def sample(kind, scenario):
    provider = SimulatedProvider(scenario)
    cls = CompetentDirectClient if kind == 'direct_competent' else Trial
    with tempfile.TemporaryDirectory() as directory:
        started = time.perf_counter_ns()
        client = cls(directory, provider)
        try:
            result = client.run() if kind == 'direct_competent' else client.run(consent=True, free_no_card_no_recharge_confirmed=True)
        finally:
            client.db.close()
        elapsed_ms = (time.perf_counter_ns() - started) / 1e6
        count = len(provider.calls)
        restarted = cls(directory, provider)
        try:
            restarted.run()  # An existing journal needs no new consent and must issue no requests.
        finally:
            restarted.db.close()
    return {'local_elapsed_ms': elapsed_ms, 'simulated_transport_calls': count,
            'create_attempts': sum(m == 'POST' and p == '/api/v4/runs' for m, p in provider.calls),
            'restart_added_requests': len(provider.calls) - count,
            'verified': result['verified'], 'cleanup_confirmed': result['browser_stopped']}


def cost_fixture():
    """Hypothetical $1 retail task; 10% revenue share is NOT any accepted agreement."""
    return {'mode': 'hypothetical_USD', 'direct_customer_total': '1.00',
            'broker_customer_total_same_retail_price': '1.00',
            'provider_paid_commission': '0.10', 'provider_net_before_own_costs': '0.90',
            'broker_gross_before_hosting_tax_settlement_fees': '0.10',
            'if_provider_passes_commission_on_customer_total': '1.10',
            'historical_single_internal_trial_usage_not_a_quote': '0.005671',
            'hosting_payment_tax_fx_costs': 'unmeasured; excluded, not zero',
            'real_money_spent_by_benchmark': '0'}


def benchmark(samples=15):
    if type(samples) is not int or not 1 <= samples <= 100:
        raise ValueError('samples must be 1..100')
    rows = []
    # Defence in depth: accidental socket/DNS use fails the offline benchmark.
    with patch('socket.create_connection', side_effect=AssertionError('network forbidden')), patch('socket.getaddrinfo', side_effect=AssertionError('network forbidden')):
        for scenario in SCENARIOS:
            row = {'scenario': scenario}
            for kind in ('direct_competent', 'resultgate'):
                measurements = [sample(kind, scenario) for _ in range(samples)]
                final = dict(measurements[-1])
                final['local_elapsed_ms'] = round(statistics.median(m['local_elapsed_ms'] for m in measurements), 3)
                row[kind] = final
            rows.append(row)
    return {'mode': 'internal_offline_simulation', 'samples_per_case': samples,
            'discovery_time_measured': False, 'provider_already_known_in_both_cases': True,
            'network_latency_measured': False, 'external_tasks_created': 0,
            'rows': rows, 'cost_fixture': cost_fixture(),
            'conclusion': 'No reliability or request-count advantage over this competent direct baseline on these fixtures. Local timing is wrapper/database overhead, not agent latency. ResultGate reuses safety code; engineering effort and unknown-provider discovery benefit are not measured.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=15)
    args = parser.parse_args()
    print(json.dumps(benchmark(args.samples), indent=2))


if __name__ == '__main__':
    main()
