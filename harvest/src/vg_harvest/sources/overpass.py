"""OpenStreetMap via the Overpass API - the source that matches the ICP.

Top-lists were tried first and are useless here: Majestic Million holds 688 .bg
domains and they are google.bg, government.bg, uni-sofia.bg and the ministries.
Backlink rank will never surface a dentist in Plovdiv.

OSM gives the opposite: real businesses tagged by exactly the verticals the plan
names, with a website and often a phone and a town. Free, no API key.

Overpass is donated infrastructure with a two-slot limit per client. One query per
vertical, paced, retried on overload, and cached to disk so a re-run costs nothing.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

# The main instance blocks clients that query it too hard - at the network level,
# so it looks like "connection refused" rather than an HTTP 429. Mirrors are tried
# in turn; if all of them refuse, the honest answer is to wait, not to retry harder.
ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
USER_AGENT = "ViridianGrids-Harvest/0.1 (prospect research; +https://viridiangrids.example)"

PACE_SECONDS = 5.0
MAX_ATTEMPTS = 3

# vertical -> OSM selectors. Straight from docs/icp-and-prospecting.md.
VERTICALS: dict[str, tuple[str, ...]] = {
    "dentist": ('["amenity"="dentist"]', '["healthcare"="dentist"]'),
    "clinic": ('["amenity"="clinic"]', '["amenity"="doctors"]'),
    "veterinary": ('["amenity"="veterinary"]',),
    "hotel": ('["tourism"="hotel"]',),
    "guest_house": ('["tourism"="guest_house"]', '["tourism"="apartment"]'),
    "lawyer": ('["office"="lawyer"]',),
    "accountant": ('["office"="accountant"]', '["office"="tax_advisor"]'),
    "estate_agent": ('["office"="estate_agent"]',),
    "restaurant": ('["amenity"="restaurant"]',),
    "beauty": ('["shop"="beauty"]', '["shop"="hairdresser"]'),
    "car_repair": ('["shop"="car_repair"]',),
}

WEBSITE_TAGS = ("website", "contact:website", "url")
PHONE_TAGS = ("phone", "contact:phone", "contact:mobile")
EMAIL_TAGS = ("email", "contact:email")


class OverpassError(RuntimeError):
    pass


@dataclass
class Business:
    """One business as OSM knows it. The website is the point; the rest is context."""

    name: str = ""
    website: str = ""
    phone: str = ""
    email: str = ""
    city: str = ""
    vertical: str = ""
    osm_id: str = ""
    tags: dict[str, str] = field(default_factory=dict)


def build_query(vertical: str, country: str = "BG", timeout: int = 180) -> str:
    """One vertical per query.

    Asking for every vertical at once was refused by the server's own dispatcher
    timeout - restaurants across a whole country is already heavy, and the rest on
    top never finished. Small queries also mean a failure costs one vertical
    instead of the whole run.
    """
    selectors = "\n".join(f"  nwr{selector}(area.target);" for selector in VERTICALS[vertical])
    return (
        f"[out:json][timeout:{timeout}];\n"
        f'area["ISO3166-1"="{country}"][admin_level=2]->.target;\n'
        f"(\n{selectors}\n);\n"
        "out tags center;"
    )


def fetch_vertical(
    vertical: str,
    *,
    country: str = "BG",
    timeout: float = 240.0,
    cache_dir: Path | None = None,
    refresh: bool = False,
) -> list[Business]:
    """Fetch one vertical, reusing the cached response unless asked to refresh."""
    if vertical not in VERTICALS:
        raise KeyError(vertical)

    cache = cache_dir / f"{country.lower()}-{vertical}.json" if cache_dir else None
    if cache and cache.exists() and not refresh:
        payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        payload = _request(build_query(vertical, country=country), timeout)
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(payload), encoding="utf-8")

    businesses = [_to_business(element, vertical) for element in payload.get("elements", [])]
    return [b for b in businesses if b.website]


def _request(query: str, timeout: float) -> dict:
    problems: list[str] = []
    for endpoint in ENDPOINTS:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = httpx.post(
                    endpoint,
                    data={"data": query},
                    timeout=timeout,
                    headers={"User-Agent": USER_AGENT},
                )
            except httpx.HTTPError as exc:
                problems.append(f"{_host(endpoint)}: {type(exc).__name__}")
                break  # unreachable: move to the next mirror rather than retrying

            # Overpass reports overload and timeouts as an HTML page, not as JSON.
            if response.status_code == 200 and response.text.lstrip().startswith("{"):
                return response.json()

            problems.append(f"{_host(endpoint)}: {_explain(response.status_code, response.text)}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(PACE_SECONDS * attempt * 2)

    raise OverpassError("; ".join(dict.fromkeys(problems)) or "no endpoint answered")


def _host(endpoint: str) -> str:
    return endpoint.split("//", 1)[-1].split("/", 1)[0]


def _explain(status: int, body: str) -> str:
    lowered = body.lower()
    if status == 429 or "rate_limited" in lowered or "too many requests" in lowered:
        return "rate limited by Overpass (two slots per client) - pace the queries"
    if "timeout" in lowered:
        return "query too heavy for the server (dispatcher timeout)"
    if "out of memory" in lowered:
        return "query too large for the server (out of memory)"
    return f"Overpass returned HTTP {status} and no JSON"


def _to_business(element: dict, vertical: str) -> Business:
    tags = element.get("tags", {})
    return Business(
        name=tags.get("name") or tags.get("operator") or "",
        website=_first(tags, WEBSITE_TAGS),
        phone=_first(tags, PHONE_TAGS),
        email=_first(tags, EMAIL_TAGS),
        city=tags.get("addr:city") or tags.get("addr:place") or "",
        vertical=vertical,
        osm_id=f"{element.get('type', '')}/{element.get('id', '')}",
        tags=tags,
    )


def _first(tags: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = tags.get(key)
        if value:
            return str(value).strip()
    return ""
