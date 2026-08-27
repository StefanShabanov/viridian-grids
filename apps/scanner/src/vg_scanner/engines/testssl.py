"""testssl.sh - the reference TLS scanner.

GPLv2, run from its official Docker image. This supersedes every TLS check I
wrote by hand, including the legacy-protocol probe I had to verify across two
OpenSSL builds to trust. testssl.sh has been doing this correctly for a decade.

It only ever opens TLS connections to port 443. No content probing, no paths.
It is still tens of seconds per host, so it runs only with --deep.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ..models import Category, Finding, Severity, Status
from .base import Engine, Target, docker_image_present, run_tool

IMAGE = "drwetter/testssl.sh:3.2"

SEVERITY_MAP = {
    "CRITICAL": (Severity.HIGH, 25),
    "HIGH": (Severity.HIGH, 18),
    "MEDIUM": (Severity.MEDIUM, 8),
    "LOW": (Severity.LOW, 3),
    "WARN": (Severity.LOW, 2),
}

# Sections worth surfacing. "pretest" and "grease" are diagnostics about the scan
# itself, not about the site.
SECTIONS = ("protocols", "vulnerabilities", "cipherTests", "fs", "ciphers")

# Certificates stay ours: our expiry logic understands ACME renewal cycles, and
# two sources disagreeing about a certificate in one report helps nobody.
SKIP_PREFIXES = ("cert", "ocsp", "dns_ca", "caa_")

# Hedged checks that fire on the configuration rather than on a demonstrated
# weakness. BREACH triggers on any site with HTTP compression - which put
# "TLS: BREACH ... gzip compression detected" directly underneath our own
# "Compression is enabled" tick on the same page. We cannot substantiate them,
# so we do not raise them.
HEDGE_MARKERS = ("potentially", "likely mitigated", "not vulnerable")


class TestsslEngine(Engine):
    name = "testssl"
    # Protocol support only. Superseding all of "tls." stripped every certificate
    # PASS from the report, so a --deep scan of a perfectly healthy site showed no
    # "Certificate is valid" at all - the report got worse the more we looked.
    supersedes = (
        "tls.protocol_modern",
        "tls.protocol_outdated",
        "tls.legacy_protocols_enabled",
        "tls.legacy_protocols_disabled",
        "tls.legacy_not_tested",
    )
    heavy = True
    default_timeout = 300.0

    def available(self) -> tuple[bool, str]:
        if not docker_image_present(IMAGE):
            return False, f"docker image {IMAGE} not present (run ./bin/setup-engines.sh)"
        return True, ""

    def execute(self, target: Target, timeout: float) -> list[Finding]:
        with tempfile.TemporaryDirectory(prefix="vgscan-testssl-") as workdir:
            out = Path(workdir) / "result.json"
            run_tool(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{workdir}:/data",
                    IMAGE,
                    "--jsonfile-pretty",
                    "/data/result.json",
                    "--quiet",
                    "--color",
                    "0",
                    "--fast",
                    "--protocols",
                    "--vulnerable",
                    "--severity",
                    "LOW",
                    target.domain,
                ],
                timeout=timeout,
            )
            if not out.exists():
                raise RuntimeError("testssl produced no JSON")
            payload = json.loads(out.read_text(encoding="utf-8"))

        results = payload.get("scanResult") or []
        if not results:
            raise RuntimeError("testssl returned an empty scan result")

        return _to_findings(results[0], self.name)


def _to_findings(result: dict, source: str) -> list[Finding]:
    findings: list[Finding] = []
    for section in SECTIONS:
        for item in result.get(section, []):
            if not isinstance(item, dict):
                continue
            severity = str(item.get("severity", "")).upper()
            if severity not in SEVERITY_MAP:
                continue  # OK / INFO: nothing to report
            finding = _one(item, section, severity, source)
            if finding is not None:
                findings.append(finding)
    return findings


def _one(item: dict, section: str, severity: str, source: str) -> Finding | None:
    level, weight = SEVERITY_MAP[severity]
    text = str(item.get("finding", "")).strip()
    identifier = str(item.get("id", "")).strip()
    if not identifier:
        return None

    lowered = text.lower()
    if identifier.lower().startswith(SKIP_PREFIXES):
        return None
    if any(marker in lowered for marker in HEDGE_MARKERS):
        return None

    cve = str(item.get("cve", "")).strip()
    detail = text[:300]
    if cve:
        detail = f"{detail} ({cve.split()[0]})" if detail else cve

    return Finding(
        id=f"testssl.{identifier.lower()}",
        category=Category.TLS,
        status=Status.WARN,
        severity=level,
        weight=weight,
        source=source,
        title=f"TLS: {identifier}",
        detail=detail,
        reference=cve or None,
        params={"section": section, "severity": severity, "finding": text[:120]},
        evidence={"finding": text[:400]},
    )
