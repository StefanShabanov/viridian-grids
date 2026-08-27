"""Orchestration: gather once, run every check, score, return a ScanResult.

A check that raises is recorded as an error and the scan continues. One broken
check must never cost us a prospect report.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from . import __version__
from .checks import CHECKS
from .context import ScanContext, gather
from .engines import Target, select
from .models import Finding, ScanResult
from .probe import DEFAULT_TIMEOUT, normalize_domain
from .scoring import prospect_score, score


def scan(
    domain: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    authorized: bool = False,
    check_aux: bool = True,
    check_legacy_tls: bool = True,
    deep: bool = False,
    engines: list[str] | None = None,
) -> ScanResult:
    host = normalize_domain(domain)
    started = time.perf_counter()

    ctx = gather(
        host,
        timeout=timeout,
        authorized=authorized,
        check_aux=check_aux,
        check_legacy_tls=check_legacy_tls,
    )
    result = ScanResult(
        domain=host,
        url=ctx.url,
        final_url=ctx.primary.final_url if ctx.primary else None,
        scanned_at=datetime.now(UTC),
        scanner_version=__version__,
        authorized=authorized,
        errors=list(ctx.errors),
    )

    for module in CHECKS:
        try:
            result.findings.extend(module.run(ctx))
        except Exception as exc:  # noqa: BLE001 - one bad check must not lose the scan
            name = module.__name__.rsplit(".", 1)[-1]
            result.errors.append(f"check {name} failed: {type(exc).__name__}: {exc}")

    _apply_engines(result, ctx, deep=deep, authorized=authorized, only=engines)

    result.score = score(result.findings)
    result.reachable = ctx.reachable
    result.inconclusive = _is_inconclusive(result)
    result.prospect_score = prospect_score(ctx, result.findings)
    result.duration_ms = int((time.perf_counter() - started) * 1000)
    return result


def _apply_engines(
    result: ScanResult,
    ctx: ScanContext,
    *,
    deep: bool,
    authorized: bool,
    only: list[str] | None,
) -> None:
    """Run the external engines and let them replace our own approximations.

    Where a proven tool covers the same ground as one of my hand-written checks,
    the tool wins and my version is dropped - otherwise the report would carry two
    answers to the same question, one of them worse.
    """
    chosen = select(deep=deep, authorized=authorized, only=only)
    if not chosen or not ctx.reachable:
        for engine in chosen:
            result.engines[engine.name] = "skipped"
        return

    target = Target(domain=ctx.domain, url=ctx.origin, authorized=authorized)
    with ThreadPoolExecutor(max_workers=min(4, len(chosen))) as pool:
        outcomes = list(pool.map(lambda e: e.run(target), chosen))

    superseded: tuple[str, ...] = ()
    for engine, outcome in zip(chosen, outcomes, strict=True):
        result.engines[engine.name] = outcome.status
        if outcome.status != "ok":
            if outcome.detail:
                result.errors.append(f"{engine.name}: {outcome.status} - {outcome.detail}")
            continue
        superseded += engine.supersedes_for(outcome.findings)
        result.findings.extend(outcome.findings)

    if superseded:
        result.findings = [
            finding
            for finding in result.findings
            if finding.source != "vg" or not _superseded(finding, superseded)
        ]


def _superseded(finding: Finding, prefixes: tuple[str, ...]) -> bool:
    return any(finding.id.startswith(prefix) for prefix in prefixes)


def scan_context(ctx: ScanContext) -> ScanResult:
    """Score an already-gathered context. Used by tests and by any future worker
    that wants to re-score a stored scan without touching the network."""
    result = ScanResult(
        domain=ctx.domain,
        url=ctx.url,
        final_url=ctx.primary.final_url if ctx.primary else None,
        scanned_at=datetime.now(UTC),
        authorized=ctx.authorized,
        errors=list(ctx.errors),
    )
    for module in CHECKS:
        try:
            result.findings.extend(module.run(ctx))
        except Exception as exc:  # noqa: BLE001
            name = module.__name__.rsplit(".", 1)[-1]
            result.errors.append(f"check {name} failed: {type(exc).__name__}: {exc}")
    result.score = score(result.findings)
    result.reachable = ctx.reachable
    result.inconclusive = _is_inconclusive(result)
    result.prospect_score = prospect_score(ctx, result.findings)
    return result


def _is_inconclusive(result: ScanResult) -> bool:
    """Did the site refuse us rather than answer? Then nothing here is safe to send."""
    return any(f.id == "availability.request_blocked" for f in result.findings)
