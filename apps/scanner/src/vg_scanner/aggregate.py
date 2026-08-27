"""Aggregation across many scans.

This is the calibration tool. One scan tells you about one site; a hundred scans
tell you whether the weights are sane, which findings are so common they are
worthless as a talking point, and which verticals are worth the outreach.

Pure functions over saved ScanResults - no network, so it can be re-run against a
stored corpus every time a weight changes.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median

from .models import ScanResult, Status
from .scoring import band


@dataclass
class Aggregate:
    total: int = 0
    blocked: int = 0
    scores: list[int] = field(default_factory=list)
    bands: Counter[str] = field(default_factory=Counter)
    findings: Counter[str] = field(default_factory=Counter)
    platforms: Counter[str] = field(default_factory=Counter)
    signals: Counter[str] = field(default_factory=Counter)
    prospects: list[tuple[int, int, str]] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)

    @property
    def usable(self) -> int:
        """Scans we would actually be willing to send."""
        return self.total - self.blocked

    def score_summary(self) -> tuple[int, int, int]:
        if not self.scores:
            return (0, 0, 0)
        return (min(self.scores), int(median(self.scores)), max(self.scores))

    def frequency(self, finding_id: str) -> float:
        """Share of scanned sites carrying this finding, 0.0-1.0."""
        return self.findings[finding_id] / self.total if self.total else 0.0


def aggregate(results: list[ScanResult]) -> Aggregate:
    agg = Aggregate(total=len(results))
    for result in results:
        if result.inconclusive:
            agg.blocked += 1
        else:
            # A blocked scan's score is not a measurement, so it must not skew the
            # distribution we tune weights against.
            agg.scores.append(result.score)
            agg.bands[band(result.score)] += 1

        for finding in result.by_status(Status.WARN, Status.FAIL):
            agg.findings[finding.id] += 1

        agg.platforms[_platform(result)] += 1
        for signal in result.prospect_score.signals:
            agg.signals[signal.name] += 1
        agg.prospects.append((result.prospect_score.total, result.score, result.domain))
        for error in result.errors:
            agg.errors.append((result.domain, error))

    agg.prospects.sort(key=lambda row: (-row[0], row[1]))
    return agg


# Whichever source answered. webanalyze supersedes our own CMS finding, so reading
# only ours reported "50 of 50 none detected" on a corpus where it found WordPress
# on eleven of them.
_PLATFORM_IDS = ("webanalyze.cms", "technology.cms_detected")


def _platform(result: ScanResult) -> str:
    by_id = {f.id: f for f in result.findings}
    for finding_id in _PLATFORM_IDS:
        finding = by_id.get(finding_id)
        if finding and finding.params.get("name"):
            return str(finding.params["name"])
    return "none detected"


def load_results(source: Path) -> list[ScanResult]:
    """Read every scan JSON in a directory (or one file). Bad files are skipped."""
    paths = sorted(source.glob("*.json")) if source.is_dir() else [source]
    results: list[ScanResult] = []
    for path in paths:
        try:
            results.append(ScanResult.model_validate_json(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return results
