"""External scanning engines.

The plan was always for this scanner to be an aggregator, not a scanning engine:
"write some software yourself, but not the scanning engines". This package is
that. Each engine wraps a proven tool, runs it in a safe configuration, and
normalizes its output into our Finding model so one report can be assembled from
all of them.

An engine that is not installed reports itself unavailable and the scan carries
on. Nothing here is allowed to be required.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from ..models import Finding


def engines_dir() -> Path:
    """Where ./bin/setup-engines.sh put the tools."""
    override = os.environ.get("VG_ENGINES_DIR")
    if override:
        return Path(override)
    # src/vg_scanner/engines/base.py -> apps/scanner/.engines
    return Path(__file__).resolve().parents[3] / ".engines"


def tool_path(name: str) -> Path | None:
    candidate = engines_dir() / "bin" / name
    if candidate.exists():
        return candidate
    found = shutil.which(name)
    return Path(found) if found else None


def docker_image_present(image: str) -> bool:
    if not shutil.which("docker"):
        return False
    try:
        done = subprocess.run(
            ["docker", "image", "inspect", image],
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


@dataclass
class Target:
    domain: str
    url: str
    authorized: bool = False


@dataclass
class EngineResult:
    """What one engine contributed, and whether it actually ran."""

    name: str
    status: str = "ok"  # ok | unavailable | error | timeout
    findings: list[Finding] = field(default_factory=list)
    detail: str = ""

    @property
    def ran(self) -> bool:
        return self.status == "ok"


class Engine:
    """Base class. Subclasses override `available` and `execute`."""

    name: str = "engine"
    # Finding-id prefixes this engine replaces when it runs successfully, so our
    # own approximations do not appear alongside the authoritative answer.
    supersedes: tuple[str, ...] = ()
    # Heavy engines take tens of seconds and only run with --deep.
    heavy: bool = False
    default_timeout: float = 60.0

    def available(self) -> tuple[bool, str]:
        return True, ""

    def supersedes_for(self, findings: list[Finding]) -> tuple[str, ...]:
        """What this engine replaces, given what it actually found.

        Static `supersedes` is the default. An engine that answered a question
        only sometimes must not silence our own answer on the runs where it
        stayed quiet - that would lose a real finding rather than dedupe one.
        """
        return self.supersedes

    def execute(self, target: Target, timeout: float) -> list[Finding]:
        raise NotImplementedError

    def run(self, target: Target, timeout: float | None = None) -> EngineResult:
        ok, why = self.available()
        if not ok:
            return EngineResult(self.name, "unavailable", detail=why)
        try:
            findings = self.execute(target, timeout or self.default_timeout)
        except subprocess.TimeoutExpired:
            return EngineResult(self.name, "timeout", detail="tool did not finish in time")
        except Exception as exc:  # noqa: BLE001 - an engine failing is data, not a crash
            return EngineResult(self.name, "error", detail=f"{type(exc).__name__}: {exc}")
        return EngineResult(self.name, "ok", findings=findings)


def run_tool(
    command: list[str], timeout: float, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    """Run an external tool with no shell, capturing everything."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
        check=False,
    )
