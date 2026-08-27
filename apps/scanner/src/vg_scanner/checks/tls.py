"""Certificate validity, expiry and protocol configuration.

Expiry thresholds are deliberately generous: 45 days is a nudge, not an alarm.
A missing certificate renewal is the single most common thing this service is
actually bought to prevent, so it is worth flagging early and calmly.
"""

from __future__ import annotations

from ..context import ScanContext
from ..models import Category, Finding, Severity, Status
from .base import make

C = Category.TLS

# Browsers hard-block an untrusted certificate, so visitors simply cannot get in.
# That is worth more than any header, and less than the site being down entirely.
UNTRUSTED_WEIGHT = 35

EXPIRY_WARN_DAYS = 45
EXPIRY_URGENT_DAYS = 14

# A certificate issued for 90 days or so comes from an automated ACME client and
# renews itself at about 30 days remaining. Warning about it is noise - worse,
# it tells a prospect we do not understand their setup. What IS worth saying is
# when such a certificate gets close to expiry, because that means the automation
# has stopped working. Manually-renewed year-long certificates keep the old rule.
SHORT_LIVED_MAX_DAYS = 100
AUTOMATED_ALERT_DAYS = 10


def run(ctx: ScanContext) -> list[Finding]:
    info = ctx.tls
    if info is None or not info.available:
        reason = (info.error if info else None) or "no TLS handshake"
        return [
            make(
                "tls.unavailable",
                C,
                Status.SKIPPED,
                params={"error": reason},
            )
        ]

    expiry = _expiry(info)
    # Expiry and hostname mismatch are *reasons* a certificate is untrusted. Each
    # already carries its own weight, so the generic finding must not charge again.
    explained = not info.hostname_ok or any(f.id == "tls.certificate_expired" for f in expiry)

    out: list[Finding] = []
    out.extend(_trust(info, explained=explained))
    out.extend(expiry)
    out.extend(_protocol(info))
    return out


def _trust(info, *, explained: bool = False) -> list[Finding]:
    out: list[Finding] = []

    if not info.hostname_ok:
        out.append(
            make(
                "tls.hostname_mismatch",
                C,
                Status.FAIL,
                severity=Severity.HIGH,
                weight=25,
                params={"names": ", ".join(info.san[:5]) or info.subject or "unknown"},
                evidence={"san": info.san},
            )
        )

    if info.trusted:
        out.append(
            make(
                "tls.certificate_trusted",
                C,
                Status.PASS,
                params={"issuer": info.issuer or "unknown"},
            )
        )
    else:
        out.append(
            make(
                "tls.certificate_untrusted",
                C,
                Status.FAIL,
                severity=Severity.HIGH,
                weight=0 if explained else UNTRUSTED_WEIGHT,
                params={"reason": info.trust_error or "not trusted"},
                evidence={"issuer": info.issuer},
            )
        )
    return out


def _lifetime_days(info) -> int | None:
    if not info.not_after or not info.not_before:
        return None
    return (info.not_after - info.not_before).days


def _expiry(info) -> list[Finding]:
    days = info.days_remaining
    if days is None:
        return []

    expires = info.not_after.date().isoformat() if info.not_after else "unknown"
    lifetime = _lifetime_days(info)
    automated = lifetime is not None and lifetime <= SHORT_LIVED_MAX_DAYS

    if days >= 0 and automated:
        if days <= AUTOMATED_ALERT_DAYS:
            return [
                make(
                    "tls.certificate_renewal_failing",
                    C,
                    Status.WARN,
                    severity=Severity.HIGH,
                    weight=12,
                    params={"days": days, "expires": expires},
                )
            ]
        return [
            make(
                "tls.certificate_auto_renewing",
                C,
                Status.PASS,
                params={"days": days, "expires": expires},
            )
        ]

    if days < 0:
        return [
            make(
                "tls.certificate_expired",
                C,
                Status.FAIL,
                severity=Severity.HIGH,
                weight=30,
                params={"days": abs(days), "expires": expires},
            )
        ]
    if days <= EXPIRY_URGENT_DAYS:
        return [
            make(
                "tls.certificate_expiring_urgently",
                C,
                Status.WARN,
                severity=Severity.HIGH,
                weight=10,
                params={"days": days, "expires": expires},
            )
        ]
    if days <= EXPIRY_WARN_DAYS:
        return [
            make(
                "tls.certificate_expiring_soon",
                C,
                Status.WARN,
                severity=Severity.LOW,
                weight=4,
                params={"days": days, "expires": expires},
            )
        ]
    return [
        make(
            "tls.certificate_expiry_ok",
            C,
            Status.PASS,
            params={"days": days, "expires": expires},
        )
    ]


def _protocol(info) -> list[Finding]:
    out: list[Finding] = []
    version = info.negotiated_version or "unknown"

    if version in ("TLSv1.3", "TLSv1.2"):
        out.append(make("tls.protocol_modern", C, Status.PASS, params={"version": version}))
    else:
        out.append(
            make(
                "tls.protocol_outdated",
                C,
                Status.WARN,
                severity=Severity.MEDIUM,
                weight=10,
                params={"version": version},
            )
        )

    if not info.legacy_tested:
        out.append(make("tls.legacy_not_tested", C, Status.SKIPPED))
    elif info.legacy_versions:
        out.append(
            make(
                "tls.legacy_protocols_enabled",
                C,
                Status.WARN,
                severity=Severity.MEDIUM,
                weight=5,
                params={"versions": ", ".join(sorted(set(info.legacy_versions)))},
            )
        )
    else:
        out.append(make("tls.legacy_protocols_disabled", C, Status.PASS))

    return out
