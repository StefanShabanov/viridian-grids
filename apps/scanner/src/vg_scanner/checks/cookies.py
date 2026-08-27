"""Cookie flags on whatever the homepage sets.

Only cookies we were actually handed are judged - we never log in, so this is a
sample, and the report wording says so.
"""

from __future__ import annotations

from http.cookies import SimpleCookie

from ..context import ScanContext
from ..models import Category, Finding, Severity, Status
from .base import make

C = Category.COOKIES


def run(ctx: ScanContext) -> list[Finding]:
    primary = ctx.primary
    if not primary or not primary.ok:
        return [make("cookies.not_checked", C, Status.SKIPPED)]

    cookies = _parse(primary.set_cookie)
    if not cookies:
        return [make("cookies.none_set", C, Status.INFO)]

    over_https = (primary.scheme or "") == "https"
    missing_secure = [n for n, attrs in cookies.items() if over_https and not attrs["secure"]]
    missing_httponly = [n for n, attrs in cookies.items() if not attrs["httponly"]]
    missing_samesite = [n for n, attrs in cookies.items() if not attrs["samesite"]]

    out: list[Finding] = []
    if missing_secure:
        out.append(
            _flag("cookies.missing_secure", missing_secure, len(cookies), 4, Severity.MEDIUM)
        )
    if missing_httponly:
        out.append(
            _flag("cookies.missing_httponly", missing_httponly, len(cookies), 3, Severity.LOW)
        )
    if missing_samesite:
        out.append(
            _flag("cookies.missing_samesite", missing_samesite, len(cookies), 2, Severity.LOW)
        )
    if not out:
        out.append(make("cookies.flags_ok", C, Status.PASS, params={"count": len(cookies)}))
    return out


def _flag(
    finding_id: str, names: list[str], total: int, weight: int, severity: Severity
) -> Finding:
    shown = ", ".join(names[:4]) + ("..." if len(names) > 4 else "")
    return make(
        finding_id,
        C,
        Status.WARN,
        severity=severity,
        weight=weight,
        params={"count": len(names), "total": total, "names": shown},
        evidence={"cookies": names},
    )


def _parse(headers: list[str]) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for raw in headers:
        jar = SimpleCookie()
        try:
            jar.load(raw)
        except Exception:  # noqa: BLE001 - malformed Set-Cookie is common in the wild
            continue
        for name, morsel in jar.items():
            lowered = raw.lower()
            out[name] = {
                "secure": bool(morsel["secure"]) or "secure" in lowered,
                "httponly": bool(morsel["httponly"]) or "httponly" in lowered,
                "samesite": (morsel.get("samesite") or "") or ("samesite" in lowered),
            }
    return out
