"""Offline, conservative usage accounting. Client IDs do not prove independence.

Operator-maintained verified clients must be grounded in evidence outside this
file. This module is neither an authentication service nor a traffic collector.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def summarize(events, verified_external_clients: set) -> dict:
    """Summarize recorded events; never infer verified users from identifiers."""
    if not isinstance(events, list):
        raise ValueError("events must be a JSON list")
    if not isinstance(verified_external_clients, set) or any(
        not isinstance(c, str) or not c.strip() for c in verified_external_clients
    ):
        raise ValueError("verified clients must be a set of nonempty strings")
    result = {
        "qualified_uses": 0, "goal_uses": 100, "uses_remaining": 100,
        "distinct_verified_clients": 0, "returning_verified_clients": 0,
        "unverified_candidate_uses": 0, "excluded_events": 0,
        "duplicate_events": 0, "invalid_events": 0,
        "invalid_financial_values": 0,
        "recorded_revenue_usd": 0.0, "recorded_cost_usd": 0.0,
        "recorded_net_usd": 0.0,
        "measurement_basis": "Operator-verified external clients; IDs alone are not proof. Recorded amounts are not reconciled payments or full operating profit.",
    }
    seen_ids, seen_tasks, dates = set(), set(), {}
    revenue, cost = Decimal(0), Decimal(0)
    for event in events:
        try:
            if not isinstance(event, dict):
                raise ValueError()
            for key in ("event_id", "client_id", "task_id", "timestamp"):
                if not isinstance(event.get(key), str) or not event[key].strip():
                    raise ValueError()
            if type(event.get("completed")) is not bool:
                raise ValueError()
            if event.get("environment") not in ("production", "test", "internal"):
                raise ValueError()
            if event.get("origin") not in ("real_task", "healthcheck", "demo", "retry"):
                raise ValueError()
            moment = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            if moment.tzinfo is None or moment.utcoffset() is None:
                raise ValueError()
            day = moment.astimezone(timezone.utc).date()
        except (ValueError, TypeError, OverflowError):
            result["invalid_events"] += 1
            continue
        if not (event["completed"] and event["environment"] == "production"
                and event["origin"] == "real_task"):
            result["excluded_events"] += 1
            continue
        pair = (event["client_id"], event["task_id"])
        # Keep unverified IDs from suppressing independently verified records.
        scope = event["client_id"] in verified_external_clients
        identity = (scope, event["event_id"])
        if identity in seen_ids or pair in seen_tasks:
            result["duplicate_events"] += 1
            continue
        seen_ids.add(identity)
        seen_tasks.add(pair)
        if not scope:
            result["unverified_candidate_uses"] += 1
            continue
        result["qualified_uses"] += 1
        dates.setdefault(event["client_id"], set()).add(day)
        for key in ("revenue_usd", "cost_usd"):
            value = event.get(key, 0)
            if type(value) not in (int, float) or value < 0:
                result["invalid_financial_values"] += 1
                continue
            try:
                if not math.isfinite(value):
                    raise ValueError()
                amount = Decimal(str(value))
            except (ValueError, OverflowError):
                result["invalid_financial_values"] += 1
                continue
            if key == "revenue_usd":
                revenue += amount
            else:
                cost += amount
    result["uses_remaining"] = max(0, 100 - result["qualified_uses"])
    result["distinct_verified_clients"] = len(dates)
    result["returning_verified_clients"] = sum(len(days) >= 2 for days in dates.values())
    for key, amount in (("recorded_revenue_usd", revenue), ("recorded_cost_usd", cost),
                        ("recorded_net_usd", revenue - cost)):
        # Preserve JSON validity even for unrealistic sums beyond float range.
        result[key] = float(amount) if abs(amount) <= Decimal("1.7976931348623157e308") else str(amount)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="JSON list of recorded events")
    parser.add_argument("verified_clients", type=Path, help="Operator-maintained JSON list; not evidence by itself")
    args = parser.parse_args()
    try:
        clients = json.loads(args.verified_clients.read_text())
        if not isinstance(clients, list) or any(not isinstance(c, str) or not c.strip() for c in clients):
            raise ValueError("verified clients must be a list of nonempty strings")
        output = summarize(json.loads(args.events.read_text()), set(clients))
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
