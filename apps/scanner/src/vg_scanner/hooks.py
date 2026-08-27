"""Picking the one thing to say to a prospect.

A scan produces twenty findings. An email needs one. This chooses it, and the
choice is not "the most severe finding" - it is **the most specific one**.

Measured across 1,028 Bulgarian SME sites, the security headers are missing on
69-79% of them. A finding that common says nothing about the recipient, and they
can tell. What earns a reply is something true about *their* site that is not
true about everyone else's: a certificate with a date on it, a version that
stopped receiving fixes, a site that is down right now.

Every hook carries a `kind`, so the CRM can record which opener was used and the
first hundred emails can answer the question the plan actually cares about -
which opener converts.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import ScanResult, Status

# Findings so common across the market that they identify nobody. Never a hook.
COMMODITY = {
    "http.hsts_missing",
    "http.csp_missing",
    "http.xcto_missing",
    "http.referrer_policy_missing",
    "http.permissions_policy_missing",
    "http.clickjacking_unprotected",
    "observatory.grade",
    "configuration.sitemap_missing",
    "configuration.robots_missing",
    "configuration.favicon_missing",
}


@dataclass
class Hook:
    kind: str = "none"
    text: str = ""
    detail: str = ""
    urgency: int = 0  # higher sorts first within a prospect list

    @property
    def usable(self) -> bool:
        return self.kind != "none"


def choose(result: ScanResult) -> Hook:
    """The single best thing to lead with, or nothing worth writing about."""
    if not result.reachable:
        dead = any(f.id == "availability.dns_failure" for f in result.findings)
        if dead:
            return Hook("dead", "Domain does not resolve", "Drop from the list.", 0)
        return Hook(
            "site_down",
            "The website is not responding",
            "The domain is still registered but the server is not answering. Call, do not email.",
            100,
        )

    if result.inconclusive:
        return Hook("blocked", "Scan was blocked", "Nothing here is safe to send.", 0)

    by_id = {f.id: f for f in result.findings}

    # 1. A certificate somebody has to remember to renew, with a date on it.
    for finding_id in ("tls.certificate_expiring_urgently", "tls.certificate_expiring_soon"):
        finding = by_id.get(finding_id)
        if finding:
            days = finding.params.get("days")
            expires = finding.params.get("expires")
            return Hook(
                "cert_expiry",
                f"Certificate expires in {days} days ({expires})",
                "Manually renewed, so somebody has to remember. If it lapses, browsers "
                "show a security warning and visitors stop booking.",
                90 - int(days or 0),
            )

    # 2. Something whose vendor has stopped shipping security fixes. A date, checkable.
    eol = [f for f in result.findings if f.id.startswith("intel.eol.")]
    if eol:
        finding = max(eol, key=lambda f: f.weight)
        return Hook("software_eol", finding.title, finding.detail or "", 70)

    # 3. Visitors already see "Not secure" today.
    if "configuration.http_no_redirect" in by_id:
        return Hook(
            "no_https_redirect",
            "The plain address is not redirected to HTTPS",
            "Anyone typing the address without https sees a Not secure warning today.",
            65,
        )
    if "availability.https_unavailable" in by_id:
        return Hook(
            "no_https",
            "The site has no working HTTPS",
            "Every visitor sees a Not secure warning.",
            80,
        )
    if "configuration.http_error" in by_id:
        return Hook(
            "http_error",
            "The plain HTTP address returns a server error",
            "Half-broken rather than merely unencrypted.",
            75,
        )

    # 4. Publicly reported vulnerabilities against a detected version.
    cve = [f for f in result.findings if f.id.startswith("intel.cve.")]
    if cve:
        finding = max(cve, key=lambda f: f.weight)
        return Hook("known_cves", finding.title, finding.detail or "", 60)

    # 5. Behind on its own release line, or publishing its version.
    behind = [f for f in result.findings if f.id.startswith("intel.behind.")]
    if behind:
        finding = max(behind, key=lambda f: f.weight)
        return Hook("outdated", finding.title, finding.detail or "", 50)

    versions = [f for f in result.findings if f.id.startswith("webanalyze.version.")]
    if versions:
        listed = ", ".join(
            f"{f.params.get('name')} {f.params.get('version')}" for f in versions[:3]
        )
        return Hook(
            "version_exposed",
            f"Publishes its software versions: {listed}",
            "Visible to every visitor, and it shows exactly which updates are outstanding.",
            40,
        )

    # 6. Slow, or duplicated across www and non-www.
    for finding_id, kind, urgency in (
        ("performance.response_very_slow", "slow", 45),
        ("performance.response_slow", "slow", 30),
        ("configuration.canonical_host_duplicate", "duplicate_host", 25),
    ):
        finding = by_id.get(finding_id)
        if finding:
            return Hook(kind, finding.id, "", urgency)

    remaining = [
        f
        for f in result.by_status(Status.WARN, Status.FAIL)
        if f.id not in COMMODITY and f.source != "vg"
    ]
    if remaining:
        finding = remaining[0]
        return Hook("other", finding.title or finding.id, finding.detail or "", 10)

    return Hook()
