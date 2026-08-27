"""Turning a messy OSM `website` tag into a host the scanner can take.

OSM website tags are typed by volunteers: trailing slashes, tracking parameters,
Facebook pages, `www.`, mixed case, occasional nonsense.

One decision worth spelling out: we keep the **host as given**, minus `www.`, and
do not collapse it to its registrable domain. Collapsing is right for bulk
Certificate Transparency data, where a business appears as a hundred subdomains;
it is wrong here, where the tag is the actual address of the actual site. It would
turn a real site at shop.example.bg into example.bg and scan the wrong thing - and
because the Public Suffix List has no `com.bg` entry, it would turn
example.com.bg into com.bg, which belongs to somebody else entirely.

The registrable domain is still computed, but only to classify: is this a social
page, is this a template on a hosting provider.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

import tldextract

# Bundled Public Suffix List snapshot: no network call on first use, and the same
# answer on every machine. Refresh it by bumping tldextract.
_extract = tldextract.TLDExtract(suffix_list_urls=())

# A website tag pointing at one of these is not a website we could maintain.
NOT_A_WEBSITE = frozenset(
    {
        "facebook.com",
        "fb.com",
        "fb.me",
        "instagram.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "tiktok.com",
        "wa.me",
        "t.me",
        "viber.com",
        "google.com",
        "goo.gl",
        "booking.com",
        "airbnb.com",
        "tripadvisor.com",
        "superdoc.bg",
        "framar.bg",
        "zavedenia.com",
        "grabo.bg",
    }
)

# Site builders and free-hosting providers. A page on a subdomain of one of these
# is a template the business does not control: nothing to maintain, and usually
# nobody who could authorize us to touch it.
SHARED_HOSTS = frozenset(
    {
        "add.bg",
        "alle.bg",
        "hit.bg",
        "dir.bg",
        "data.bg",
        "wordpress.com",
        "wixsite.com",
        "weebly.com",
        "blogspot.com",
        "jimdosite.com",
        "webnode.com",
        "ucoz.com",
        "narod.ru",
        "business.site",
        "shopiko.bg",
        "cloudcart.net",
    }
)

_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*://", re.I)
_NON_HTTP = ("mailto:", "tel:", "fax:", "sms:", "geo:")


def _host_of(raw: str) -> str | None:
    if not raw:
        return None
    value = raw.strip().strip('"')
    if not value:
        return None
    value = value.split()[0]
    if value.lower().startswith(_NON_HTTP):
        return None
    if not _SCHEME.match(value):
        value = f"https://{value}"

    host = urlsplit(value).netloc.lower()
    if "@" in host:
        host = host.split("@", 1)[1]
    host = host.split(":", 1)[0].rstrip(".")
    if not host or "." not in host or " " in host:
        return None
    return host


def registrable(raw: str) -> str | None:
    """The domain someone actually registered, per the Public Suffix List."""
    host = _host_of(raw)
    if host is None:
        return None
    parsed = _extract(host)
    if not parsed.domain or not parsed.suffix:
        return None
    return f"{parsed.domain}.{parsed.suffix}"


def to_domain(raw: str) -> str | None:
    """The host to scan, or None when the tag is not a website we can work with."""
    host = _host_of(raw)
    if host is None:
        return None

    owner = registrable(host)
    if owner is None or owner in NOT_A_WEBSITE:
        return None

    return host.removeprefix("www.")


def is_social(raw: str) -> bool:
    """Did this business list a social profile or a directory listing?"""
    owner = registrable(raw)
    return owner is not None and owner in NOT_A_WEBSITE


def is_shared_host(raw: str) -> bool:
    """A template page on a builder or free-hosting provider.

    Only a known provider counts. Flagging every subdomain would throw away real
    businesses that legitimately run at shop.example.bg.
    """
    host = _host_of(raw)
    owner = registrable(raw)
    if host is None or owner is None:
        return False
    if owner not in SHARED_HOSTS:
        return False
    return host.removeprefix("www.") != owner
