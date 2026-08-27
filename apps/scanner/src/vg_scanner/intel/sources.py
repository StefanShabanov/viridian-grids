"""Version intelligence: what is known, publicly, about the versions we found.

Nothing here touches the prospect. We already hold exact versions from
webanalyze; this looks them up against public databases. That is what makes it
safe to do at all - it is the depth nuclei promised without the 1,040 requests.

Two sources, both free and without an API key:

  endoflife.date   when a release line stopped receiving security updates.
                   A date, not an opinion, and the strongest thing we can say
                   to a business owner.
  NVD (NIST)       publicly reported vulnerabilities affecting a version.

The honest caveat, which the wording everywhere must respect: a version match is
not proof of exposure. Distributions backport security fixes without changing
the version string, and Bulgarian shared hosting very often runs distribution
PHP. "Publicly reported vulnerabilities affect this version unless your host has
backported the fixes" is true. "You are vulnerable" is not something we know.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime

from .store import IntelStore

EOL_API = "https://endoflife.date/api/{product}.json"
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
USER_AGENT = "ViridianGrids-HealthCheck/0.1 (+https://viridiangrids.example)"

# NVD allows roughly 5 requests per 30 seconds without a key, 50 with one.
NVD_PAUSE_SECONDS = 6.5
NVD_PAUSE_WITH_KEY = 0.7

# What webanalyze calls it -> (endoflife.date slug, CPE vendor, CPE product).
PRODUCTS: dict[str, tuple[str | None, str | None, str | None]] = {
    "WordPress": ("wordpress", "wordpress", "wordpress"),
    "PHP": ("php", "php", "php"),
    "Nginx": ("nginx", "nginx", "nginx"),
    "Apache HTTP Server": ("apache", "apache", "http_server"),
    "MySQL": ("mysql", "oracle", "mysql"),
    "OpenSSL": ("openssl", "openssl", "openssl"),
    "Joomla": ("joomla", "joomla", "joomla!"),
    "Drupal": ("drupal", "drupal", "drupal"),
}


@dataclass
class EndOfLife:
    product: str
    cycle: str
    eol_date: date | None = None
    is_eol: bool = False
    latest: str = ""


@dataclass
class Vulnerability:
    cve: str
    severity: str = ""
    summary: str = ""

    @property
    def url(self) -> str:
        return f"https://nvd.nist.gov/vuln/detail/{self.cve}"


@dataclass
class Cache:
    """Thin wrapper over the local intel database.

    Sites share versions constantly - 218 shortlisted sites collapse to 66
    distinct product+version pairs - so this turns a rate-limited lookup into one
    request per distinct version, ever, rather than one per site.

    Entries expire (see store.py): new CVEs get published against versions that
    never change, so a cache without a TTL grows confidently wrong.
    """

    store: IntelStore
    refresh: bool = False

    def get(self, kind: str, product: str, version: str = "") -> object | None:
        if self.refresh:
            return None
        return self.store.get(kind, product, version)

    def put(self, kind: str, product: str, version: str, value: object) -> None:
        self.store.put(kind, product, version, value)


def _get(url: str, headers: dict[str, str] | None = None, timeout: float = 30.0) -> dict | list:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


# --------------------------------------------------------------------- end of life


def end_of_life(product: str, version: str, cache: Cache) -> EndOfLife | None:
    """Which release line this version is on, and whether it still gets fixes."""
    slug = PRODUCTS.get(product, (None, None, None))[0]
    if not slug or not version:
        return None

    cycles = cache.get("eol", slug)
    if cycles is None:
        try:
            cycles = _get(EOL_API.format(product=slug))
        except (urllib.error.URLError, OSError, ValueError):
            return None
        cache.put("eol", slug, "", cycles)

    cycle = _match_cycle(version, cycles)  # type: ignore[arg-type]
    if cycle is None:
        return None

    eol_raw = cycle.get("eol")
    eol_date = _as_date(eol_raw)
    is_eol = eol_raw is True or (eol_date is not None and eol_date <= datetime.now(UTC).date())
    return EndOfLife(
        product=product,
        cycle=str(cycle.get("cycle", "")),
        eol_date=eol_date,
        is_eol=is_eol,
        latest=str(cycle.get("latest", "")),
    )


def _match_cycle(version: str, cycles: list[dict]) -> dict | None:
    """Longest cycle prefix wins, so 8.0.28 matches cycle "8.0" over cycle "8"."""
    best: dict | None = None
    for cycle in cycles:
        name = str(cycle.get("cycle", ""))
        if not name:
            continue
        matches = version == name or version.startswith(f"{name}.")
        if matches and (best is None or len(name) > len(str(best.get("cycle", "")))):
            best = cycle
    return best


def _as_date(value: object) -> date | None:
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


# ------------------------------------------------------------------------- NVD


def vulnerabilities(
    product: str,
    version: str,
    cache: Cache,
    *,
    api_key: str = "",
    limit: int = 6,
) -> list[Vulnerability] | None:
    """Publicly reported vulnerabilities affecting this exact version."""
    _, vendor, cpe_product = PRODUCTS.get(product, (None, None, None))
    if not vendor or not cpe_product or not version:
        return None

    cached = cache.get("cve", product, version)
    if cached is None:
        cpe = f"cpe:2.3:a:{vendor}:{cpe_product}:{version}"
        url = (
            f"{NVD_API}?{urllib.parse.urlencode({'virtualMatchString': cpe, 'resultsPerPage': 20})}"
        )
        headers = {"apiKey": api_key} if api_key else {}
        try:
            payload = _get(url, headers=headers, timeout=45.0)
        except (urllib.error.URLError, OSError, ValueError):
            return None
        cached = [_to_vulnerability(item) for item in payload.get("vulnerabilities", [])]  # type: ignore[union-attr]
        cache.put("cve", product, version, cached)
        time.sleep(NVD_PAUSE_WITH_KEY if api_key else NVD_PAUSE_SECONDS)

    found = [Vulnerability(**item) for item in cached]  # type: ignore[arg-type]
    found.sort(key=lambda v: _severity_rank(v.severity))
    return found[:limit]


def _to_vulnerability(item: dict) -> dict:
    cve = item.get("cve", {})
    severity = ""
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)
        if entries:
            data = entries[0].get("cvssData", {})
            severity = data.get("baseSeverity") or entries[0].get("baseSeverity") or ""
            break
    descriptions = cve.get("descriptions", [])
    summary = descriptions[0]["value"] if descriptions else ""
    return {"cve": cve.get("id", ""), "severity": severity.upper(), "summary": summary[:300]}


_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "": 4}


def _severity_rank(severity: str) -> int:
    return _SEVERITY_ORDER.get(severity.upper(), 4)
