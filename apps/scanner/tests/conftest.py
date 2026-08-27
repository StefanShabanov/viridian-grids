"""Synthetic scan contexts.

Every test in this suite is offline. Checks must be judgeable without a network,
otherwise tuning weights means waiting on someone else's web server.
"""

from __future__ import annotations

import pytest
from httpx import Headers

from vg_scanner.content import extract
from vg_scanner.context import ScanContext
from vg_scanner.probe import Fetch, TlsInfo

HTML_WORDPRESS = """
<!doctype html><html lang="bg"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta name="generator" content="WordPress 6.4.2">
<title>Хотел Пример</title></head>
<body class="woocommerce home">
<form action="/contact"><input type="email" name="mail"><textarea name="msg"></textarea></form>
<a href="/cart">количка</a><a href="/booking">резервация</a>
</body></html>
"""

HTML_PLAIN = (
    "<!doctype html><html><head><title>Plain</title>"
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    "</head><body><p>hi</p></body></html>"
)


def make_fetch(
    url: str = "https://example.bg",
    *,
    status: int | None = 200,
    ok: bool = True,
    headers: dict[str, str] | None = None,
    body: str = HTML_PLAIN,
    ttfb_ms: float = 210.0,
    set_cookie: list[str] | None = None,
    redirects: list[tuple[int, str]] | None = None,
    error: str | None = None,
) -> Fetch:
    fetch = Fetch(url=url)
    fetch.ok = ok
    fetch.status = status
    fetch.headers = Headers(headers or {})
    fetch.body = body
    fetch.body_bytes = len(body.encode())
    fetch.ttfb_ms = ttfb_ms
    fetch.total_ms = ttfb_ms + 40
    fetch.final_url = url
    fetch.scheme = url.split(":", 1)[0]
    fetch.set_cookie = set_cookie or []
    fetch.redirects = redirects or []
    fetch.error = error
    return fetch


def make_tls(
    *,
    available: bool = True,
    trusted: bool = True,
    days: int | None = 300,
    version: str = "TLSv1.3",
    legacy: list[str] | None = None,
    hostname_ok: bool = True,
) -> TlsInfo:
    from datetime import UTC, datetime, timedelta

    info = TlsInfo()
    info.available = available
    info.trusted = trusted
    info.hostname_ok = hostname_ok
    info.negotiated_version = version
    info.issuer = "Let's Encrypt"
    info.days_remaining = days
    if days is not None:
        info.not_after = datetime.now(UTC) + timedelta(days=days)
    info.legacy_versions = legacy or []
    info.legacy_tested = True
    return info


def make_context(
    *,
    primary: Fetch | None = None,
    https: Fetch | None = None,
    http: Fetch | None = None,
    sibling: Fetch | None = None,
    tls: TlsInfo | None = None,
    robots: Fetch | None = None,
    sitemap: Fetch | None = None,
    favicon: Fetch | None = None,
    domain: str = "example.bg",
) -> ScanContext:
    primary = primary or make_fetch()
    ctx = ScanContext(domain=domain, url=f"https://{domain}")
    ctx.primary = primary
    ctx.https = https if https is not None else primary
    ctx.http = http
    ctx.sibling = sibling
    ctx.sibling_name = f"www.{domain}"
    ctx.tls = tls if tls is not None else make_tls()
    ctx.robots = robots
    ctx.sitemap = sitemap
    ctx.favicon = favicon
    ctx.facts = extract(primary)
    return ctx


@pytest.fixture
def healthy_context() -> ScanContext:
    """A well-configured site: nothing here should warn."""
    headers = {
        "strict-transport-security": "max-age=31536000; includeSubDomains",
        "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
        "x-content-type-options": "nosniff",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "camera=(), microphone=()",
        "content-encoding": "gzip",
    }
    primary = make_fetch(headers=headers)
    return make_context(
        primary=primary,
        http=make_fetch(
            "http://example.bg", status=301, headers={"location": "https://example.bg/"}
        ),
        sibling=make_fetch(
            "https://www.example.bg", status=301, headers={"location": "https://example.bg/"}
        ),
        robots=make_fetch("https://example.bg/robots.txt"),
        sitemap=make_fetch("https://example.bg/sitemap.xml"),
        favicon=make_fetch("https://example.bg/favicon.ico"),
    )


@pytest.fixture
def neglected_context() -> ScanContext:
    """A typical prospect: WordPress, no headers, slow, no HTTPS redirect."""
    primary = make_fetch(
        headers={"server": "Apache/2.4.29 (Ubuntu)", "x-powered-by": "PHP/7.2.24"},
        body=HTML_WORDPRESS,
        ttfb_ms=2600.0,
        set_cookie=["sessid=abc; Path=/"],
    )
    return make_context(
        primary=primary,
        http=make_fetch("http://example.bg", status=200),
        sibling=make_fetch("https://www.example.bg", status=200),
        tls=make_tls(days=38, legacy=["TLSv1"]),
        robots=make_fetch("https://example.bg/robots.txt", status=404, ok=True),
        sitemap=make_fetch("https://example.bg/sitemap.xml", status=404, ok=True),
        favicon=make_fetch("https://example.bg/favicon.ico", status=404, ok=True),
    )
