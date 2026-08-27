"""Cheap HTML inspection.

Regex rather than a parser: we only ever look for fingerprints in a document we
already have in memory, and a fingerprint that needs a DOM is a fingerprint we
should not be trusting in a sales report anyway.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .probe import Fetch

BOUNDARY = chr(92) + chr(98)  # regex word boundary
WORDLIKE = chr(91) + chr(92) + chr(119) + chr(92) + chr(115) + chr(93) + chr(43)

_GENERATOR = re.compile(r"""<meta[^>]+name=["']?generator["']?[^>]+content=["']([^"']+)""", re.I)
_VIEWPORT = re.compile(r"""<meta[^>]+name=["']?viewport["']?""", re.I)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_LANG = re.compile(r"""<html[^>]+lang=["']([a-zA-Z-]+)""", re.I)
_FORM = re.compile(r"<form\b", re.I)
_INPUT_EMAIL = re.compile(r"""<input[^>]+type=["']?email""", re.I)
_INPUT_TEL = re.compile(r"""<input[^>]+type=["']?tel""", re.I)
_TEXTAREA = re.compile(r"<textarea\b", re.I)
_JQUERY_OLD = re.compile(r"jquery[.-]?(1\.\d+(\.\d+)?)(\.min)?\.js", re.I)
_CSP_META = re.compile(r"""<meta[^>]+http-equiv=["']?content-security-policy["']?""", re.I)
# Browsers use whatever <link rel="icon"> says; /favicon.ico is only the fallback.
_FAVICON_LINK = re.compile(r"""<link[^>]+rel=["']?[^"'>]*icon""", re.I)

# Is the business behind this site Bulgarian? The .bg TLD answers it only sometimes -
# plenty of Bulgarian SMEs sit on .com or .eu, so the page itself has to be asked.
_BG_PHONE = re.compile(r"(\+|00)\s?359\s?\d")
# Bulgarian company registration identifiers. A translated page never grows these.
_BG_REGISTRATION = ("еик", "булстат", "ддс № bg", "vat bg")

# (label, version-capturing pattern or None, plain markers)
_CMS_SIGNATURES: list[tuple[str, re.Pattern[str] | None, tuple[str, ...]]] = [
    (
        "WordPress",
        re.compile(r"WordPress\s+([\d.]+)", re.I),
        ("/wp-content/", "/wp-includes/", "wp-json"),
    ),
    (
        "Joomla",
        re.compile(r"Joomla!?\s*([\d.]+)", re.I),
        ("/media/jui/", "com_content", "/media/system/js/"),
    ),
    (
        "Drupal",
        re.compile(r"Drupal\s*([\d.]+)", re.I),
        ("drupal.settings", "/sites/default/files/", "drupal-"),
    ),
    ("Shopify", None, ("cdn.shopify.com", "shopify-features")),
    ("Wix", None, ("static.wixstatic.com", "wix-warmup-data")),
    ("Squarespace", None, ("squarespace.com/universal", "static1.squarespace.com")),
    (
        "Magento",
        re.compile(r"Magento[/ ]([\d.]+)", re.I),
        ("/static/version", "mage/cookies", "magento"),
    ),
    ("PrestaShop", re.compile(r"PrestaShop\s*([\d.]+)", re.I), ("prestashop", "/modules/ps_")),
    ("OpenCart", None, ("index.php?route=common", "catalog/view/theme")),
    ("CloudCart", None, ("cloudcart", "cdn.cloudcart")),
    ("Shopiko", None, ("shopiko",)),
    ("Summer Cart", None, ("summercart", "summer cart")),
    ("Tilda", None, ("tildacdn.com",)),
    ("Webflow", None, ("webflow.js", "w-webflow-badge")),
]

_ECOMMERCE_MARKERS = (
    "woocommerce",
    "add-to-cart",
    "/cart",
    "/checkout",
    "/kolichka",
    "shopping-cart",
    "количка",
    "поръчка",
    "добави в количката",
)

_BOOKING_MARKERS = (
    "booking",
    "reservation",
    "reserve",
    "book-now",
    "резервация",
    "резервирай",
    "запази час",
    "свободни стаи",
    "check-in",
)

_CONTACT_MARKERS = ("contact", "контакт", "запитване", "изпрати", "свържете")


def _compile(markers: tuple[str, ...]) -> re.Pattern[str]:
    """Word-boundary alternation for plain words, plain substring for the rest.

    Substring matching cost us real accuracy: "reserve" matches "All rights
    reserved", so booking functionality appeared to exist on almost every site.
    Markers containing punctuation ("/cart", "add-to-cart") are specific enough
    already, and word boundaries around them would not match.
    """
    parts = []
    for marker in markers:
        if re.fullmatch(WORDLIKE, marker):
            parts.append(BOUNDARY + re.escape(marker) + BOUNDARY)
        else:
            parts.append(re.escape(marker))
    return re.compile("|".join(parts), re.I)


_ECOMMERCE_RE = _compile(_ECOMMERCE_MARKERS)
_BOOKING_RE = _compile(_BOOKING_MARKERS)
_CONTACT_RE = _compile(_CONTACT_MARKERS)


@dataclass
class PageFacts:
    """Everything the checks want to know about the HTML, extracted once."""

    title: str | None = None
    lang: str | None = None
    generator: str | None = None
    cms: str | None = None
    cms_version: str | None = None
    ecommerce: str | None = None
    has_booking: bool = False
    has_form: bool = False
    has_contact_form: bool = False
    responsive: bool = False
    csp_meta: bool = False
    favicon_declared: bool = False
    old_jquery: str | None = None
    markers: list[str] = field(default_factory=list)
    bulgarian_hints: list[str] = field(default_factory=list)

    @property
    def is_bulgarian(self) -> bool:
        return bool(self.bulgarian_hints)


def extract(fetch: Fetch) -> PageFacts:
    facts = PageFacts()
    if not fetch.ok or not fetch.body or not fetch.body_decoded:
        return facts

    body = fetch.body
    low = body.lower()

    if match := _TITLE.search(body):
        facts.title = re.sub(r"\s+", " ", match.group(1)).strip()[:200]
    if match := _LANG.search(body):
        facts.lang = match.group(1).lower()
    if match := _GENERATOR.search(body):
        facts.generator = match.group(1).strip()[:120]

    facts.responsive = bool(_VIEWPORT.search(body))
    facts.csp_meta = bool(_CSP_META.search(body))
    facts.favicon_declared = bool(_FAVICON_LINK.search(body))
    if match := _JQUERY_OLD.search(body):
        facts.old_jquery = match.group(1)

    haystack = f"{low} {facts.generator or ''} {_server_hints(fetch)}".lower()
    for name, version_re, markers in _CMS_SIGNATURES:
        hit = any(marker in haystack for marker in markers)
        version = None
        if version_re and (match := version_re.search(facts.generator or "")):
            version = match.group(1)
            hit = True
        if hit:
            facts.cms = name
            facts.cms_version = version
            facts.markers.append(name.lower())
            break

    if "woocommerce" in haystack:
        facts.ecommerce = "WooCommerce"
    elif facts.cms in (
        "Shopify",
        "Magento",
        "PrestaShop",
        "OpenCart",
        "CloudCart",
        "Shopiko",
        "Summer Cart",
    ):
        facts.ecommerce = facts.cms
    elif _ECOMMERCE_RE.search(haystack):
        facts.ecommerce = "unknown"

    facts.has_booking = bool(_BOOKING_RE.search(haystack))
    facts.has_form = bool(_FORM.search(body))
    facts.has_contact_form = facts.has_form and (
        bool(_INPUT_EMAIL.search(body))
        or bool(_INPUT_TEL.search(body))
        or bool(_TEXTAREA.search(body))
        or bool(_CONTACT_RE.search(low))
    )
    facts.bulgarian_hints = _bulgarian_hints(body, low, facts.lang)
    return facts


def _bulgarian_hints(body: str, low: str, lang: str | None) -> list[str]:
    """Evidence that the business *behind* the page is Bulgarian.

    Only contact-detail evidence counts, and deliberately so. We send
    `Accept-Language: bg`, so any site with content negotiation hands us a
    Bulgarian page: mozilla.org came back with `lang="bg"`, Cyrillic text and the
    word "България" in it, and was scored a local Bulgarian SME. Language,
    Cyrillic and country names therefore prove nothing here - we caused them.

    A +359 number or an ЕИК/БУЛСТАТ registration is not something a translation
    produces. This misses a Bulgarian company that puts no contact details on its
    homepage, which is the right way round to be wrong for a one-point signal.
    """
    hints: list[str] = []
    if _BG_PHONE.search(body):
        hints.append("phone")

    found = [term for term in _BG_REGISTRATION if term in low]
    if found:
        hints.append(f"registration:{','.join(found[:2])}")
    return hints


def _server_hints(fetch: Fetch) -> str:
    if not fetch.headers:
        return ""
    parts = [
        fetch.headers.get("server", ""),
        fetch.headers.get("x-powered-by", ""),
        fetch.headers.get("x-generator", ""),
        " ".join(fetch.headers.get_list("set-cookie")),
        " ".join(k for k in fetch.headers if k.lower().startswith("x-")),
    ]
    return " ".join(parts)
