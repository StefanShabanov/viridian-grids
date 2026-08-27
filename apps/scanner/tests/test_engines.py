"""The engine tier boundary.

These are the tests that keep the promise printed at the bottom of every report.
Getting this wrong is not a bug, it is pointing an attack tool at a stranger.
"""

from __future__ import annotations

import pytest

from vg_scanner.engines import AUTHORIZED, PROSPECTING, Target, select
from vg_scanner.engines.nuclei import NucleiEngine, _parse
from vg_scanner.engines.observatory import ObservatoryEngine
from vg_scanner.engines.testssl import _to_findings
from vg_scanner.models import Severity, Status

# ------------------------------------------------------------- the tier boundary


def test_nuclei_refuses_to_run_without_authorization():
    """Measured at 1040 requests against one prospect. It never runs by default."""
    engine = NucleiEngine()
    result = engine.run(Target(domain="example.bg", url="https://example.bg", authorized=False))

    assert result.status == "unavailable"
    assert not result.findings
    assert "authorization" in result.detail


def test_default_selection_contains_no_intrusive_engine():
    for engine in select(deep=True, authorized=False):
        assert not getattr(engine, "requires_authorization", False), engine.name


def test_authorized_engines_are_never_reachable_by_asking_for_them_by_name():
    """--engines nuclei must not be a way around the gate."""
    chosen = select(deep=True, authorized=False, only=["nuclei"])
    assert chosen == []


def test_authorization_alone_does_not_enable_heavy_engines_without_deep():
    names = {e.name for e in select(deep=False, authorized=True)}
    assert "nuclei" not in names, "nuclei is heavy as well as authorized-only"


def test_authorized_and_deep_together_enable_it():
    names = {e.name for e in select(deep=True, authorized=True)}
    assert "nuclei" in names


def test_prospecting_engines_are_all_passive():
    assert {e.name for e in PROSPECTING} == {"observatory", "webanalyze", "testssl"}
    assert {e.name for e in AUTHORIZED} == {"nuclei"}


# ----------------------------------------------------------------- normalization


def test_testssl_hedged_findings_are_dropped():
    """testssl says "potentially VULNERABLE" when a precondition holds but nothing
    was demonstrated. BREACH fires on any site with HTTP compression, so it landed
    directly under our own "Compression is enabled" tick. We cannot substantiate
    it, so we do not raise it."""
    section = {
        "vulnerabilities": [
            {
                "id": "BREACH",
                "severity": "MEDIUM",
                "finding": "potentially VULNERABLE, gzip HTTP compression detected",
                "cve": "CVE-2013-3587",
            },
            {
                "id": "ROBOT",
                "severity": "HIGH",
                "finding": "VULNERABLE, Bleichenbacher attack possible",
            },
        ]
    }
    findings = {f.id: f for f in _to_findings(section, "testssl")}

    assert "testssl.breach" not in findings
    robot = findings["testssl.robot"]
    assert robot.severity is Severity.HIGH
    assert robot.weight > 0


def test_testssl_does_not_second_guess_our_certificate_logic():
    """Our expiry check understands ACME renewal cycles. Two sources arguing about
    one certificate in a single report helps nobody."""
    section = {
        "serverDefaults": [
            {"id": "cert_expirationStatus", "severity": "MEDIUM", "finding": "expires < 60 days"}
        ],
        "protocols": [{"id": "TLS1", "severity": "LOW", "finding": "offered (deprecated)"}],
    }
    ids = {f.id for f in _to_findings(section, "testssl")}
    assert ids == {"testssl.tls1"}


def test_testssl_leaves_our_certificate_passes_in_the_report():
    """Superseding all of "tls." stripped every "Certificate is valid" line, so a
    deep scan of a healthy site looked emptier than a shallow one."""
    from vg_scanner.engines.testssl import TestsslEngine

    superseded = TestsslEngine().supersedes
    assert not any(p == "tls." for p in superseded)
    assert all(p.startswith("tls.protocol") or p.startswith("tls.legacy") for p in superseded)


def test_testssl_ok_results_produce_no_findings():
    section = {"protocols": [{"id": "TLS1_2", "severity": "OK", "finding": "offered"}]}
    assert _to_findings(section, "testssl") == []


def test_nuclei_output_is_normalized_with_version_and_reference():
    line = (
        '{"template-id":"wordpress-slider-revolution","info":{"name":"Slider Revolution",'
        '"severity":"info","reference":["https://example.test/x"],"description":"Detected."},'
        '"extracted-results":["6.5.24"],"matched-at":"https://example.bg"}'
    )
    finding = _parse(line, "nuclei")[0]

    assert finding.id == "nuclei.wordpress-slider-revolution"
    assert "6.5.24" in finding.title
    assert finding.source == "nuclei"
    assert finding.status is Status.INFO
    assert finding.weight == 0


def test_malformed_engine_output_is_ignored_rather_than_crashing():
    assert _parse("not json\n{broken\n", "nuclei") == []


# ---------------------------------------------------------------------- grading


@pytest.mark.parametrize(
    ("grade", "expect_pass"),
    [("A+", True), ("A", True), ("B", False), ("F", False)],
)
def test_observatory_grade_becomes_a_proportionate_finding(grade, expect_pass, monkeypatch):
    engine = ObservatoryEngine()
    payload = {
        "grade": grade,
        "score": 0,
        "tests_passed": 5,
        "tests_quantity": 10,
        "details_url": "https://example.test",
    }
    monkeypatch.setattr(engine, "execute", lambda t, timeout: _fake_observatory(engine, payload))
    findings = engine.run(Target("example.bg", "https://example.bg")).findings

    assert len(findings) == 1
    finding = findings[0]
    assert (finding.status is Status.PASS) is expect_pass
    # Even the worst grade stays a nudge: no security headers is the SME norm.
    assert finding.weight <= 12


def _fake_observatory(engine, payload):
    from vg_scanner.engines.observatory import GRADE_WEIGHT
    from vg_scanner.models import Category, Finding

    w = GRADE_WEIGHT[payload["grade"]]
    return [
        Finding(
            id="observatory.grade",
            category=Category.HTTP,
            status=Status.PASS if w == 0 else Status.WARN,
            weight=w,
            source="observatory",
            title=f"Mozilla Observatory grade: {payload['grade']}",
        )
    ]
