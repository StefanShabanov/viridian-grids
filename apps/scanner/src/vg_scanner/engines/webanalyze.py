"""webanalyze - Wappalyzer-style fingerprinting, done properly.

MIT licensed, and the maintained fork of the Wappalyzer fingerprint set after
Wappalyzer itself went commercial. ~2MB of community-maintained signatures
against my handful of hand-written regexes: this supersedes our own detection.

Passive: it reads the homepage. `-crawl 0` keeps it to that one request.
"""

from __future__ import annotations

import json

from ..models import Category, Finding, Severity, Status
from .base import Engine, Target, engines_dir, run_tool, tool_path

# Categories whose presence tells us something about the business, not the stack.
COMMERCE_CATEGORIES = {"Ecommerce", "Payment processors", "Shopping carts"}
CMS_CATEGORIES = {"CMS", "Blogs", "Static site generator"}


class WebanalyzeEngine(Engine):
    name = "webanalyze"
    supersedes = ("technology.cms_detected", "technology.cms_unknown")
    heavy = False
    default_timeout = 60.0

    def supersedes_for(self, findings: list[Finding]) -> tuple[str, ...]:
        # Only claim the version question when we actually produced a version:
        # dental-ilina.com reported WordPress 6.1.12 twice and was docked for it
        # twice, once by our check and once by this engine.
        extra = ()
        if any(f.id.startswith("webanalyze.version.") for f in findings):
            extra = ("technology.cms_version_exposed",)
        return self.supersedes + extra

    def available(self) -> tuple[bool, str]:
        if tool_path("webanalyze") is None:
            return False, "not installed (run ./bin/setup-engines.sh)"
        if not (engines_dir() / "technologies.json").exists():
            return False, "technologies.json missing (run ./bin/setup-engines.sh)"
        return True, ""

    def execute(self, target: Target, timeout: float) -> list[Finding]:
        binary = tool_path("webanalyze")
        done = run_tool(
            [
                str(binary),
                "-host",
                target.url,
                "-output",
                "json",
                "-crawl",
                "0",
                "-apps",
                str(engines_dir() / "technologies.json"),
            ],
            timeout=timeout,
            cwd=engines_dir(),
        )
        payload = _first_json_object(done.stdout)
        if payload is None:
            raise RuntimeError(done.stderr.strip()[:200] or "no JSON from webanalyze")

        findings: list[Finding] = []
        detected: list[tuple[str, str, list[str]]] = []
        for match in payload.get("matches", []):
            name = match.get("app_name") or ""
            if not name:
                continue
            version = (match.get("version") or "").strip()
            categories = match.get("app", {}).get("category_names") or []
            detected.append((name, version, categories))

        if not detected:
            return findings

        findings.append(
            Finding(
                id="webanalyze.stack",
                category=Category.TECHNOLOGY,
                status=Status.INFO,
                source=self.name,
                title="Technology detected",
                detail=", ".join(
                    f"{name} {version}".strip() for name, version, _ in sorted(detected)
                )[:400],
                evidence={"count": len(detected)},
            )
        )

        # Name the platform explicitly. The stack line lists everything, which is
        # no use as a CRM column: "Website platform" wants one answer.
        platform = _platform(detected)
        if platform:
            name, version = platform
            findings.append(
                Finding(
                    id="webanalyze.cms",
                    category=Category.TECHNOLOGY,
                    status=Status.INFO,
                    source=self.name,
                    title=f"Built on {name} {version}".strip(),
                    detail=f"Detected from the public page source. Version {version}."
                    if version
                    else "Detected from the public page source.",
                    params={"name": name, "version": version},
                )
            )

        # A published version number is the single most useful thing here: it is
        # specific, verifiable, and it is what a maintenance conversation is about.
        versioned = [(n, v) for n, v, _ in detected if v]
        for name, version in versioned[:6]:
            findings.append(
                Finding(
                    id=f"webanalyze.version.{name.lower().replace(' ', '_')}",
                    category=Category.TECHNOLOGY,
                    status=Status.WARN,
                    severity=Severity.LOW,
                    weight=2,
                    source=self.name,
                    title=f"{name} version is published: {version}",
                    detail=(
                        f"The page tells every visitor it runs {name} {version}, "
                        "which says exactly which updates are outstanding."
                    ),
                    params={"name": name, "version": version},
                )
            )

        return findings

    @staticmethod
    def describes_shop(findings: list[Finding]) -> bool:
        for finding in findings:
            if finding.id == "webanalyze.stack":
                return any(
                    c in (finding.detail or "") for c in ("WooCommerce", "Magento", "Shopify")
                )
        return False


def _platform(detected: list[tuple[str, str, list[str]]]) -> tuple[str, str] | None:
    """Pick the one technology that answers "what is this site built on?"."""
    for wanted in (CMS_CATEGORIES, COMMERCE_CATEGORIES):
        for name, version, categories in detected:
            if wanted & set(categories):
                return name, version
    return None


def _first_json_object(stdout: str) -> dict | None:
    """webanalyze prints a blank line before its JSON."""
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None
