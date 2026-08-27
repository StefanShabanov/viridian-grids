"""Shared helper for building findings.

Checks emit an id plus params - never prose. The message catalog turns that into
English or Bulgarian at render time, which is what keeps the two reports in sync.
"""

from __future__ import annotations

from typing import Any

from ..models import Category, Finding, Severity, Status


def make(
    finding_id: str,
    category: Category,
    status: Status,
    *,
    severity: Severity = Severity.INFO,
    weight: int = 0,
    params: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        status=status,
        severity=severity,
        weight=weight,
        params=params or {},
        evidence=evidence or {},
    )
