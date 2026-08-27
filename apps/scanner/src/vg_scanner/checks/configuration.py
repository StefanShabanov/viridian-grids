"""The unglamorous configuration issues that actually cost small businesses money:
plain HTTP that never redirects, a www variant nobody set up, a redirect loop.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from ..context import ScanContext
from ..models import Category, Finding, Severity, Status
from .availability import is_blocked
from .base import make

C = Category.CONFIGURATION

LONG_CHAIN_HOPS = 3


def run(ctx: ScanContext) -> list[Finding]:
    out: list[Finding] = []
    out.extend(_http_redirect(ctx))
    out.extend(_redirect_chain(ctx))
    out.extend(_canonical_host(ctx))
    out.extend(_well_known(ctx))
    out.extend(_favicon(ctx))
    return out


def _favicon(ctx: ScanContext) -> list[Finding]:
    """A 404 on /favicon.ico is not a missing favicon.

    Almost every site points at its icon with <link rel="icon">, which is what
    browsers actually use. We were reporting well-run shops as having no favicon
    purely because the legacy path was empty.
    """
    if ctx.facts.favicon_declared:
        return [make("configuration.favicon_present", C, Status.PASS, params={"what": "favicon"})]

    probe = ctx.favicon
    if probe is None:
        return []
    if probe.ok and probe.status and 200 <= probe.status < 300:
        return [make("configuration.favicon_present", C, Status.PASS, params={"what": "favicon"})]
    if is_blocked(probe) or probe.status is None or probe.status >= 500:
        return [
            make(
                "configuration.well_known_unavailable",
                C,
                Status.SKIPPED,
                params={"what": "favicon", "status": probe.status or 0},
            )
        ]
    return [
        make(
            "configuration.favicon_missing",
            C,
            Status.WARN,
            severity=Severity.INFO,
            weight=1,
            params={"what": "favicon", "status": probe.status or 0},
        )
    ]


def _http_redirect(ctx: ScanContext) -> list[Finding]:
    http = ctx.http
    if not http or (not http.ok and not http.redirects and http.status is None):
        # No plain-HTTP listener at all is a legitimate configuration, not a fault.
        return [make("configuration.http_closed", C, Status.INFO)]

    status = http.status
    location = ""
    if http.redirects:
        status, location = http.redirects[0]
    elif status and 300 <= status < 400:
        location = http.header("location") or ""

    if status and 300 <= status < 400:
        if location.lower().startswith("https://"):
            permanent = status in (301, 308)
            return [
                make(
                    "configuration.http_redirects_https"
                    if permanent
                    else "configuration.http_redirects_https_temporary",
                    C,
                    Status.PASS if permanent else Status.WARN,
                    severity=Severity.LOW,
                    weight=0 if permanent else 2,
                    params={"status": status},
                    evidence={"location": location},
                )
            ]
        return [
            make(
                "configuration.http_redirects_elsewhere",
                C,
                Status.WARN,
                severity=Severity.MEDIUM,
                weight=6,
                params={"location": location or "unknown"},
            )
        ]

    if status and status >= 500:
        # Saying "visitors stay unencrypted" would be wrong: the plain address is
        # broken outright, which is a bigger problem and a better thing to raise.
        return [
            make(
                "configuration.http_error",
                C,
                Status.WARN,
                severity=Severity.MEDIUM,
                weight=8,
                params={"status": status},
            )
        ]

    return [
        make(
            "configuration.http_no_redirect",
            C,
            Status.WARN,
            severity=Severity.MEDIUM,
            weight=8,
            params={"status": status or 0},
        )
    ]


def _redirect_chain(ctx: ScanContext) -> list[Finding]:
    primary = ctx.primary
    if not primary:
        return []
    if primary.error == "redirect loop" or primary.error == "too many redirects":
        return [
            make(
                "configuration.redirect_loop",
                C,
                Status.FAIL,
                severity=Severity.HIGH,
                weight=15,
                evidence={"chain": [url for _, url in primary.redirects][:10]},
            )
        ]
    hops = len(primary.redirects)
    if hops >= LONG_CHAIN_HOPS:
        return [
            make(
                "configuration.redirect_chain_long",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=2,
                params={"hops": hops},
                evidence={"chain": [url for _, url in primary.redirects][:10]},
            )
        ]
    return []


def _canonical_host(ctx: ScanContext) -> list[Finding]:
    sibling = ctx.sibling
    name = ctx.sibling_name
    if not sibling:
        return []

    if not sibling.ok and sibling.status is None and not sibling.redirects:
        return [
            make(
                "configuration.canonical_host_unreachable",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=3,
                params={"host": name, "error": sibling.error or "no response"},
            )
        ]

    status = sibling.status
    location = sibling.header("location") or ""
    if status and 300 <= status < 400 and location:
        target_host = urlsplit(location).netloc.lower()
        if target_host and target_host != name:
            return [
                make(
                    "configuration.canonical_host_ok",
                    C,
                    Status.PASS,
                    params={"host": name, "target": target_host},
                )
            ]

    if status and 200 <= status < 300:
        return [
            make(
                "configuration.canonical_host_duplicate",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=3,
                params={"host": name},
            )
        ]
    return []


def _well_known(ctx: ScanContext) -> list[Finding]:
    out: list[Finding] = []
    checks = (
        (
            "robots.txt",
            ctx.robots,
            "configuration.robots_present",
            "configuration.robots_missing",
            1,
        ),
        (
            "sitemap",
            ctx.sitemap,
            "configuration.sitemap_present",
            "configuration.sitemap_missing",
            1,
        ),
    )
    for label, probe, ok_id, missing_id, weight in checks:
        if probe is None:
            continue
        if probe.ok and probe.status and 200 <= probe.status < 300:
            out.append(make(ok_id, C, Status.PASS, params={"what": label}))
        elif is_blocked(probe):
            # A blocked request tells us nothing about whether the file exists.
            out.append(
                make(
                    "configuration.well_known_blocked",
                    C,
                    Status.SKIPPED,
                    params={"what": label, "status": probe.status or 0},
                )
            )
        elif probe.status is None or probe.status >= 500:
            # A server error or a failed request is not evidence of absence. We
            # reported "Sitemap is missing (HTTP 500)" and "(HTTP 0)", both untrue.
            out.append(
                make(
                    "configuration.well_known_unavailable",
                    C,
                    Status.SKIPPED,
                    params={"what": label, "status": probe.status or 0},
                )
            )
        else:
            out.append(
                make(
                    missing_id,
                    C,
                    Status.WARN,
                    severity=Severity.INFO,
                    weight=weight,
                    params={"what": label, "status": probe.status or 0},
                )
            )
    return out
