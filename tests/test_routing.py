from resultgate.routing import Provider, route_task
import pytest


def test_matching_and_price_order():
    providers = [
        Provider("b", "B", ("pdf", "ocr"), "https://example.org/b", 2, True),
        Provider("a", "A", ("pdf", "ocr"), "https://example.org/a", 1, True),
        Provider("c", "C", ("pdf",), "https://example.org/c", 0, True),
    ]
    assert [p["provider_id"] for p in route_task(["pdf", "ocr"], providers)] == ["a", "b"]


def test_unverified_excluded_by_default():
    provider = Provider("a", "A", ("pdf",), "https://example.org/a")
    assert route_task(["pdf"], [provider]) == []
    assert len(route_task(["pdf"], [provider], require_verified=False)) == 1


def test_budget_and_commission_not_assumed():
    provider = Provider("a", "A", ("pdf",), "https://example.org/a", 2, True)
    assert route_task(["pdf"], [provider], max_price_usd=1) == []
    assert route_task(["pdf"], [provider])[0]["commission_available"] is False


def test_empty_capabilities_rejected():
    with pytest.raises(ValueError):
        route_task([], [])
