import unittest
from resultgate.metrics import summarize


def event(**changes):
    data = dict(event_id="e1", client_id="external", task_id="t1",
                timestamp="2026-10-20T00:00:00Z", completed=True,
                environment="production", origin="real_task")
    data.update(changes)
    return data


class MetricsTests(unittest.TestCase):
    def test_empty_is_zero(self):
        result = summarize([], set())
        self.assertEqual(result["qualified_uses"], 0)
        self.assertEqual(result["recorded_revenue_usd"], 0)
        self.assertEqual(result["uses_remaining"], 100)

    def test_unverified_claim_is_not_verification(self):
        result = summarize([event(verified=True, revenue_usd=500)], set())
        self.assertEqual(result["unverified_candidate_uses"], 1)
        self.assertEqual(result["qualified_uses"], 0)
        self.assertEqual(result["recorded_revenue_usd"], 0)

    def test_exclude_non_real_and_internal(self):
        values = [event(origin=o) for o in ("retry", "demo", "healthcheck")]
        values += [event(environment=e) for e in ("test", "internal")]
        values += [event(completed=False)]
        result = summarize(values, {"external"})
        self.assertEqual(result["excluded_events"], 6)
        self.assertEqual(result["qualified_uses"], 0)

    def test_dedupe_event_and_task(self):
        result = summarize([event(), event(task_id="t2"), event(event_id="e2")], {"external"})
        self.assertEqual(result["qualified_uses"], 1)
        self.assertEqual(result["duplicate_events"], 2)

    def test_returning_clients_utc_dates(self):
        values = [event(timestamp="2026-10-20T23:30:00-02:00"),
                  event(event_id="e2", task_id="t2", timestamp="2026-10-21T04:00:00Z")]
        self.assertEqual(summarize(values, {"external"})["returning_verified_clients"], 0)
        values.append(event(event_id="e3", task_id="t3", timestamp="2026-10-22T00:00:00Z"))
        result = summarize(values, {"external"})
        self.assertEqual(result["returning_verified_clients"], 1)
        self.assertEqual(result["distinct_verified_clients"], 1)

    def test_money_only_qualified_and_valid(self):
        values = [event(revenue_usd=0.3, cost_usd=0.1),
                  event(event_id="e2", task_id="t2", revenue_usd=float("nan"), cost_usd=-3),
                  event(event_id="e3", task_id="t3", revenue_usd=True, cost_usd=float("inf")),
                  event(client_id="unknown", event_id="e4", revenue_usd=100)]
        result = summarize(values, {"external"})
        self.assertEqual(result["recorded_net_usd"], 0.2)
        self.assertEqual(result["invalid_financial_values"], 4)
        self.assertEqual(result["qualified_uses"], 3)

    def test_malformed_and_timezone_required(self):
        result = summarize([None, {}, event(timestamp="2026-10-20"), event(completed=1)], {"external"})
        self.assertEqual(result["invalid_events"], 4)
        self.assertEqual(result["qualified_uses"], 0)

    def test_unverified_cannot_poison_verified_event_id(self):
        result = summarize([event(client_id="spoof"), event()], {"external"})
        self.assertEqual(result["qualified_uses"], 1)
        self.assertEqual(result["unverified_candidate_uses"], 1)

    def test_invalid_container(self):
        with self.assertRaises(ValueError):
            summarize({}, set())


if __name__ == "__main__":
    unittest.main()
