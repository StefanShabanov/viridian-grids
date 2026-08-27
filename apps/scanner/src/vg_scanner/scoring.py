"""Scoring - deliberately boring, deliberately pure.

Two separate numbers that must never be confused:

  score          what we show the prospect. 100 minus the weight of what we found.
  prospect_score what we keep for ourselves. How much this company is worth
                 fifteen minutes of personal outreach.

Keeping this a pure function over findings means weights can be re-tuned against
a saved corpus of scans without touching a single check or making a request.
"""

from __future__ import annotations

from .context import ScanContext
from .models import Finding, ProspectScore, ProspectSignal, Status

# name -> points, straight from docs/icp-and-prospecting.md
SIGNAL_POINTS = {
    "wordpress": 3,
    "woocommerce": 3,
    "slow_response": 2,
    "missing_headers": 2,
    "outdated_site": 2,
    "business_form": 2,
    "booking_ecommerce": 2,
    "local_bg_sme": 1,
}
MAX_PROSPECT_SCORE = sum(SIGNAL_POINTS.values())

_HEADER_GAPS = {
    "http.hsts_missing",
    "http.csp_missing",
    "http.xcto_missing",
    "http.referrer_policy_missing",
}
# Signs the *site* looks dated, which is what the outreach actually talks about.
# Server-side TLS and compression settings were in here originally and fired on 11
# of the first 12 sites scanned, including mozilla.org - a signal that common
# discriminates nothing. They still cost score; they just no longer rank prospects.
_DATED_SIGNS = {
    "technology.not_responsive",
    "technology.legacy_javascript",
    "technology.cms_version_exposed",
}


def score(findings: list[Finding]) -> int:
    """100 minus the weight of everything that warned or failed, floored at zero."""
    deducted = sum(finding.weight for finding in findings if finding.deducts)
    return max(0, 100 - deducted)


def band(value: int) -> str:
    """Coarse label for the report. Three bands, no letter grades, no drama."""
    if value >= 85:
        return "good"
    if value >= 60:
        return "fair"
    return "poor"


def prospect_score(ctx: ScanContext, findings: list[Finding]) -> ProspectScore:
    ids = {finding.id for finding in findings if finding.status is not Status.SKIPPED}
    facts = ctx.facts
    hit: list[str] = []

    if facts.cms == "WordPress":
        hit.append("wordpress")
    if facts.ecommerce == "WooCommerce":
        hit.append("woocommerce")
    if {"performance.response_slow", "performance.response_very_slow"} & ids:
        hit.append("slow_response")
    if len(_HEADER_GAPS & ids) >= 2:
        hit.append("missing_headers")
    # Engine-sourced version findings count too. When webanalyze supersedes our own
    # version check the id changes, and keying only on ours silently lost the signal
    # on exactly the sites that have it most.
    dated = bool(_DATED_SIGNS & ids) or any(i.startswith("webanalyze.version.") for i in ids)
    if dated:
        hit.append("outdated_site")
    if facts.has_contact_form:
        hit.append("business_form")
    if facts.has_booking or facts.ecommerce:
        hit.append("booking_ecommerce")
    if ctx.domain.endswith(".bg") or facts.is_bulgarian:
        hit.append("local_bg_sme")

    signals = [ProspectSignal(name=name, points=SIGNAL_POINTS[name]) for name in hit]
    return ProspectScore(
        total=sum(signal.points for signal in signals),
        max=MAX_PROSPECT_SCORE,
        signals=signals,
    )
