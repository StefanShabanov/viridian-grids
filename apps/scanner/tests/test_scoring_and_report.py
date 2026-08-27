"""Scoring, prospect ranking, the message catalog, and what the customer sees."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vg_scanner.catalog import DISCLAIMER, LANGUAGES, MESSAGES, heading, resolve
from vg_scanner.models import Category, Finding, Severity, Status
from vg_scanner.probe import normalize_domain, sibling_host
from vg_scanner.report import csv_row, render_html, render_text
from vg_scanner.runner import scan_context
from vg_scanner.scoring import MAX_PROSPECT_SCORE, band, score

CHECKS_DIR = Path(__file__).resolve().parents[1] / "src" / "vg_scanner" / "checks"

# Some checks pass ids through a variable rather than inline into make(), so match
# any string literal carrying a known category prefix. Anchoring on the categories
# keeps "robots.txt" and friends out of the results.
EMITTED_ID = re.compile(r'"((?:' + "|".join(c.value for c in Category) + r')\.[a-z_]+)"')


# ------------------------------------------------------------------ the catalog


def emitted_ids() -> set[str]:
    found: set[str] = set()
    for path in CHECKS_DIR.glob("*.py"):
        found.update(EMITTED_ID.findall(path.read_text(encoding="utf-8")))
    return found


def test_every_emitted_finding_has_text_in_every_language():
    """A finding with no catalog entry renders as a raw id in front of a prospect."""
    missing = {}
    for finding_id in sorted(emitted_ids()):
        entry = MESSAGES.get(finding_id)
        if entry is None:
            missing[finding_id] = "no catalog entry"
        else:
            absent = [lang for lang in LANGUAGES if lang not in entry]
            if absent:
                missing[finding_id] = f"missing {absent}"
    assert not missing, missing


ENGINE_PREFIXES = ("testssl.", "nuclei.", "observatory.", "webanalyze.")


def test_catalog_has_no_orphans():
    """Entries for ids nothing emits are dead weight and drift out of date.

    Engine ids are built at runtime from tool output, so they cannot be found by
    reading our source; they are exempt.
    """
    ours = {k for k in MESSAGES if not k.startswith(ENGINE_PREFIXES)}
    assert not ours - emitted_ids()


@pytest.mark.parametrize("lang", LANGUAGES)
def test_catalog_placeholders_resolve(lang):
    """Every {placeholder} must be fillable, or the report shows a raw template."""
    for finding_id, entry in MESSAGES.items():
        title, detail = entry[lang]
        params = {name: "x" for name in re.findall(r"\{(\w+)\}", title + detail)}
        finding = Finding(id=finding_id, category=Category.HTTP, status=Status.INFO, params=params)
        rendered_title, rendered_detail = resolve(finding, lang)
        assert "{" not in rendered_title + rendered_detail, finding_id


# ------------------------------------------------------------------- the scoring


def test_score_is_100_minus_weights():
    findings = [
        Finding(id="a.b", category=Category.HTTP, status=Status.WARN, weight=4),
        Finding(id="c.d", category=Category.HTTP, status=Status.FAIL, weight=25),
        Finding(id="e.f", category=Category.HTTP, status=Status.PASS, weight=99),
        Finding(id="g.h", category=Category.HTTP, status=Status.SKIPPED, weight=99),
    ]
    assert score(findings) == 71


def test_score_never_goes_negative():
    heavy = [Finding(id="a.b", category=Category.HTTP, status=Status.FAIL, weight=500)]
    assert score(heavy) == 0


def test_no_single_missing_header_can_drop_a_site_below_good():
    """The tone rule, enforced: one header is worth a nudge, not an alarm."""
    for finding_id in ("http.hsts_missing", "http.csp_missing", "http.xcto_missing"):
        one = [Finding(id=finding_id, category=Category.HTTP, status=Status.WARN, weight=4)]
        assert band(score(one)) == "good"


def test_prospect_score_ranks_the_neglected_wordpress_site(neglected_context, healthy_context):
    neglected = scan_context(neglected_context).prospect_score
    healthy = scan_context(healthy_context).prospect_score

    assert neglected.total > healthy.total
    assert neglected.max == MAX_PROSPECT_SCORE
    names = {s.name for s in neglected.signals}
    assert {"wordpress", "woocommerce", "slow_response", "local_bg_sme"} <= names


# -------------------------------------------------------------------- rendering


def test_customer_html_never_leaks_the_prospect_score(neglected_context):
    result = scan_context(neglected_context)
    assert result.prospect_score.total > 0
    html = render_html(result, "en")
    assert "rospect" not in html
    for signal in result.prospect_score.signals:
        assert signal.name not in html


@pytest.mark.parametrize("lang", LANGUAGES)
def test_report_always_carries_the_disclaimer(neglected_context, lang):
    result = scan_context(neglected_context)
    assert DISCLAIMER[lang] in render_html(result, lang)
    assert DISCLAIMER[lang] in render_text(result, lang)


def test_text_report_shows_prospect_score_only_when_internal(neglected_context):
    result = scan_context(neglected_context)
    assert "internal" in render_text(result, "en", internal=True)
    assert "internal" not in render_text(result, "en", internal=False)


def test_attention_items_are_ordered_worst_first(neglected_context):
    neglected_context.tls = None
    result = scan_context(neglected_context)
    text = render_text(result, "en")
    lines = [line for line in text.splitlines() if line.startswith("  [!]")]
    assert lines, "expected warnings"
    first = result.by_status(Status.WARN, Status.FAIL)
    severities = [f.severity for f in first]
    assert Severity.MEDIUM in severities


def test_csv_row_is_shaped_for_the_crm(neglected_context):
    row = csv_row(scan_context(neglected_context))
    assert row["Domain"] == "example.bg"
    assert row["Website platform"].startswith("WordPress")
    assert row["Interesting finding"]
    assert isinstance(row["Scan score"], int)


# ------------------------------------------------------------------- input mess


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("example.bg", "example.bg"),
        ("  HTTPS://WWW.Example.BG/some/path?a=1  ", "www.example.bg"),
        ("http://example.bg:8080", "example.bg"),
        ("ivan@example.bg", "example.bg"),
        ("example.bg.", "example.bg"),
    ],
)
def test_normalize_domain(raw, expected):
    assert normalize_domain(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "localhost", "not a domain"])
def test_normalize_domain_rejects_rubbish(raw):
    with pytest.raises(ValueError):
        normalize_domain(raw)


def test_sibling_host_round_trips():
    assert sibling_host("example.bg") == "www.example.bg"
    assert sibling_host("www.example.bg") == "example.bg"


def test_inconclusive_scan_is_flagged_everywhere_it_could_be_missed(healthy_context):
    """A blocked scan must be impossible to send by accident."""
    healthy_context.primary.status = 403
    result = scan_context(healthy_context)

    assert result.inconclusive
    assert csv_row(result)["Needs manual review"] == "yes"
    for lang in LANGUAGES:
        assert heading("inconclusive", lang) in render_html(result, lang)
        assert heading("inconclusive", lang) in render_text(result, lang)


# ----------------------------------------------------------- marker discipline


@pytest.mark.parametrize(
    ("text", "booking"),
    [
        ("All rights reserved 2026", False),
        ("Vsichki prava zapazeni", False),
        ("we reserved the right", False),
        ("Reserve a table", True),
        ("online reservation form", True),
        ("book now for tonight", False),
    ],
)
def test_booking_markers_need_word_boundaries(text, booking):
    """ "reserve" is a substring of "All rights reserved", which appears in almost
    every footer. Substring matching made booking look near-universal."""
    from vg_scanner.content import _BOOKING_RE

    assert bool(_BOOKING_RE.search(text.lower())) is booking


def test_bulgarian_shop_platforms_are_recognised():
    """CloudCart and Shopiko are common in the target market; missing them costs
    prospect points on exactly the companies this business is aimed at."""
    from vg_scanner.content import extract

    from .conftest import make_fetch

    for marker, expected in (("cloudcart", "CloudCart"), ("shopiko", "Shopiko")):
        body = f'<html><head><title>Shop</title></head><body><script src="//{marker}.com/a.js">'
        facts = extract(make_fetch(body=body))
        assert facts.cms == expected
        assert facts.ecommerce == expected


@pytest.mark.parametrize(
    ("body", "expected", "why"),
    [
        ("<html><body>Plain English shop</body></html>", False, "no Bulgarian signal"),
        ("<html><body>Tel: +359 2 123 456</body></html>", True, "Bulgarian phone prefix"),
        ("<html><body>Tel: 00359 888 123456</body></html>", True, "international prefix form"),
        ("<html><body>ЕИК 123456789</body></html>", True, "company registration number"),
        ("<html><body>БУЛСТАТ 831234567</body></html>", True, "legacy registration number"),
        ("<html><body>Sofia, Bulgaria</body></html>", False, "a mention is not an address"),
    ],
)
def test_bulgarian_business_detection(body, expected, why):
    """A .com domain must not hide a Bulgarian SME from the prospect ranking."""
    from vg_scanner.content import extract

    from .conftest import make_fetch

    assert extract(make_fetch(body=body)).is_bulgarian is expected, why


def test_a_translated_page_is_not_a_bulgarian_business():
    """We send Accept-Language: bg, so sites hand us Bulgarian pages on request.
    mozilla.org came back with lang=bg, Cyrillic and the word "България" in it and
    was scored a local Bulgarian SME. Only contact evidence may count."""
    from vg_scanner.content import extract

    from .conftest import make_fetch

    translated = (
        '<html lang="bg"><body>'
        + ("Изтеглете браузъра Firefox. Достъпно в България и още 90 държави. " * 40)
        + "</body></html>"
    )
    facts = extract(make_fetch(body=translated))
    assert facts.lang == "bg"
    assert facts.is_bulgarian is False


def test_engine_version_findings_still_mark_a_site_as_dated(neglected_context):
    """webanalyze supersedes our version check, which changes the finding id. The
    prospect signal must follow the fact, not the id."""
    from vg_scanner.models import Category, Finding
    from vg_scanner.scoring import prospect_score

    result = scan_context(neglected_context)
    findings = [f for f in result.findings if f.id != "technology.cms_version_exposed"]
    findings.append(
        Finding(
            id="webanalyze.version.wordpress",
            category=Category.TECHNOLOGY,
            status=Status.WARN,
            source="webanalyze",
            weight=2,
        )
    )
    signals = {s.name for s in prospect_score(neglected_context, findings).signals}
    assert "outdated_site" in signals


def test_platform_column_survives_an_engine_superseding_our_check(neglected_context):
    """webanalyze replaces our CMS finding, which silently emptied the
    "Website platform" column in the prospect list for every scanned site."""
    from vg_scanner.models import Category, Finding
    from vg_scanner.report import csv_row

    result = scan_context(neglected_context)
    result.findings = [f for f in result.findings if f.id != "technology.cms_detected"]
    result.findings.append(
        Finding(
            id="webanalyze.cms",
            category=Category.TECHNOLOGY,
            status=Status.INFO,
            source="webanalyze",
            params={"name": "WordPress", "version": "6.1.12"},
        )
    )
    assert csv_row(result)["Website platform"] == "WordPress 6.1.12"


def test_certificate_columns_are_exported_for_the_prospect_list(healthy_context):
    """Outreach is timed off these, so they belong in the CRM export."""
    from vg_scanner.report import csv_row

    row = csv_row(scan_context(healthy_context))
    assert row["Cert expires"]
    assert row["Cert days left"]
    assert row["Cert renewal"] in ("manual", "automatic")


def test_corpus_platform_breakdown_reads_engine_findings_too(neglected_context):
    """A 50-site corpus reported "none detected" for every site while webanalyze
    had found WordPress on eleven of them."""
    from vg_scanner.aggregate import aggregate
    from vg_scanner.models import Category, Finding

    result = scan_context(neglected_context)
    result.findings = [f for f in result.findings if f.id != "technology.cms_detected"]
    result.findings.append(
        Finding(
            id="webanalyze.cms",
            category=Category.TECHNOLOGY,
            status=Status.INFO,
            source="webanalyze",
            params={"name": "WordPress", "version": "6.1.12"},
        )
    )
    assert aggregate([result]).platforms["WordPress"] == 1


# --------------------------------------------------------- version intelligence


@pytest.mark.parametrize(
    ("version", "latest", "behind"),
    [
        ("7.1", "7.1.0", False),
        ("7.1.0", "7.1", False),
        ("6.1.6", "6.1.12", True),
        ("8.0.28", "8.0.30", True),
        ("1.23.4", "1.23.4", False),
        ("7.4.33", "7.4.33", False),
        ("10", "9.9", False),
    ],
)
def test_version_comparison_is_numeric_not_textual(version, latest, behind):
    """String comparison called WordPress 7.1 "behind" 7.1.0 - the same release."""
    from vg_scanner.intel import _is_behind

    assert _is_behind(version, latest) is behind


def test_wordpress_is_never_declared_end_of_life():
    """WordPress backports security fixes to old branches: 6.1 was marked EOL in
    March 2023 and shipped 6.1.12 afterwards. Claiming otherwise is false."""
    from vg_scanner.intel import BACKPORTS_SECURITY, _eol_finding
    from vg_scanner.intel.sources import EndOfLife

    assert "WordPress" in BACKPORTS_SECURITY
    eol = EndOfLife(product="WordPress", cycle="6.1", is_eol=True, latest="6.1.12")
    finding = _eol_finding("WordPress", "6.1.6", eol)

    assert "no longer receives security updates" not in finding.title
    assert finding.id == "intel.behind.wordpress"


def test_php_end_of_life_is_stated_plainly():
    """PHP genuinely stops: that date is the strongest line we have."""
    from datetime import date

    from vg_scanner.intel import _eol_finding
    from vg_scanner.intel.sources import EndOfLife

    eol = EndOfLife(
        product="PHP", cycle="7.4", is_eol=True, eol_date=date(2022, 11, 28), latest="7.4.33"
    )
    finding = _eol_finding("PHP", "7.4.33", eol)

    assert finding.id == "intel.eol.php"
    assert "28 November 2022" in finding.detail


def test_cve_findings_never_claim_the_site_is_vulnerable():
    """We matched a version; we did not demonstrate an exposure. Distributions
    backport fixes without changing the version string."""
    from vg_scanner.intel import _cve_finding
    from vg_scanner.intel.sources import Vulnerability

    finding = _cve_finding(
        "PHP", "8.0.28", [Vulnerability(cve="CVE-2023-3824", severity="CRITICAL")]
    )
    text = f"{finding.title} {finding.detail}".lower()

    assert "you are vulnerable" not in text
    assert "your site is vulnerable" not in text
    assert "reported" in text
    assert "backported" in text
    assert finding.weight <= 12, "a version match must not dominate the score"


def test_intel_lookups_expire(tmp_path):
    """New CVEs are filed against versions that never change, so a cache without
    a TTL grows confidently wrong."""
    from vg_scanner.intel.store import IntelStore

    store = IntelStore(path=tmp_path / "intel.db", max_age_days=30)
    store.put("cve", "PHP", "8.0.28", [{"cve": "CVE-2023-3824"}])
    assert store.get("cve", "PHP", "8.0.28") is not None

    aged = IntelStore(path=tmp_path / "intel.db", max_age_days=0)
    assert aged.get("cve", "PHP", "8.0.28") is None, "should be considered stale"
    assert aged.get("cve", "PHP", "8.0.28", allow_stale=True) is not None
    assert ("PHP", "8.0.28") in [(p, v) for p, v, _ in aged.stale()]


def test_intel_store_reports_what_it_holds(tmp_path):
    from vg_scanner.intel.store import IntelStore

    store = IntelStore(path=tmp_path / "intel.db")
    store.put("cve", "PHP", "8.0.28", [])
    store.put("eol", "php", "", [{"cycle": "8.0"}])

    stats = store.stats()
    assert stats == {"entries": 2, "cve_lookups": 1, "eol_lookups": 1, "stale": 0}


def test_a_known_version_is_answered_without_a_network_call(tmp_path):
    """After the first sweep, enriching a thousand sites must be local."""
    from vg_scanner.intel.sources import Cache, vulnerabilities
    from vg_scanner.intel.store import IntelStore

    store = IntelStore(path=tmp_path / "intel.db")
    store.put(
        "cve", "PHP", "8.0.28", [{"cve": "CVE-2023-3824", "severity": "CRITICAL", "summary": ""}]
    )

    found = vulnerabilities("PHP", "8.0.28", Cache(store=store))
    assert found and found[0].cve == "CVE-2023-3824"
