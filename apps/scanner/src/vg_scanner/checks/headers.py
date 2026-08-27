"""Security headers.

Weights here are small on purpose. A missing Permissions-Policy is a housekeeping
item, not a breach, and a report that says otherwise costs us the customer.
"""

from __future__ import annotations

import re

from ..context import ScanContext
from ..models import Category, Finding, Severity, Status
from .base import make

C = Category.HTTP

HSTS_SHORT_MAX_AGE = 15_552_000  # 180 days, the usual "you meant to do more" line
_MAX_AGE = re.compile(r"max-age\s*=\s*(\d+)", re.I)


def run(ctx: ScanContext) -> list[Finding]:
    primary = ctx.primary
    if not primary or not primary.ok:
        return [make("http.headers_not_checked", C, Status.SKIPPED)]

    out: list[Finding] = []
    out.extend(_hsts(ctx))
    out.extend(_csp(ctx))
    out.extend(_frame_options(ctx))

    out.append(
        _simple(
            ctx,
            header="x-content-type-options",
            ok_id="http.xcto_present",
            missing_id="http.xcto_missing",
            weight=2,
        )
    )
    out.append(
        _simple(
            ctx,
            header="referrer-policy",
            ok_id="http.referrer_policy_present",
            missing_id="http.referrer_policy_missing",
            weight=2,
        )
    )
    out.append(
        _simple(
            ctx,
            header="permissions-policy",
            ok_id="http.permissions_policy_present",
            missing_id="http.permissions_policy_missing",
            weight=1,
            severity=Severity.LOW,
        )
    )
    return out


def _simple(
    ctx: ScanContext,
    *,
    header: str,
    ok_id: str,
    missing_id: str,
    weight: int,
    severity: Severity = Severity.LOW,
) -> Finding:
    value = ctx.primary.header(header)
    if value:
        return make(ok_id, C, Status.PASS, params={"value": value[:120]})
    return make(missing_id, C, Status.WARN, severity=severity, weight=weight)


def _hsts(ctx: ScanContext) -> list[Finding]:
    # HSTS over plain HTTP is meaningless, so only judge it when HTTPS works.
    if not ctx.https_ok:
        return [make("http.hsts_not_applicable", C, Status.SKIPPED)]

    value = ctx.https.header("strict-transport-security")
    if not value:
        return [make("http.hsts_missing", C, Status.WARN, severity=Severity.MEDIUM, weight=4)]

    match = _MAX_AGE.search(value)
    max_age = int(match.group(1)) if match else 0
    if max_age < HSTS_SHORT_MAX_AGE:
        return [
            make(
                "http.hsts_short",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=2,
                params={"days": max_age // 86400},
                evidence={"header": value[:200]},
            )
        ]
    return [
        make(
            "http.hsts_present",
            C,
            Status.PASS,
            params={"days": max_age // 86400},
            evidence={"header": value[:200]},
        )
    ]


def _csp(ctx: ScanContext) -> list[Finding]:
    value = ctx.primary.header("content-security-policy")
    if value:
        return [make("http.csp_present", C, Status.PASS, evidence={"header": value[:200]})]
    if ctx.primary.header("content-security-policy-report-only"):
        return [
            make(
                "http.csp_report_only",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=2,
            )
        ]
    if ctx.facts.csp_meta:
        return [make("http.csp_meta_only", C, Status.WARN, severity=Severity.LOW, weight=2)]
    return [make("http.csp_missing", C, Status.WARN, severity=Severity.MEDIUM, weight=4)]


def _frame_options(ctx: ScanContext) -> list[Finding]:
    xfo = ctx.primary.header("x-frame-options")
    csp = ctx.primary.header("content-security-policy") or ""
    if xfo or "frame-ancestors" in csp.lower():
        return [
            make(
                "http.clickjacking_protected",
                C,
                Status.PASS,
                params={"via": "X-Frame-Options" if xfo else "CSP frame-ancestors"},
            )
        ]
    return [make("http.clickjacking_unprotected", C, Status.WARN, severity=Severity.LOW, weight=2)]
