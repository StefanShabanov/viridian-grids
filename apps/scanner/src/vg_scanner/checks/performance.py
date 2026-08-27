"""Initial latency and document weight.

One request from one location is not a performance audit, and the report says so.
It is enough to tell a hotel their homepage takes three seconds to start loading,
which is the conversation we actually want to have.
"""

from __future__ import annotations

from ..context import ScanContext
from ..models import Category, Finding, Severity, Status
from .base import make

C = Category.PERFORMANCE

SLOW_MS = 1200
VERY_SLOW_MS = 3000
LARGE_DOC_KB = 500


def run(ctx: ScanContext) -> list[Finding]:
    primary = ctx.primary
    if not primary or not primary.ok:
        return [make("performance.not_checked", C, Status.SKIPPED)]

    out: list[Finding] = []
    out.extend(_latency(ctx))
    out.extend(_document_size(ctx))
    out.extend(_compression(ctx))
    return out


def _humanize(ms: float) -> str:
    """Rounding to a tenth of a second turned every fast server into "0.0 seconds",
    which reads as a broken measurement rather than a good result."""
    if ms < 1000:
        return f"{int(round(ms))} ms"
    return f"{ms / 1000:.1f} s"


def _latency(ctx: ScanContext) -> list[Finding]:
    ttfb = ctx.primary.ttfb_ms
    if ttfb is None:
        return []
    seconds = round(ttfb / 1000, 1)
    duration = _humanize(ttfb)

    if ttfb >= VERY_SLOW_MS:
        return [
            make(
                "performance.response_very_slow",
                C,
                Status.WARN,
                severity=Severity.MEDIUM,
                weight=8,
                params={"duration": duration, "seconds": seconds, "ms": int(ttfb)},
            )
        ]
    if ttfb >= SLOW_MS:
        return [
            make(
                "performance.response_slow",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=4,
                params={"duration": duration, "seconds": seconds, "ms": int(ttfb)},
            )
        ]
    return [
        make(
            "performance.response_fast",
            C,
            Status.PASS,
            params={"duration": duration, "seconds": seconds, "ms": int(ttfb)},
        )
    ]


def _document_size(ctx: ScanContext) -> list[Finding]:
    size = ctx.primary.body_bytes
    if not size:
        return []
    kb = round(size / 1024)
    if kb > LARGE_DOC_KB:
        return [
            make(
                "performance.document_large",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=2,
                params={"kb": kb},
            )
        ]
    return [make("performance.document_size_ok", C, Status.PASS, params={"kb": kb})]


def _compression(ctx: ScanContext) -> list[Finding]:
    encoding = ctx.primary.header("content-encoding")
    if encoding:
        return [make("performance.compression_ok", C, Status.PASS, params={"encoding": encoding})]
    if ctx.primary.body_bytes < 20_000:
        return []  # too small for compression to matter
    return [
        make(
            "performance.compression_missing",
            C,
            Status.WARN,
            severity=Severity.LOW,
            weight=3,
        )
    ]
