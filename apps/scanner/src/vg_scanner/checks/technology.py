"""What the site is built on, and what it tells the world about itself.

Detection is a sales signal first and a finding second: knowing a prospect runs
WordPress is worth more to the outreach than the two points a Server header costs.
"""

from __future__ import annotations

from ..context import ScanContext
from ..models import Category, Finding, Severity, Status
from .base import make

C = Category.TECHNOLOGY


def run(ctx: ScanContext) -> list[Finding]:
    primary = ctx.primary
    if not primary or not primary.ok or not primary.body_decoded:
        # An unreadable body means we detected nothing, which is not the same as
        # there being nothing to detect. Reporting it as absence would be a lie.
        return [make("technology.not_checked", C, Status.SKIPPED)]

    facts = ctx.facts
    out: list[Finding] = []

    if facts.cms:
        out.append(
            make(
                "technology.cms_detected",
                C,
                Status.INFO,
                params={"name": facts.cms, "version": facts.cms_version or ""},
                evidence={"generator": facts.generator},
            )
        )
        if facts.cms_version:
            out.append(
                make(
                    "technology.cms_version_exposed",
                    C,
                    Status.WARN,
                    severity=Severity.LOW,
                    weight=3,
                    params={"name": facts.cms, "version": facts.cms_version},
                )
            )
    else:
        out.append(make("technology.cms_unknown", C, Status.INFO))

    if facts.ecommerce == "unknown":
        # An unidentified shop is still a shop, and that is what decides whether
        # the site matters to the business behind it.
        out.append(make("technology.ecommerce_unidentified", C, Status.INFO))
    elif facts.ecommerce:
        out.append(
            make("technology.ecommerce_detected", C, Status.INFO, params={"name": facts.ecommerce})
        )
    if facts.has_booking:
        out.append(make("technology.booking_detected", C, Status.INFO))

    out.extend(_exposed_headers(ctx))

    if not facts.responsive:
        out.append(
            make(
                "technology.not_responsive",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=3,
            )
        )
    if facts.old_jquery:
        out.append(
            make(
                "technology.legacy_javascript",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=2,
                params={"library": "jQuery", "version": facts.old_jquery},
            )
        )
    return out


def _exposed_headers(ctx: ScanContext) -> list[Finding]:
    out: list[Finding] = []
    server = ctx.primary.header("server") or ""
    powered = ctx.primary.header("x-powered-by") or ""

    # A bare product name is normal; a version number is the thing worth mentioning.
    if server and any(ch.isdigit() for ch in server):
        out.append(
            make(
                "technology.server_version_exposed",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=2,
                params={"server": server[:80]},
            )
        )
    elif server:
        out.append(make("technology.server_header", C, Status.INFO, params={"server": server[:80]}))

    if powered:
        out.append(
            make(
                "technology.powered_by_exposed",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=2,
                params={"value": powered[:80]},
            )
        )
    return out
