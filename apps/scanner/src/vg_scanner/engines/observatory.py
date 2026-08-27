"""Mozilla HTTP Observatory - the authoritative header assessment.

Passive and third-party: Mozilla's infrastructure fetches the site, the way any
online checker does. Nothing of ours touches the prospect for this.

This supersedes our own header weights, which were my judgement calls. Observatory
has a published, versioned scoring algorithm that people already trust.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ..models import Category, Finding, Severity, Status
from .base import Engine, Target

API = "https://observatory-api.mdn.mozilla.net/api/v2/scan"

# Observatory grade -> what we deduct. Deliberately gentle: an F here means
# "no security headers", which is the norm for a Bulgarian SME, not a crisis.
GRADE_WEIGHT = {
    "A+": 0,
    "A": 0,
    "A-": 0,
    "B+": 2,
    "B": 3,
    "B-": 4,
    "C+": 5,
    "C": 6,
    "C-": 7,
    "D+": 8,
    "D": 9,
    "D-": 10,
    "F": 12,
}


class ObservatoryEngine(Engine):
    name = "observatory"
    supersedes = ()  # our header checks name the specific gaps; this grades them
    heavy = False
    default_timeout = 45.0

    def execute(self, target: Target, timeout: float) -> list[Finding]:
        request = urllib.request.Request(
            f"{API}?host={target.domain}",
            method="POST",
            headers={"User-Agent": "ViridianGrids-HealthCheck/0.1", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"observatory returned HTTP {exc.code}") from exc

        if payload.get("error"):
            raise RuntimeError(str(payload["error"]))

        grade = payload.get("grade")
        if not grade:
            return []

        score = payload.get("score", 0)
        passed = payload.get("tests_passed", 0)
        total = payload.get("tests_quantity", 0)
        weight = GRADE_WEIGHT.get(grade, 6)
        good = weight == 0

        return [
            Finding(
                id="observatory.grade",
                category=Category.HTTP,
                status=Status.PASS if good else Status.WARN,
                severity=Severity.INFO if good else Severity.LOW,
                weight=weight,
                source=self.name,
                title=f"Mozilla Observatory grade: {grade}",
                detail=(
                    f"Independent header assessment by Mozilla: {passed} of {total} checks passed "
                    f"(score {score})."
                ),
                reference=payload.get("details_url"),
                params={"grade": grade, "score": score},
                evidence={"tests_passed": passed, "tests_quantity": total},
            )
        ]
