"""nuclei - powerful, and not usable on strangers.

Measured against one real prospect, `-t http/technologies/` issued **1,040 HTTP
requests** at 9 RPS, 113 of which errored because they were probes for paths that
do not exist. That is directory probing and aggressive crawling. Pointed at a
dentist on shared hosting who has never heard of us, it is precisely what MVP.md
forbids, and a good way to be firewalled or complained about.

So nuclei is gated: it refuses to run unless the target is explicitly marked
authorized. That is the same boundary MVP.md draws around ZAP's active scanner,
and it is the boundary that lets us say "non-intrusive" and mean it.

Once a customer signs the authorization, this becomes one of the most valuable
things we own: 243 WordPress-plugin templates with version extraction, plus the
CVE templates that turn "you run plugin X 2.1" into "plugin X 2.1 has a known
vulnerability".
"""

from __future__ import annotations

import json

from ..models import Category, Finding, Severity, Status
from .base import Engine, Target, run_tool, tool_path

SEVERITY_MAP = {
    "critical": (Severity.HIGH, 30),
    "high": (Severity.HIGH, 20),
    "medium": (Severity.MEDIUM, 10),
    "low": (Severity.LOW, 4),
    "info": (Severity.INFO, 0),
}

# Never run these, even with authorization, without a separate explicit decision.
EXCLUDED_TAGS = "intrusive,fuzz,dos,sqli,xss,rce,lfi,ssrf,brute-force,bruteforce,deserialization"


class NucleiEngine(Engine):
    name = "nuclei"
    supersedes = ()
    heavy = True
    default_timeout = 900.0
    requires_authorization = True

    def available(self) -> tuple[bool, str]:
        if tool_path("nuclei") is None:
            return False, "not installed (run ./bin/setup-engines.sh)"
        return True, ""

    def run(self, target: Target, timeout: float | None = None):
        from .base import EngineResult

        if not target.authorized:
            return EngineResult(
                self.name,
                "unavailable",
                detail="needs written authorization: this scan sends ~1000 requests",
            )
        return super().run(target, timeout)

    def execute(self, target: Target, timeout: float) -> list[Finding]:
        binary = tool_path("nuclei")
        done = run_tool(
            [
                str(binary),
                "-u",
                target.url,
                "-jsonl",
                "-silent",
                "-no-interactsh",
                "-disable-update-check",
                "-etags",
                EXCLUDED_TAGS,
                "-timeout",
                "10",
                "-retries",
                "1",
                "-rate-limit",
                "20",
                "-t",
                "http/technologies/",
                "-t",
                "http/cves/",
                "-t",
                "ssl/",
            ],
            timeout=timeout,
        )
        return _parse(done.stdout, self.name)


def _parse(stdout: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue

        info = row.get("info", {})
        severity = str(info.get("severity", "info")).lower()
        level, weight = SEVERITY_MAP.get(severity, (Severity.INFO, 0))
        extracted = row.get("extracted-results") or []
        version = extracted[0] if extracted else ""

        name = info.get("name") or row.get("template-id", "finding")
        title = f"{name} {version}".strip()
        references = info.get("reference") or []

        findings.append(
            Finding(
                id=f"nuclei.{row.get('template-id', 'unknown')}",
                category=Category.TECHNOLOGY,
                status=Status.INFO if weight == 0 else Status.WARN,
                severity=level,
                weight=weight,
                source=source,
                title=title[:160],
                detail=str(info.get("description", "")).strip()[:300],
                reference=references[0] if references else None,
                params={"severity": severity, "version": version},
                evidence={"matched": row.get("matched-at", "")},
            )
        )
    return findings
