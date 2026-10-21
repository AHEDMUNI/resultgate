"""Offline, deterministic provider matching for ResultGate.

No network calls, billing, or referral claims. Provider entries are supplied
by the caller and must be independently verified before production use.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Provider:
    provider_id: str
    name: str
    capabilities: tuple[str, ...]
    endpoint: str
    price_usd: float | None = None
    verified: bool = False
    referral_terms_verified: bool = False


def route_task(
    required_capabilities: Iterable[str],
    providers: Iterable[Provider],
    *,
    max_price_usd: float | None = None,
    require_verified: bool = True,
) -> list[dict]:
    """Return matching providers ranked by cost, with explicit trust flags.

    Matching requires every requested capability; no invented providers or
    implicit claims that a referral commission exists.
    """
    required = {s.strip().lower() for s in required_capabilities if s.strip()}
    if not required:
        raise ValueError("At least one required capability is needed")
    if max_price_usd is not None and (isinstance(max_price_usd, bool) or not math.isfinite(max_price_usd) or max_price_usd < 0):
        raise ValueError("max_price_usd must be nonnegative")
    matches = []
    for provider in providers:
        if require_verified and not provider.verified:
            continue
        if not required.issubset({c.strip().lower() for c in provider.capabilities}):
            continue
        if provider.price_usd is not None and (isinstance(provider.price_usd, bool) or not math.isfinite(provider.price_usd) or provider.price_usd < 0):
            continue
        if max_price_usd is not None and (
            provider.price_usd is None or provider.price_usd > max_price_usd
        ):
            continue
        matches.append({
            "provider_id": provider.provider_id,
            "name": provider.name,
            "endpoint": provider.endpoint,
            "price_usd": provider.price_usd,
            "verified": provider.verified,
            "referral_terms_verified": provider.referral_terms_verified,
            "commission_available": False,  # Caller flags are not an executed agreement.
            "verification_source": "caller_asserted_not_trusted",
        })
    return sorted(matches, key=lambda p: (
        p["price_usd"] is None,
        p["price_usd"] if p["price_usd"] is not None else float("inf"),
        p["provider_id"],
    ))
