import unittest
from scripts.broker_value_benchmark import benchmark, cost_fixture

class ValueBenchmarkTests(unittest.TestCase):
    def test_baselines_reject_wrong_output_and_do_not_repeat(self):
        result = benchmark(1)
        self.assertEqual(result['external_tasks_created'], 0)
        self.assertFalse(result['discovery_time_measured'])
        for row in result['rows']:
            direct, broker = row['direct_competent'], row['resultgate']
            for client in (direct, broker):
                self.assertEqual(client['create_attempts'], 1)
                self.assertEqual(client['restart_added_requests'], 0)
                self.assertEqual(client['verified'], row['scenario'] in ('success','cleanup_failure'))
                self.assertEqual(client['cleanup_confirmed'], row['scenario'] not in ('ambiguous_create','cleanup_failure'))
            self.assertEqual(direct['simulated_transport_calls'], broker['simulated_transport_calls'])
    def test_cost_fixture_has_no_unagreed_real_commission(self):
        result=cost_fixture()
        self.assertEqual(result['mode'],'hypothetical_USD')
        self.assertEqual(result['real_money_spent_by_benchmark'],'0')
        self.assertEqual(result['broker_customer_total_same_retail_price'],'1.00')
    def test_bounded_sample_count(self):
        for value in (0,101,True):
            with self.assertRaises(ValueError):benchmark(value)
