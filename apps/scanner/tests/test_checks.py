"""Check behaviour, judged against synthetic contexts."""

from __future__ import annotations

import pytest

from vg_scanner.content import extract
from vg_scanner.models import Severity, Status
from vg_scanner.runner import scan_context

from .conftest import make_context, make_fetch, make_tls


def ids(result, *statuses) -> set[str]:
    findings = result.by_status(*statuses) if statuses else result.findings
    return {f.id for f in findings}


def test_healthy_site_scores_high(healthy_context):
    result = scan_context(healthy_context)
    warned = ids(result, Status.WARN, Status.FAIL)
    assert warned == set(), f"a well-configured site should not warn, got {warned}"
    assert result.score == 100


def test_neglected_site_finds_the_expected_problems(neglected_context):
    result = scan_context(neglected_context)
    warned = ids(result, Status.WARN, Status.FAIL)

    assert "configuration.http_no_redirect" in warned
    assert "http.hsts_missing" in warned
    assert "http.csp_missing" in warned
    assert "performance.response_slow" in warned  # 2.6s: slow, not yet "very slow"
    assert "tls.certificate_expiring_soon" in warned
    assert "tls.legacy_protocols_enabled" in warned
    assert "technology.server_version_exposed" in warned
    assert "configuration.canonical_host_duplicate" in warned
    assert "cookies.missing_secure" in warned


def test_score_stays_proportionate_for_a_working_but_untended_site(neglected_context):
    """The site works. A missing header must not drag it into the red."""
    result = scan_context(neglected_context)
    assert 30 <= result.score <= 75, result.score


def test_a_domain_that_does_not_resolve_is_reported_as_dead():
    """A lapsed domain scored 57/100 - above a live 15/17 prospect at 43 - which
    put dead businesses in the middle of the ranked list."""
    ctx = make_context(
        primary=make_fetch(ok=False, status=None, error="DNS lookup failed"),
        https=make_fetch(ok=False, status=None, error="DNS lookup failed"),
        tls=make_tls(available=False),
    )
    result = scan_context(ctx)

    assert "availability.dns_failure" in ids(result, Status.FAIL)
    assert result.errors == []
    assert result.score <= 15, "nothing answered, so there is no health to report"


def test_a_refused_connection_is_a_site_down_not_a_dead_domain():
    """The domain still resolves, so it is still paid for: the server is down and
    that is the most valuable thing we ever find."""
    ctx = make_context(
        primary=make_fetch(ok=False, status=None, error="connection failed: Connection refused"),
        https=make_fetch(ok=False, status=None, error="connection failed: Connection refused"),
        tls=make_tls(available=False),
    )
    result = scan_context(ctx)

    assert "availability.unreachable" in ids(result, Status.FAIL)
    assert "availability.dns_failure" not in ids(result)
    assert result.reachable is False


def test_an_unreachable_site_ranks_below_a_live_one(healthy_context):
    dead = make_context(
        primary=make_fetch(ok=False, status=None, error="DNS lookup failed"),
        https=make_fetch(ok=False, status=None, error="DNS lookup failed"),
        tls=make_tls(available=False),
    )
    assert scan_context(dead).score < scan_context(healthy_context).score - 50


def test_https_failure_is_reported_when_http_still_answers():
    ctx = make_context(
        primary=make_fetch("http://example.bg"),
        https=make_fetch(ok=False, status=None, error="connection failed"),
        tls=make_tls(available=False),
    )
    result = scan_context(ctx)
    assert "availability.https_unavailable" in ids(result, Status.FAIL)
    # HSTS is meaningless without HTTPS and must be skipped, not counted against them.
    assert "http.hsts_not_applicable" in ids(result, Status.SKIPPED)


def test_expired_certificate_outranks_a_missing_header(neglected_context):
    neglected_context.tls = make_tls(days=-3)
    result = scan_context(neglected_context)
    expired = next(f for f in result.findings if f.id == "tls.certificate_expired")
    header = next(f for f in result.findings if f.id == "http.csp_missing")
    assert expired.weight > header.weight * 5


@pytest.mark.parametrize(
    ("cookie", "expected"),
    [
        (
            "a=1; Path=/",
            {"cookies.missing_secure", "cookies.missing_httponly", "cookies.missing_samesite"},
        ),
        ("a=1; Secure; HttpOnly; SameSite=Lax", set()),
        ("a=1; secure; httponly; samesite=strict", set()),
    ],
)
def test_cookie_flags(healthy_context, cookie, expected):
    healthy_context.primary.set_cookie = [cookie]
    result = scan_context(healthy_context)
    assert (
        ids(result, Status.WARN)
        & {
            "cookies.missing_secure",
            "cookies.missing_httponly",
            "cookies.missing_samesite",
        }
        == expected
    )


def test_redirect_loop_is_a_failure(healthy_context):
    healthy_context.primary.error = "redirect loop"
    result = scan_context(healthy_context)
    assert "configuration.redirect_loop" in ids(result, Status.FAIL)


def test_temporary_https_redirect_is_a_gentle_warning(healthy_context):
    healthy_context.http = make_fetch(
        "http://example.bg", status=302, headers={"location": "https://example.bg/"}
    )
    result = scan_context(healthy_context)
    finding = next(f for f in result.findings if f.id.startswith("configuration.http_redirects"))
    assert finding.status is Status.WARN
    assert finding.weight <= 2


def test_no_plain_http_listener_is_not_a_fault(healthy_context):
    healthy_context.http = make_fetch(ok=False, status=None, error="connection failed")
    result = scan_context(healthy_context)
    assert "configuration.http_closed" in ids(result, Status.INFO)
    assert result.score == 100


# --------------------------------------------------------------- bot protection


def test_a_403_is_treated_as_blocked_not_as_a_broken_site(healthy_context):
    """sofia.bg taught us this one: bot protection is not an outage."""
    healthy_context.primary.status = 403
    healthy_context.robots.status = 403
    healthy_context.sitemap.status = 403
    healthy_context.favicon.status = 403
    result = scan_context(healthy_context)

    assert result.inconclusive
    assert "availability.request_blocked" in ids(result, Status.SKIPPED)
    assert "availability.status_error" not in ids(result)
    # Nothing we could not observe may be reported as missing.
    assert not {
        "configuration.robots_missing",
        "configuration.sitemap_missing",
        "configuration.favicon_missing",
    } & ids(result, Status.WARN)


def test_a_challenge_page_is_detected_by_its_body(healthy_context):
    healthy_context.primary.status = 503
    healthy_context.primary.body = "<html><title>Just a moment...</title>cf-chl</html>"
    assert scan_context(healthy_context).inconclusive


def test_a_genuine_500_is_still_reported_as_an_error(healthy_context):
    healthy_context.primary.status = 500
    result = scan_context(healthy_context)
    assert not result.inconclusive
    assert "availability.status_error" in ids(result, Status.FAIL)


# ------------------------------------------------------- undecodable responses


def test_client_does_not_advertise_encodings_it_cannot_decode():
    """The bug this guards: we asked for Brotli, could not decode it, and every
    content check then silently reported that it had found nothing."""
    from vg_scanner.probe import make_client

    with make_client() as client:
        advertised = client.headers.get("accept-encoding", "")
    assert "br" not in advertised or _brotli_available()


def _brotli_available() -> bool:
    try:
        import brotli  # noqa: F401
    except ImportError:
        try:
            import brotlicffi  # noqa: F401
        except ImportError:
            return False
    return True


def test_an_undecodable_body_is_never_reported_as_absence(healthy_context):
    healthy_context.primary.body = "�" * 500
    healthy_context.primary.body_decoded = False
    healthy_context.facts = extract(healthy_context.primary)

    result = scan_context(healthy_context)
    assert "technology.not_checked" in ids(result, Status.SKIPPED)
    # Absence we never established must not be reported as a finding.
    assert "technology.not_responsive" not in ids(result)
    assert "technology.cms_unknown" not in ids(result)


@pytest.mark.parametrize(
    ("body", "readable"),
    [
        ("<html>fine</html>", True),
        ("", True),
        ("�" * 200, False),
        ("mostly fine text with one � in it", True),
    ],
)
def test_readable_text_detection(body, readable):
    from vg_scanner.probe import _is_readable_text

    assert _is_readable_text(body) is readable


def test_untestable_legacy_tls_is_reported_as_unknown_not_as_safe(healthy_context):
    """If the local OpenSSL refuses to try TLS 1.0, we must not claim it is off."""
    healthy_context.tls = make_tls(legacy=[])
    healthy_context.tls.legacy_tested = False
    result = scan_context(healthy_context)

    assert "tls.legacy_not_tested" in ids(result, Status.SKIPPED)
    assert "tls.legacy_protocols_disabled" not in ids(result)


# ------------------------------------------------------- certificate lifetimes


def _cert(days_remaining: int, lifetime_days: int):
    from datetime import UTC, datetime, timedelta

    info = make_tls(days=days_remaining)
    info.not_after = datetime.now(UTC) + timedelta(days=days_remaining)
    info.not_before = info.not_after - timedelta(days=lifetime_days)
    return info


def test_short_lived_certificate_is_not_nagged_about(healthy_context):
    """A 90-day ACME certificate at 33 days is mid-renewal-cycle, not a problem.
    Warning about it tells the prospect we do not understand their setup."""
    healthy_context.tls = _cert(days_remaining=33, lifetime_days=89)
    result = scan_context(healthy_context)

    assert "tls.certificate_auto_renewing" in ids(result, Status.PASS)
    assert "tls.certificate_expiring_soon" not in ids(result)


def test_short_lived_certificate_close_to_expiry_means_renewal_broke(healthy_context):
    healthy_context.tls = _cert(days_remaining=4, lifetime_days=89)
    result = scan_context(healthy_context)

    finding = next(f for f in result.findings if f.id == "tls.certificate_renewal_failing")
    assert finding.status is Status.WARN
    assert finding.severity is Severity.HIGH


def test_year_long_certificate_still_warns_early(healthy_context):
    """Nobody auto-renews a 392-day certificate, so 34 days out is worth raising."""
    healthy_context.tls = _cert(days_remaining=34, lifetime_days=392)
    result = scan_context(healthy_context)

    assert "tls.certificate_expiring_soon" in ids(result, Status.WARN)


# ------------------------------------------------- absence must be established


def test_a_server_error_is_not_evidence_a_file_is_missing(healthy_context):
    """We told a prospect "Sitemap is missing (HTTP 500)". It may exist perfectly
    well; their server was erroring."""
    healthy_context.sitemap.status = 500
    healthy_context.favicon.status = None
    healthy_context.favicon.ok = False
    result = scan_context(healthy_context)

    assert "configuration.well_known_unavailable" in ids(result, Status.SKIPPED)
    assert "configuration.sitemap_missing" not in ids(result)
    assert "configuration.favicon_missing" not in ids(result)


def test_a_404_is_still_a_genuine_absence(healthy_context):
    healthy_context.sitemap.status = 404
    result = scan_context(healthy_context)
    assert "configuration.sitemap_missing" in ids(result, Status.WARN)


def test_erroring_plain_http_is_reported_as_an_error_not_as_plaintext(healthy_context):
    healthy_context.http = make_fetch("http://example.bg", status=500)
    result = scan_context(healthy_context)

    assert "configuration.http_error" in ids(result, Status.WARN)
    assert "configuration.http_no_redirect" not in ids(result)


# ------------------------------------------------------------------- favicons


def test_a_declared_favicon_counts_even_when_the_legacy_path_is_404(healthy_context):
    """angro.bg scored 98/100 and one of its two findings was a missing favicon,
    while its HTML pointed straight at one. Browsers use the link tag."""
    body = (
        "<html><head><title>Shop</title>"
        '<meta name="viewport" content="width=device-width">'
        '<link rel="icon" type="image/png" href="/media/favicon.png">'
        "</head><body>hi</body></html>"
    )
    healthy_context.primary.body = body
    healthy_context.facts = extract(healthy_context.primary)
    healthy_context.favicon = make_fetch("https://example.bg/favicon.ico", status=404)

    result = scan_context(healthy_context)
    assert "configuration.favicon_present" in ids(result, Status.PASS)
    assert "configuration.favicon_missing" not in ids(result)


def test_shortcut_icon_and_apple_touch_icon_both_count():
    from vg_scanner.content import extract as ex

    for rel in ("shortcut icon", "apple-touch-icon", "ICON"):
        body = f'<html><head><link rel="{rel}" href="/a.png"></head><body></body></html>'
        assert ex(make_fetch(body=body)).favicon_declared, rel


def test_no_declaration_and_no_file_is_still_reported_missing(healthy_context):
    healthy_context.favicon = make_fetch("https://example.bg/favicon.ico", status=404)
    result = scan_context(healthy_context)
    assert "configuration.favicon_missing" in ids(result, Status.WARN)


@pytest.mark.parametrize(
    ("ttfb_ms", "expected"),
    [(43.0, "43 ms"), (180.4, "180 ms"), (999.0, "999 ms"), (1000.0, "1.0 s"), (2600.0, "2.6 s")],
)
def test_fast_responses_are_not_reported_as_zero_seconds(ttfb_ms, expected):
    """Rounding to a tenth of a second printed "First response in 0.0 seconds" for
    every quick server, which reads as a broken measurement."""
    from vg_scanner.checks.performance import _humanize

    assert _humanize(ttfb_ms) == expected


def test_latency_detail_renders_the_humanized_duration(healthy_context):
    from vg_scanner.catalog import resolve

    healthy_context.primary.ttfb_ms = 87.0
    result = scan_context(healthy_context)
    finding = next(f for f in result.findings if f.id == "performance.response_fast")
    _, detail = resolve(finding, "en")
    assert "87 ms" in detail
    assert "0.0" not in detail
