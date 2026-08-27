"""Gathers everything the checks need, in one pass, with a fixed request budget.

Checks never make requests of their own. That keeps the load on a prospect's site
predictable and auditable: if you want to know what we did to someone's server,
you read this file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .content import PageFacts, extract
from .probe import DEFAULT_TIMEOUT, Fetch, TlsInfo, fetch, inspect_tls, make_client, sibling_host

_ROBOTS_SITEMAP = re.compile(r"^\s*sitemap:\s*(\S+)", re.I | re.M)


@dataclass
class ScanContext:
    domain: str
    url: str
    authorized: bool = False
    https: Fetch | None = None
    http: Fetch | None = None
    primary: Fetch | None = None
    sibling: Fetch | None = None
    sibling_name: str = ""
    robots: Fetch | None = None
    sitemap: Fetch | None = None
    favicon: Fetch | None = None
    tls: TlsInfo | None = None
    facts: PageFacts = field(default_factory=PageFacts)
    errors: list[str] = field(default_factory=list)

    @property
    def reachable(self) -> bool:
        return bool(self.primary and self.primary.ok)

    @property
    def https_ok(self) -> bool:
        return bool(self.https and self.https.ok)

    @property
    def origin(self) -> str:
        """Scheme + host of wherever the site actually ended up."""
        source = self.primary.final_url if self.primary and self.primary.final_url else self.url
        parts = urlsplit(source)
        return f"{parts.scheme}://{parts.netloc}"


def gather(
    domain: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    authorized: bool = False,
    check_aux: bool = True,
    check_legacy_tls: bool = True,
) -> ScanContext:
    ctx = ScanContext(domain=domain, url=f"https://{domain}", authorized=authorized)
    ctx.sibling_name = sibling_host(domain)

    with make_client(timeout=timeout) as client:
        # 1. The site itself, over HTTPS, following redirects.
        ctx.https = fetch(client, f"https://{domain}")
        ctx.primary = ctx.https

        # 2. Plain HTTP, without following, purely to see the redirect behaviour.
        ctx.http = fetch(client, f"http://{domain}", follow_redirects=False, read_body=False)

        # 3. If HTTPS is unusable, the site still has to be assessed over HTTP.
        if not ctx.https.ok:
            over_http = fetch(client, f"http://{domain}")
            if over_http.ok:
                ctx.primary = over_http

        # 4. www vs apex.
        ctx.sibling = fetch(
            client,
            f"https://{ctx.sibling_name}",
            follow_redirects=False,
            read_body=False,
        )

        if ctx.primary and ctx.primary.ok:
            ctx.facts = extract(ctx.primary)

        if check_aux and ctx.reachable:
            origin = ctx.origin
            ctx.robots = fetch(client, f"{origin}/robots.txt", follow_redirects=True)
            if not ctx.facts.favicon_declared:
                # Only worth asking when the page did not already say where its icon is.
                ctx.favicon = fetch(
                    client, f"{origin}/favicon.ico", follow_redirects=True, read_body=False
                )
            ctx.sitemap = fetch(
                client,
                _sitemap_url(ctx.robots, origin),
                follow_redirects=True,
                read_body=False,
            )

    # Always inspect TLS, even when HTTPS failed - the reason it failed is the finding.
    ctx.tls = inspect_tls(domain, timeout=timeout, test_legacy=check_legacy_tls)

    if ctx.https and ctx.https.error:
        ctx.errors.append(f"https://{domain}: {ctx.https.error}")
    if ctx.tls and ctx.tls.error:
        ctx.errors.append(f"tls {domain}: {ctx.tls.error}")
    return ctx


def _sitemap_url(robots: Fetch | None, origin: str) -> str:
    """Prefer the sitemap robots.txt declares; fall back to the conventional path."""
    if robots and robots.ok and robots.body and (match := _ROBOTS_SITEMAP.search(robots.body)):
        return match.group(1).strip()
    return f"{origin}/sitemap.xml"
