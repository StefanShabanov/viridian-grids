"""Turn the versions we found into things we can actually say.

Runs over saved scans, not over the prospect: every lookup here is against a
public database, so enriching costs the target nothing. That is deliberate - it
is the depth nuclei offered without the traffic that got us firewalled.

Where the wording is careful, it is careful on purpose:

  End of life is a fact. "PHP 7.4 stopped receiving security updates on
  28 November 2022" is a date anyone can check, it is about maintenance rather
  than accusation, and it is the strongest line we have for a cold email.

  A CVE match is not a fact about *them*. Distributions backport fixes without
  changing the version string, and Bulgarian shared hosting usually runs
  distribution PHP. So findings say vulnerabilities "have been reported against
  this version", never "your site is vulnerable" - which we do not know and
  cannot responsibly imply to a stranger.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..models import Category, Finding, ScanResult, Severity, Status
from .sources import Cache, end_of_life, vulnerabilities
from .store import IntelStore


def versions_in(result: ScanResult) -> list[tuple[str, str]]:
    """(product, version) pairs the scan established, newest source first."""
    found: dict[str, str] = {}
    for finding in result.findings:
        name = str(finding.params.get("name", ""))
        version = str(finding.params.get("version", ""))
        if name and version and name not in found:
            found[name] = version
    return sorted(found.items())


def enrich(
    result: ScanResult,
    *,
    store: IntelStore | None = None,
    api_key: str = "",
    include_cves: bool = True,
    refresh: bool = False,
) -> list[Finding]:
    """Look every detected version up and return the findings that result."""
    cache = Cache(store=store or IntelStore(), refresh=refresh)
    findings: list[Finding] = []

    for product, version in versions_in(result):
        eol = end_of_life(product, version, cache)
        if eol is not None:
            findings.append(_eol_finding(product, version, eol))

        if not include_cves:
            continue
        reported = vulnerabilities(product, version, cache, api_key=api_key)
        if reported:
            findings.append(_cve_finding(product, version, reported))

    return findings


# Projects that backport security fixes to old release lines. For these,
# endoflife.date "eol" marks the end of *feature* support, not of security
# patches - our own output gave this away by declaring WordPress 6.1 dead while
# naming 6.1.12 as its latest release. Saying "no longer receives security
# updates" about one of these would be false, and false in the direction that
# costs us the credibility this whole lookup exists to build.
BACKPORTS_SECURITY = {"WordPress", "Drupal", "Joomla"}


def _slug(product: str) -> str:
    return product.lower().replace(" ", "_")


def _parts(version: str) -> tuple[int, ...]:
    numbers: list[int] = []
    for chunk in version.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        if not digits:
            break
        numbers.append(int(digits))
    return tuple(numbers)


def _is_behind(version: str, latest: str) -> bool:
    """Is this version actually older, rather than just written differently?

    A plain string comparison called WordPress 7.1 "behind" WordPress 7.1.0 -
    the same release, one trailing zero apart - which is exactly the sort of
    sloppy claim that gets an email deleted.
    """
    if not latest or not version:
        return False
    ours, theirs = _parts(version), _parts(latest)
    if not ours or not theirs:
        return version != latest
    width = max(len(ours), len(theirs))
    ours += (0,) * (width - len(ours))
    theirs += (0,) * (width - len(theirs))
    return ours < theirs


def _eol_finding(product: str, version: str, eol) -> Finding:
    behind = _is_behind(version, eol.latest)

    if eol.is_eol and product not in BACKPORTS_SECURITY:
        since = eol.eol_date.strftime("%d %B %Y") if eol.eol_date else "some time ago"
        detail = f"The {product} {eol.cycle} line reached end of life on {since}."
        if behind:
            detail += f" This site runs {version}; the line ended at {eol.latest}."
        else:
            detail += f" This site runs {version}, the final release on that line."
        return Finding(
            id=f"intel.eol.{_slug(product)}",
            category=Category.TECHNOLOGY,
            status=Status.WARN,
            severity=Severity.MEDIUM,
            weight=10,
            source="intel",
            title=f"{product} {eol.cycle} no longer receives security updates",
            detail=detail,
            reference="https://endoflife.date/",
            params={"name": product, "version": version, "cycle": eol.cycle},
        )

    if behind:
        # True for everything, and stronger than an end-of-life claim: they are
        # behind on the very line they chose to stay on.
        return Finding(
            id=f"intel.behind.{_slug(product)}",
            category=Category.TECHNOLOGY,
            status=Status.WARN,
            severity=Severity.LOW,
            weight=6,
            source="intel",
            title=f"{product} {version} is behind its own release line",
            detail=(
                f"The {product} {eol.cycle} line has since reached {eol.latest}, "
                "which includes the security fixes released for it in the meantime."
            ),
            reference="https://endoflife.date/",
            params={"name": product, "version": version, "cycle": eol.cycle, "latest": eol.latest},
        )

    return Finding(
        id=f"intel.current.{_slug(product)}",
        category=Category.TECHNOLOGY,
        status=Status.PASS,
        source="intel",
        title=f"{product} {version} is current",
        detail=f"Latest release on the {eol.cycle} line.",
        params={"name": product, "version": version, "cycle": eol.cycle},
    )


def _cve_finding(product: str, version: str, reported: list) -> Finding:
    worst = reported[0].severity or "UNRATED"
    counts: dict[str, int] = {}
    for item in reported:
        counts[item.severity or "UNRATED"] = counts.get(item.severity or "UNRATED", 0) + 1
    breakdown = ", ".join(f"{count} {name.lower()}" for name, count in counts.items())

    # Weight stays modest even for a critical: we have matched a version, not
    # demonstrated an exposure, and the report tone rule applies to us too.
    weight = 12 if worst in ("CRITICAL", "HIGH") else 5

    return Finding(
        id=f"intel.cve.{_slug(product)}",
        category=Category.TECHNOLOGY,
        status=Status.WARN,
        severity=Severity.MEDIUM if weight > 5 else Severity.LOW,
        weight=weight,
        source="intel",
        title=f"Vulnerabilities have been reported against {product} {version}",
        detail=(
            f"{len(reported)} publicly reported ({breakdown}), including "
            f"{reported[0].cve}. These affect {product} {version} unless the host has "
            "backported the fixes, which distribution packages often do."
        ),
        reference=reported[0].url,
        params={"name": product, "version": version, "worst": worst},
        evidence={"cves": [item.cve for item in reported]},
    )


def stamp() -> str:
    return datetime.now(UTC).date().isoformat()
