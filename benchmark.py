"""Synthetic functional benchmark. No external users or production accuracy implied.
Run: PYTHONPATH=. python benchmark.py --output benchmark-results.json
Optional baseline dependency: python -m pip install jsonschema
"""
import argparse
import copy
import json
import platform
import statistics
import time
from resultgate.extraction import audit_extraction


def base():
    return dict(records=[{"id": 1, "name": "Ada"}], required_fields=["/name"],
                unique_fields=["/id"], expected_count=1, job_status="completed",
                next_cursor=None, truncated=False)


def fixtures():
    cases = [("complete", "pass", base())]
    for name, update in [
        ("failed_job", {"job_status": "failed"}),
        ("cancelled_job", {"job_status": "cancelled"}),
        ("job_in_progress", {"job_status": "scraping"}),
        ("next_page", {"next_cursor": "p2"}),
        ("cursor_loop", {"next_cursor": "p2", "seen_cursors": ["p1", "p2"]}),
        ("truncated", {"truncated": True}),
        ("short_count", {"expected_count": 3}),
        ("missing_field", {"records": [{"id": 1}]}),
        ("null_field", {"records": [{"id": 1, "name": None}]}),
        ("blank_field", {"records": [{"id": 1, "name": "  "}]}),
        ("duplicate_id", {"records": [{"id": 1, "name": "Ada"}, {"id": 1, "name": "Bob"}], "expected_count": 2}),
        ("missing_key", {"records": [{"name": "Ada"}]}),
    ]:
        p = base(); p.update(update)
        cases.append((name, "fail", p))
    for field in ("expected_count", "job_status", "next_cursor", "truncated"):
        p = base(); del p[field]
        cases.append(("unknown_without_" + field, "unknown", p))
    p = base(); p.update(records=[], expected_count=0)
    cases.append(("verified_empty", "pass", p))
    return cases


def native_status_only(p):
    status = p.get("job_status")
    if status == "completed":
        return "pass"
    if status in ("failed", "cancelled", "scraping"):
        return "fail"
    return "unknown"


def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="benchmark-results.json")
    ap.add_argument("--repeats", type=int, default=200)
    args = ap.parse_args()
    if args.repeats < 1:
        ap.error("repeats must be >= 1")
    cases = fixtures()
    baselines = {"resultgate": lambda p: audit_extraction(p)["status"],
                 "native_status_only": native_status_only}
    unavailable = []
    try:
        from jsonschema import Draft202012Validator
        schema = {"type": "object", "required": ["records"], "properties": {
            "records": {"type": "array", "items": {"type": "object", "required": ["name"]}}}}
        validator = Draft202012Validator(schema)
        baselines["jsonschema_required_fields_only"] = lambda p: "pass" if validator.is_valid(p) else "fail"
    except ImportError:
        unavailable.append("jsonschema baseline skipped: dependency absent; no substitute timing or result invented")
    summary = {}
    for name, fn in baselines.items():
        predictions = [(case, expected, fn(copy.deepcopy(p))) for case, expected, p in cases]
        latencies = []
        for _ in range(args.repeats):
            for _, _, p in cases:
                start = time.perf_counter_ns()
                fn(p)
                latencies.append((time.perf_counter_ns() - start) / 1e6)
        ordered = sorted(latencies)
        errors = [x for x in predictions if x[1] != x[2]]
        summary[name] = {"fixture_count": len(cases), "correct_fixture_verdicts": len(cases)-len(errors),
                         "mismatches": [{"case": c, "expected": e, "actual": a} for c,e,a in errors],
                         "timed_calls": len(latencies), "latency_ms_median": statistics.median(latencies),
                         "latency_ms_p95": ordered[int(.95 * (len(ordered)-1))]}
    # Scale latency is separate from correctness; records are synthetic and all unique.
    p = base()
    p.update(records=[{"id": i, "name": "Synthetic"} for i in range(5000)], expected_count=5000)
    scale_times = []
    for _ in range(20):
        start = time.perf_counter_ns(); result = audit_extraction(p)
        scale_times.append((time.perf_counter_ns()-start)/1e6)
    report = {"benchmark_type": "synthetic rule coverage and local latency; not independent usage",
              "limitations": ["Hand-authored fixtures match the defined contract; not a held-out accuracy estimate.",
                              "Baselines are narrow checks, not full competing products.",
                              "No network, model inference, third-party endpoint or production workload measured.",
                              "Pass validates supplied evidence consistency, not external truth."],
              "python": platform.python_version(), "platform": platform.platform(),
              "results": summary, "unavailable": unavailable,
              "scale_5000_records": {"verdict": result["status"], "runs": 20,
                                     "latency_ms_median": statistics.median(scale_times)}}
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
