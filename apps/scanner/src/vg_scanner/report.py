"""Rendering.

Two audiences, two renderers, one rule between them: the prospect score is ours,
not theirs. It never appears in anything a prospect receives.
"""

from __future__ import annotations

import html
from collections.abc import Iterable

from .catalog import (
    BANDS,
    DEFAULT_LANGUAGE,
    DISCLAIMER,
    heading,
    resolve,
    signal_name,
)
from .hooks import choose as choose_hook
from .models import Finding, ScanResult, Severity, Status
from .scoring import band

_SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2, Severity.INFO: 3}


def _sorted_attention(findings: Iterable[Finding]) -> list[Finding]:
    """Worst first, so the one useful observation for outreach is at the top."""
    return sorted(
        findings,
        key=lambda f: (_SEVERITY_ORDER.get(f.severity, 3), -f.weight),
    )


def _groups(result: ScanResult) -> dict[str, list[Finding]]:
    return {
        "attention": _sorted_attention(result.by_status(Status.FAIL, Status.WARN)),
        "working": result.by_status(Status.PASS),
        "detected": result.by_status(Status.INFO),
        "skipped": result.by_status(Status.SKIPPED),
    }


# --------------------------------------------------------------------------- text


def render_text(result: ScanResult, lang: str = DEFAULT_LANGUAGE, *, internal: bool = False) -> str:
    """The one-page view, for the terminal. `internal=True` adds the sales side."""
    groups = _groups(result)
    label = BANDS.get(lang, BANDS[DEFAULT_LANGUAGE])[band(result.score)]
    lines: list[str] = []

    lines.append(f"{result.domain} {heading('report_title', lang)}")
    lines.append("")
    lines.append(f"{heading('overall', lang)}: {result.score}/100  ({label})")
    lines.append("")
    if result.inconclusive:
        lines.append(f"  ** {heading('inconclusive', lang)}")
        lines.append("")

    if groups["working"]:
        for finding in groups["working"]:
            title, detail = resolve(finding, lang)
            lines.append(f"  [ok]   {title}")
            # The facts behind a pass matter to us even when they are good news:
            # a certificate expiry date decides whether there is a hook and when
            # to come back. The customer one-pager stays titles-only.
            if internal and detail:
                lines.append(f"         {detail}")
        lines.append("")

    if groups["attention"]:
        for finding in groups["attention"]:
            title, detail = resolve(finding, lang)
            lines.append(f"  [!]    {title}")
            if detail:
                lines.append(f"         {detail}")
        lines.append("")

    if groups["detected"]:
        lines.append(f"{heading('detected', lang)}:")
        for finding in groups["detected"]:
            title, _ = resolve(finding, lang)
            lines.append(f"  -      {title}")
        lines.append("")

    lines.append(DISCLAIMER.get(lang, DISCLAIMER[DEFAULT_LANGUAGE]))

    if internal:
        lines.append("")
        lines.append("-- internal " + "-" * 56)
        prospect = result.prospect_score
        names = ", ".join(signal_name(s.name, lang) for s in prospect.signals) or "none"
        lines.append(f"{heading('prospect', lang)}: {prospect.total}/{prospect.max}  ({names})")
        lines.append(f"scanned in {result.duration_ms} ms, final URL {result.final_url or '-'}")
        if result.engines:
            states = ", ".join(f"{n}={s}" for n, s in sorted(result.engines.items()))
            lines.append(f"engines: {states}")
        if groups["skipped"]:
            skipped = ", ".join(f.id for f in groups["skipped"])
            lines.append(f"{heading('not_checked', lang)}: {skipped}")
        for error in result.errors:
            lines.append(f"error: {error}")

    return "\n".join(lines)


# --------------------------------------------------------------------------- html

_STYLE = """
:root { --ink:#16211c; --muted:#5c6b64; --line:#dfe6e2; --ok:#2f7d5d; --warn:#a8631a; --bg:#ffffff; }
* { box-sizing:border-box; }
body { margin:0; background:#f4f6f5; color:var(--ink);
  font:15px/1.55 "Segoe UI",-apple-system,Roboto,Helvetica,Arial,sans-serif; }
.sheet { max-width:760px; margin:32px auto; background:var(--bg); padding:44px 48px;
  border:1px solid var(--line); border-radius:4px; }
header { display:flex; justify-content:space-between; align-items:baseline;
  border-bottom:2px solid var(--ink); padding-bottom:14px; margin-bottom:26px; gap:16px; }
h1 { font-size:21px; margin:0; font-weight:650; letter-spacing:-0.01em; }
h1 span { display:block; font-size:13px; font-weight:400; color:var(--muted); margin-top:3px; }
.meta { font-size:12px; color:var(--muted); text-align:right; white-space:nowrap; }
.score { display:flex; align-items:baseline; gap:12px; margin:0 0 30px; }
.score b { font-size:38px; font-weight:650; line-height:1; }
.score .of { font-size:15px; color:var(--muted); }
.score .band { font-size:13px; color:var(--muted); margin-left:auto; }
.bar { height:6px; background:var(--line); border-radius:3px; overflow:hidden; margin-bottom:30px; }
.bar i { display:block; height:100%; background:var(--ok); }
h2 { font-size:12px; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted);
  margin:26px 0 12px; font-weight:600; }
ul { list-style:none; margin:0; padding:0; }
li { padding:9px 0 9px 26px; position:relative; border-bottom:1px solid var(--line); }
li:last-child { border-bottom:none; }
li .t { font-weight:550; }
li .d { color:var(--muted); font-size:13.5px; margin-top:2px; }
li.ok:before { content:"\\2713"; position:absolute; left:0; top:9px; color:var(--ok); font-weight:700; }
li.warn:before { content:"\\0021"; position:absolute; left:2px; top:9px; color:var(--warn); font-weight:700; }
li.info:before { content:"\\2022"; position:absolute; left:3px; top:9px; color:var(--muted); }
footer { margin-top:34px; padding-top:16px; border-top:1px solid var(--line);
  font-size:12px; color:var(--muted); }
footer .brand { margin-top:8px; }
.notice { margin:-14px 0 26px; padding:11px 14px; border-left:3px solid var(--warn);
  background:#fdf6ee; color:var(--ink); font-size:13.5px; }
@media print {
  body { background:#fff; } .sheet { margin:0; border:none; padding:0; max-width:none; }
}
"""


def render_html(result: ScanResult, lang: str = DEFAULT_LANGUAGE) -> str:
    """Customer-facing one-pager. Self-contained, printable, no prospect score."""
    groups = _groups(result)
    band_key = band(result.score)
    band_label = BANDS.get(lang, BANDS[DEFAULT_LANGUAGE])[band_key]
    bar_colour = {"good": "#2f7d5d", "fair": "#a8631a", "poor": "#a33c2f"}[band_key]
    scanned = result.scanned_at.strftime("%d.%m.%Y")

    parts: list[str] = [
        "<!doctype html>",
        f'<html lang="{html.escape(lang)}"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{html.escape(result.domain)} - {html.escape(heading('report_title', lang))}</title>",
        f"<style>{_STYLE}</style></head><body><div class=sheet>",
        "<header><h1>",
        html.escape(result.domain),
        f"<span>{html.escape(heading('report_title', lang))}</span></h1>",
        f"<div class=meta>{html.escape(heading('scanned_at', lang))} {scanned}</div></header>",
        f"<div class=score><b>{result.score}</b><span class=of>/ 100</span>"
        f"<span class=band>{html.escape(band_label)}</span></div>",
        f'<div class=bar><i style="width:{result.score}%;background:{bar_colour}"></i></div>',
    ]

    if result.inconclusive:
        parts.append(f"<p class=notice>{html.escape(heading('inconclusive', lang))}</p>")

    parts.append(_html_section(heading("attention", lang), groups["attention"], "warn", lang, True))
    parts.append(_html_section(heading("working", lang), groups["working"], "ok", lang, False))
    parts.append(_html_section(heading("detected", lang), groups["detected"], "info", lang, False))

    parts.append(
        "<footer>"
        + html.escape(DISCLAIMER.get(lang, DISCLAIMER[DEFAULT_LANGUAGE]))
        + f"<div class=brand>{html.escape(heading('prepared_by', lang))}</div></footer>"
    )
    parts.append("</div></body></html>")
    return "".join(parts)


def _html_section(
    title: str, findings: list[Finding], css: str, lang: str, with_detail: bool
) -> str:
    if not findings:
        return ""
    items: list[str] = []
    for finding in findings:
        name, detail = resolve(finding, lang)
        row = f"<li class={css}><div class=t>{html.escape(name)}</div>"
        if with_detail and detail:
            row += f"<div class=d>{html.escape(detail)}</div>"
        items.append(row + "</li>")
    return f"<h2>{html.escape(title)}</h2><ul>{''.join(items)}</ul>"


# ---------------------------------------------------------------------- csv line


def csv_row(result: ScanResult) -> dict[str, object]:
    """One flat row per scan, shaped to paste straight into the prospect CRM."""
    groups = _groups(result)
    headline = ""
    if groups["attention"]:
        title, detail = resolve(groups["attention"][0], DEFAULT_LANGUAGE)
        headline = f"{title} - {detail}" if detail else title
    expires, days, renewal = _certificate(result)
    hook = choose_hook(result)
    return {
        "Domain": result.domain,
        "Website platform": _platform(result),
        "Cert expires": expires,
        "Cert days left": days,
        "Cert renewal": renewal,
        "Scan score": result.score,
        "Prospect score": result.prospect_score.total,
        "Hook": hook.text,
        "HookType": hook.kind,
        "HookDetail": hook.detail,
        "Interesting finding": headline,
        "Status": _status(result),
        "Needs manual review": "yes" if result.inconclusive else "",
        "Signals": " ".join(s.name for s in result.prospect_score.signals),
        "Scanned": result.scanned_at.date().isoformat(),
    }


def _status(result: ScanResult) -> str:
    """Whether this row is worth contacting at all."""
    if not result.reachable:
        dead = any(f.id == "availability.dns_failure" for f in result.findings)
        return "dead domain" if dead else "site down"
    if result.inconclusive:
        return "blocked - review"
    return "ok"


def _certificate(result: ScanResult) -> tuple[str, str, str]:
    """Expiry date, days remaining, and whether anyone has to remember to renew.

    A manually-renewed year-long certificate a month out is one of the few findings
    that is both specific and genuinely urgent, so the prospect list sorts by it.
    """
    renewal = ""
    for finding in result.findings:
        if not finding.id.startswith("tls.certificate"):
            continue
        if finding.id == "tls.certificate_auto_renewing":
            renewal = "automatic"
        elif finding.id.startswith("tls.certificate_expir"):
            renewal = renewal or "manual"
        expires = finding.params.get("expires")
        days = finding.params.get("days")
        if expires:
            return str(expires), str(days if days is not None else ""), renewal or "manual"
    return "", "", ""


# Whichever source answered. webanalyze supersedes our own CMS check, so reading
# only ours silently emptied the "Website platform" column in the prospect list.
_PLATFORM_IDS = ("webanalyze.cms", "technology.cms_detected")


def _platform(result: ScanResult) -> str:
    by_id = {f.id: f for f in result.findings}
    for finding_id in _PLATFORM_IDS:
        finding = by_id.get(finding_id)
        if finding is None:
            continue
        name = str(finding.params.get("name", ""))
        version = str(finding.params.get("version", ""))
        if name:
            return f"{name} {version}".strip()
    return ""
