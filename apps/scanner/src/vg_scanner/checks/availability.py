"""Is the site up, does it serve HTTPS, and does it answer with a sane status."""

from __future__ import annotations

from ..context import ScanContext
from ..models import Category, Finding, Severity, Status
from .base import make

C = Category.AVAILABILITY

BLOCKED_STATUSES = (401, 403, 429)
CHALLENGE_MARKERS = (
    "just a moment",
    "attention required",
    "cf-browser-verification",
    "cf-chl",
    "checking your browser",
    "access denied",
    "captcha",
    "ddos-guard",
    "incapsula",
)


DNS_MARKERS = (
    "dns lookup failed",
    "name or service not known",
    "nodename nor servname",
    "temporary failure in name resolution",  # glibc EAI_AGAIN, errno -3
    "no address associated with hostname",  # glibc EAI_NODATA, errno -5
)


def _is_dns_failure(reason: str) -> bool:
    """No DNS at all usually means the domain lapsed and the business is gone.

    A refused connection or a timeout is the opposite: the domain is still paid
    for and the server is down, which is the most valuable thing we ever find.
    """
    lowered = reason.lower()
    return any(marker in lowered for marker in DNS_MARKERS)


def is_blocked(fetch) -> bool:
    """True when the server refused the automated request rather than failing.

    Distinguishing the two matters more than it looks: a 403 aimed at bots means we
    learned nothing, while a 403 on a real homepage is a genuine outage. Guessing
    wrong in either direction puts something untrue in an outreach email.
    """
    if fetch.status in BLOCKED_STATUSES:
        return True
    body = (fetch.body or "").lower()[:4000]
    return fetch.status in (503, 520) and any(m in body for m in CHALLENGE_MARKERS)


def run(ctx: ScanContext) -> list[Finding]:
    out: list[Finding] = []
    primary = ctx.primary

    if not primary or not primary.ok:
        reason = (primary.error if primary else None) or "no response"
        # Weighted to land near the floor. At 40 an unreachable domain scored
        # 57/100 - above a live, high-value prospect at 43 - which inverts the
        # ranked list. There is no health to assess when nothing answers.
        finding_id = (
            "availability.dns_failure" if _is_dns_failure(reason) else "availability.unreachable"
        )
        return [
            make(
                finding_id,
                C,
                Status.FAIL,
                severity=Severity.HIGH,
                weight=85,
                params={"error": reason},
                evidence={"url": ctx.url},
            )
        ]

    out.append(make("availability.reachable", C, Status.PASS, params={"url": primary.final_url}))

    if ctx.https_ok:
        # Our client ignores certificate errors on purpose, so a successful fetch is
        # not proof a visitor gets through. When the certificate is untrusted the TLS
        # check reports it; claiming HTTPS "works" here would contradict the browser.
        if not (ctx.tls and ctx.tls.available and not ctx.tls.trusted):
            out.append(make("availability.https_ok", C, Status.PASS))
    else:
        out.append(
            make(
                "availability.https_unavailable",
                C,
                Status.FAIL,
                severity=Severity.HIGH,
                weight=25,
                params={"error": (ctx.https.error if ctx.https else None) or "no HTTPS response"},
            )
        )

    status = primary.status or 0
    if is_blocked(primary):
        # Bot protection, not a broken website. Reporting it as an error would put a
        # false accusation in front of a prospect, so the scan is marked inconclusive.
        out.append(
            make(
                "availability.request_blocked",
                C,
                Status.SKIPPED,
                params={"status": status},
            )
        )
    elif 200 <= status < 300:
        out.append(make("availability.status_ok", C, Status.PASS, params={"status": status}))
    elif 300 <= status < 400:
        out.append(
            make(
                "availability.status_redirect",
                C,
                Status.WARN,
                severity=Severity.MEDIUM,
                weight=10,
                params={"status": status},
            )
        )
    else:
        out.append(
            make(
                "availability.status_error",
                C,
                Status.FAIL,
                severity=Severity.HIGH,
                weight=20,
                params={"status": status},
            )
        )

    return out
