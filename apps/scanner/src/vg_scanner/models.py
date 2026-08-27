"""Normalized data model. Everything the scanner produces is one of these.

The report renders from `ScanResult`; nothing renders from the checks directly.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from . import __version__


class Category(StrEnum):
    AVAILABILITY = "availability"
    TLS = "tls"
    HTTP = "http"
    COOKIES = "cookies"
    TECHNOLOGY = "technology"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"


class Status(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    INFO = "info"
    SKIPPED = "skipped"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Finding(BaseModel):
    """One observation, from one of our checks or from an external engine.

    Our own checks produce an id plus params and never prose, so the catalog can
    render them in either language. External engines (testssl.sh, nuclei, ...)
    bring their own English wording, which lands in `title`/`detail` and is used
    when the catalog has nothing for the id.
    """

    id: str
    category: Category
    status: Status
    severity: Severity = Severity.INFO
    weight: int = 0
    source: str = "vg"
    title: str | None = None
    detail: str | None = None
    reference: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)

    @property
    def deducts(self) -> bool:
        return self.status in (Status.WARN, Status.FAIL)


class ProspectSignal(BaseModel):
    name: str
    points: int


class ProspectScore(BaseModel):
    """Sales-side ranking: is this company worth 15 minutes of personal outreach?"""

    total: int = 0
    max: int = 15
    signals: list[ProspectSignal] = Field(default_factory=list)


class ScanResult(BaseModel):
    domain: str
    url: str
    final_url: str | None = None
    scanned_at: datetime
    scanner_version: str = __version__
    duration_ms: int = 0
    authorized: bool = False
    score: int = 0
    reachable: bool = True
    inconclusive: bool = False
    engines: dict[str, str] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)
    prospect_score: ProspectScore = Field(default_factory=ProspectScore)
    errors: list[str] = Field(default_factory=list)

    def by_status(self, *statuses: Status) -> list[Finding]:
        return [f for f in self.findings if f.status in statuses]
