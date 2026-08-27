"""vg-scan - the command line the sales workflow actually runs.

vg-scan scan example.bg                       one site, full report
vg-scan scan a.bg b.bg c.bg                   several, ranked
vg-scan scan --from prospects.txt --out-dir out --csv out/scans.csv
vg-scan scan example.bg -v                    every finding, with weights
vg-scan summary out                           how the scanner behaves across a corpus
"""

from __future__ import annotations

import contextlib
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import typer

from . import __version__
from .aggregate import Aggregate, aggregate, load_results
from .catalog import LANGUAGES
from .hooks import choose as choose_hook
from .intel import enrich as intel_enrich
from .intel import versions_in as intel_versions
from .intel.store import IntelStore
from .models import ScanResult, Status
from .probe import DEFAULT_TIMEOUT, normalize_domain
from .report import csv_row, render_html, render_text
from .runner import scan as run_scan
from .scoring import score as compute_score

HTML_LIMIT = 200  # above this a sweep is triage, not reporting

app = typer.Typer(
    add_completion=False,
    help="Non-intrusive website health checks for Viridian Grids.",
    no_args_is_help=True,
)


def _use_utf8_console() -> None:
    """Bulgarian reports are the point, so the console has to speak UTF-8.

    Re-encoding to the console default turned every Cyrillic character into "?".
    Reconfiguring the stream keeps the text intact wherever the terminal can show it.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):
                reconfigure(encoding="utf-8", errors="replace")


def _echo(text: str = "") -> None:
    # flush: stdout is block-buffered when redirected, so a long background run
    # showed nothing at all until it finished.
    print(text, flush=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ------------------------------------------------------------------------ scan


@app.command()
def scan(
    domains: list[str] = typer.Argument(None, help="One or more domains or URLs"),
    from_file: Path = typer.Option(
        None, "--from", "-f", help="Also read domains from a file (one per line, # comments)"
    ),
    lang: str = typer.Option("en", "--lang", "-l", help=f"Report language: {'/'.join(LANGUAGES)}"),
    customer: bool = typer.Option(
        False, "--customer", help="Show only what a prospect would see (hides the sales view)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show every finding with its id, status and weight"
    ),
    full: bool = typer.Option(
        False, "--full", help="Print the whole report for each site, even when scanning many"
    ),
    out_dir: Path = typer.Option(None, "--out-dir", "-o", help="Write JSON and HTML per domain"),
    json_out: Path = typer.Option(None, "--json", help="Write the raw JSON here (single domain)"),
    html_out: Path = typer.Option(None, "--html", help="Write the report here (single domain)"),
    csv_out: Path = typer.Option(None, "--csv", help="Write one CRM row per domain"),
    workers: int = typer.Option(4, "--workers", "-w", min=1, max=12),
    timeout: float = typer.Option(DEFAULT_TIMEOUT, help="Per-request timeout in seconds"),
    quick: bool = typer.Option(False, "--quick", help="Skip robots/sitemap/favicon and legacy TLS"),
    deep: bool = typer.Option(
        False, "--deep", help="Also run the slow engines (testssl.sh). Tens of seconds per site."
    ),
    authorized: bool = typer.Option(
        False,
        "--authorized",
        help="Target has given WRITTEN permission. Enables intrusive engines (nuclei).",
    ),
    engines: str = typer.Option(
        None, "--engines", help="Comma-separated engine names, e.g. observatory,webanalyze"
    ),
    no_engines: bool = typer.Option(
        False, "--no-engines", help="Skip external engines entirely (fast, our checks only)"
    ),
) -> None:
    """Scan one site or many. One domain prints the report; several print a ranked table."""
    targets = _collect(domains or [], from_file)
    if not targets:
        raise typer.BadParameter("give at least one domain, or --from a file")
    if len(targets) > 1 and (json_out or html_out):
        raise typer.BadParameter("--json/--html take a single domain; use --out-dir for many")

    if authorized and len(targets) > 1:
        raise typer.BadParameter(
            "--authorized applies to one target at a time; permission is per-customer"
        )

    single = len(targets) == 1
    if no_engines:
        only: list[str] | None = ["none"]  # matches nothing, so nothing runs
    else:
        only = [name.strip() for name in engines.split(",")] if engines else None
    results = _run(
        targets,
        workers=workers,
        timeout=timeout,
        quick=quick,
        live=not single,
        deep=deep,
        authorized=authorized,
        engines=only,
        out_dir=out_dir,
    )

    for result in results:
        if single or full:
            _echo(render_text(result, lang, internal=not customer))
            _echo()
        if verbose:
            _echo(_finding_table(result))
            _echo()

    if not single:
        _echo(_ranked_table(results))
        _echo(_tally(results, len(targets)))

    _emit_files(results, out_dir, json_out, html_out, csv_out, lang)


# --------------------------------------------------------------------- summary


@app.command()
def summary(
    source: Path = typer.Argument(Path("out"), help="Directory of scan JSON files"),
    top: int = typer.Option(12, "--top", help="How many findings and prospects to list"),
) -> None:
    """Aggregate a corpus of saved scans. This is how you tune the weights."""
    if not source.exists():
        raise typer.BadParameter(f"{source} does not exist")
    results = load_results(source)
    if not results:
        raise typer.BadParameter(f"no readable scan JSON in {source}")
    _echo(_render_summary(aggregate(results), top))


@app.command()
def intel(
    source: Path = typer.Argument(Path("out"), help="Directory of scan JSON files, or one file"),
    api_key: str = typer.Option(
        "", "--nvd-key", envvar="NVD_API_KEY", help="Free NVD key: 50 requests/30s instead of 5"
    ),
    no_cves: bool = typer.Option(False, "--no-cves", help="End-of-life dates only"),
    top: int = typer.Option(10, "--top", help="Only enrich the N best prospects"),
    max_age: int = typer.Option(
        30, "--max-age", help="Re-look-up anything older than this many days"
    ),
    refresh: bool = typer.Option(False, "--refresh", help="Ignore the local database entirely"),
    db: Path = typer.Option(None, "--db", help="Path to the local intel database"),
    save: bool = typer.Option(
        True, "--save/--no-save", help="Write the findings back into the JSON"
    ),
) -> None:
    """Look up what is publicly known about the versions a scan found.

    Runs against public databases, never against the prospect - so it is free to
    do, and it is the depth the intrusive scanners promised without the traffic.
    NVD allows 5 requests per 30 seconds without a key, so this enriches a
    shortlist rather than a whole harvest.
    """
    results = load_results(source)
    if not results:
        raise typer.BadParameter(f"no readable scan JSON in {source}")

    store = IntelStore(path=db, max_age_days=max_age)
    known = store.stats()

    results.sort(key=lambda r: (-r.prospect_score.total, r.score))
    shortlist = [r for r in results[:top] if r.reachable]
    _echo(f"enriching {len(shortlist)} of {len(results)} scans")
    _echo(f"local database: {known['entries']} entries, {known['stale']} older than {max_age} days")
    _echo("")

    for result in shortlist:
        pairs = intel_versions(result)
        if not pairs:
            _echo(f"  {result.domain}: no versions detected")
            continue

        findings = intel_enrich(
            result,
            store=store,
            api_key=api_key,
            include_cves=not no_cves,
            refresh=refresh,
        )
        notable = [f for f in findings if f.status is Status.WARN]
        detected = ", ".join(f"{name} {ver}" for name, ver in pairs)
        _echo(f"  {result.domain}  ({detected})")
        for finding in notable:
            _echo(f"      [!] {finding.title}")
            if finding.detail:
                _echo(f"          {finding.detail}")
            if finding.reference:
                _echo(f"          {finding.reference}")
        if not notable:
            _echo("      nothing outstanding - everything detected is still supported")

        if save:
            result.findings = [f for f in result.findings if f.source != "intel"] + findings
            result.score = compute_score(result.findings)
            path = source / f"{result.domain}.json" if source.is_dir() else source
            _write(path, result.model_dump_json(indent=2))
        _echo("")

    final = store.stats()
    _echo(
        f"local database: {final['entries']} entries "
        f"(+{final['entries'] - known['entries']} new). "
        f"Re-run with --refresh weekly to catch CVEs filed since."
    )


@app.command()
def queue(
    source: Path = typer.Argument(Path("out/sweep"), help="Directory of scan JSON files"),
    contacts: Path = typer.Option(
        None, "--contacts", help="Harvest CSV to join names, towns and phones from"
    ),
    out: Path = typer.Option(Path("out/queue.csv"), "--out", "-o", help="Work queue to write"),
    limit: int = typer.Option(0, "--limit", help="Only the top N rows (0 = all)"),
    min_prospect: int = typer.Option(8, "--min-prospect", help="Drop anything below this"),
    kind: str = typer.Option(None, "--kind", help="Only this hook type, e.g. cert_expiry"),
) -> None:
    """Build the outreach queue: one row per prospect, with the line to lead with.

    Joins scan results to the harvest's contact details and picks a single hook
    per site. Sorted so the time-boxed ones come first - an expiring certificate
    has a deadline, an outdated theme does not.
    """
    results = load_results(source)
    if not results:
        raise typer.BadParameter(f"no readable scan JSON in {source}")

    contact_rows = _load_contacts(contacts) if contacts else {}
    rows = []
    for result in results:
        hook = choose_hook(result)
        if hook.kind in ("dead", "blocked", "none"):
            continue
        if kind and hook.kind != kind:
            continue
        if result.prospect_score.total < min_prospect and hook.kind != "site_down":
            continue
        rows.append((hook, result, contact_rows.get(result.domain, {})))

    rows.sort(key=lambda r: (-r[0].urgency, -r[1].prospect_score.total, r[1].score))
    if limit:
        rows = rows[:limit]

    fields = [
        "Domain",
        "Company",
        "Vertical",
        "City",
        "Phone",
        "Email",
        "Prospect",
        "Score",
        "HookType",
        "Hook",
        "HookDetail",
        "CertExpires",
        "CertDays",
        "Platform",
        "Contacted",
        "FollowUp1",
        "FollowUp2",
        "Response",
        "Outcome",
        "Notes",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for hook, result, contact in rows:
            base = csv_row(result)
            writer.writerow(
                {
                    "Domain": result.domain,
                    "Company": contact.get("Company", ""),
                    "Vertical": contact.get("Industry", ""),
                    "City": contact.get("City", ""),
                    "Phone": contact.get("Phone", ""),
                    "Email": contact.get("Email", ""),
                    "Prospect": result.prospect_score.total,
                    "Score": result.score,
                    "HookType": hook.kind,
                    "Hook": hook.text,
                    "HookDetail": hook.detail,
                    "CertExpires": base.get("Cert expires", ""),
                    "CertDays": base.get("Cert days left", ""),
                    "Platform": base.get("Website platform", ""),
                    "Contacted": "",
                    "FollowUp1": "",
                    "FollowUp2": "",
                    "Response": "",
                    "Outcome": "",
                    "Notes": "",
                }
            )

    counts: dict[str, int] = {}
    for hook, _, _ in rows:
        counts[hook.kind] = counts.get(hook.kind, 0) + 1
    _echo(f"{len(rows)} prospects -> {out}")
    _echo("")
    _echo("by opener")
    for name, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        _echo(f"  {count:>5}  {name}")


def _load_contacts(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for record in csv.DictReader(handle):
            domain = (record.get("Domain") or "").strip().lower()
            if domain:
                rows[domain] = record
    return rows


@app.command()
def version() -> None:
    """Print the scanner version."""
    _echo(f"vg-scan {__version__}")


# ------------------------------------------------------------------------ guts


def _collect(domains: list[str], from_file: Path | None) -> list[str]:
    """Normalize and de-duplicate, keeping the order they were given in."""
    raw = list(domains)
    if from_file:
        raw.extend(from_file.read_text(encoding="utf-8").splitlines())

    seen: list[str] = []
    for line in raw:
        cleaned = line.split("#", 1)[0].strip()
        if not cleaned:
            continue
        try:
            host = normalize_domain(cleaned)
        except ValueError:
            _echo(f"  skipping unusable entry: {line.strip()}")
            continue
        if host not in seen:
            seen.append(host)
    return seen


def _run(
    targets: list[str],
    *,
    workers: int,
    timeout: float,
    quick: bool,
    live: bool,
    deep: bool = False,
    authorized: bool = False,
    engines: list[str] | None = None,
    out_dir: Path | None = None,
) -> list[ScanResult]:
    """Scan concurrently, reporting and persisting each result the moment it lands.

    Writing as we go rather than at the end matters on a thousand-domain sweep: a
    failure at site 900 used to lose all 900.
    """
    results: list[ScanResult] = []
    total = len(targets)
    done = 0

    if live:
        _echo(f"scanning {total} sites, {workers} at a time\n")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                run_scan,
                host,
                timeout=timeout,
                check_aux=not quick,
                check_legacy_tls=not quick,
                deep=deep,
                authorized=authorized,
                engines=engines,
            ): host
            for host in targets
        }
        for future in as_completed(futures):
            host = futures[future]
            done += 1
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001 - one bad domain must not stop the run
                if live:
                    _echo(f"  [{done:>3}/{total}]   --   failed  {host}  ({type(exc).__name__})")
                continue
            results.append(result)
            if out_dir:
                _write(out_dir / f"{result.domain}.json", result.model_dump_json(indent=2))
            if live:
                _echo(f"  [{done:>4}/{total}] {_row(result)}")

    results = _verify_unreachable(
        results,
        timeout=timeout,
        quick=quick,
        deep=deep,
        authorized=authorized,
        engines=engines,
        out_dir=out_dir,
        live=live,
    )
    results.sort(key=lambda r: (-r.prospect_score.total, r.score))
    return results


def _verify_unreachable(
    results: list[ScanResult],
    *,
    timeout: float,
    quick: bool,
    deep: bool,
    authorized: bool,
    engines: list[str] | None,
    out_dir: Path | None,
    live: bool,
) -> list[ScanResult]:
    """Re-check anything that failed, one at a time, before believing it.

    Eight concurrent workers overwhelmed the local DNS resolver on a 1,028-domain
    sweep, and "Temporary failure in name resolution" was recorded as if the
    domain were gone. Five of eight sampled failures resolved perfectly on a
    serial retry. Condemning a live prospect as dead is the expensive direction
    to be wrong in, so failures get a second, unhurried look.
    """
    suspect = [r for r in results if not r.reachable]
    if not suspect:
        return results

    if live:
        _echo()
        _echo(f"  re-checking {len(suspect)} unreachable domains one at a time")

    recovered = 0
    by_domain = {r.domain: r for r in results}
    for result in suspect:
        try:
            retry = run_scan(
                result.domain,
                timeout=timeout,
                check_aux=not quick,
                check_legacy_tls=not quick,
                deep=deep,
                authorized=authorized,
                engines=engines,
            )
        except Exception:  # noqa: BLE001 - a failed retry just leaves the first answer
            continue
        if retry.reachable:
            by_domain[result.domain] = retry
            recovered += 1
            if out_dir:
                _write(out_dir / f"{retry.domain}.json", retry.model_dump_json(indent=2))

    if live and recovered:
        _echo(f"  {recovered} of {len(suspect)} were transient failures, not dead sites")
    return list(by_domain.values())


def _row(result: ScanResult) -> str:
    if not result.reachable:
        note = "  DEAD" if _dns_failed(result) else "  DOWN"
    elif result.inconclusive:
        note = "  needs review"
    else:
        note = ""
    return (
        f"{result.prospect_score.total:>2}/{result.prospect_score.max}"
        f"  {result.score:>3}/100  {result.domain}{note}"
    )


def _dns_failed(result: ScanResult) -> bool:
    return any(f.id == "availability.dns_failure" for f in result.findings)


def _ranked_table(results: list[ScanResult]) -> str:
    if not results:
        return "\nnothing scanned successfully"
    lines = ["", "ranked by prospect score", ""]
    lines.extend(f"  {_row(result)}" for result in results)
    return "\n".join(lines)


def _tally(results: list[ScanResult], attempted: int) -> str:
    blocked = sum(1 for r in results if r.inconclusive)
    dead = sum(1 for r in results if not r.reachable and _dns_failed(r))
    down = sum(1 for r in results if not r.reachable and not _dns_failed(r))
    failed = attempted - len(results)
    parts = [f"{len(results)} scanned"]
    if dead:
        parts.append(f"{dead} dead domain(s) - drop from the list")
    if down:
        parts.append(f"{down} site(s) down - worth a call")
    if blocked:
        parts.append(f"{blocked} blocked (do not send)")
    if failed:
        parts.append(f"{failed} failed")
    return "\n" + ", ".join(parts)


def _finding_table(result: ScanResult) -> str:
    """Every finding, weights included. The view for judging whether a weight is fair."""
    order = {Status.FAIL: 0, Status.WARN: 1, Status.INFO: 2, Status.PASS: 3, Status.SKIPPED: 4}
    findings = sorted(result.findings, key=lambda f: (order[f.status], -f.weight, f.id))

    lines = [f"{result.domain}  all findings", "", "  status   sev     wt  id"]
    for finding in findings:
        lines.append(
            f"  {finding.status.value:<8} {finding.severity.value:<6} "
            f"{finding.weight:>3}  {finding.id}"
        )
    deducted = sum(f.weight for f in findings if f.deducts)
    lines.append("")
    lines.append(f"  100 - {deducted} = {result.score}")

    if result.errors:
        lines.append("")
        lines.extend(f"  error: {error}" for error in result.errors)
    return "\n".join(lines)


def _emit_files(
    results: list[ScanResult],
    out_dir: Path | None,
    json_out: Path | None,
    html_out: Path | None,
    csv_out: Path | None,
    lang: str,
) -> None:
    if json_out and results:
        _write(json_out, results[0].model_dump_json(indent=2))
        _echo(f"json  -> {json_out}")
    if html_out and results:
        _write(html_out, render_html(results[0], lang))
        _echo(f"html  -> {html_out}")

    if out_dir:
        # JSON was written as each scan landed. Rendering a report for every domain
        # in a large sweep is wasted work - they are produced for a shortlist.
        if len(results) <= HTML_LIMIT:
            for result in results:
                _write(out_dir / f"{result.domain}.html", render_html(result, lang))
        else:
            _echo(f"({len(results)} scans: HTML skipped, run `intel` or re-render a shortlist)")
        _echo(f"files -> {out_dir}")

    if csv_out and results:
        rows = [csv_row(result) for result in results]
        csv_out.parent.mkdir(parents=True, exist_ok=True)
        # utf-8-sig so Excel opens Cyrillic without an import dialog.
        with csv_out.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        _echo(f"csv   -> {csv_out}")


def _render_summary(agg: Aggregate, top: int) -> str:
    low, mid, high = agg.score_summary()
    lines = [
        f"{agg.total} scans, {agg.usable} usable, {agg.blocked} blocked",
        "",
        f"score   min {low}   median {mid}   max {high}",
        "        " + "   ".join(f"{name} {agg.bands[name]}" for name in ("good", "fair", "poor")),
        "",
        "most common problems",
        "",
    ]
    for finding_id, count in agg.findings.most_common(top):
        share = agg.frequency(finding_id)
        bar = "#" * round(share * 20)
        lines.append(f"  {count:>4}  {share:>4.0%}  {bar:<20}  {finding_id}")

    lines.extend(["", "platforms", ""])
    for name, count in agg.platforms.most_common(8):
        lines.append(f"  {count:>4}  {name}")

    if agg.signals:
        lines.extend(["", "prospect signals", ""])
        for name, count in agg.signals.most_common():
            lines.append(f"  {count:>4}  {name}")

    lines.extend(["", f"best prospects (top {top})", ""])
    for prospect, score, domain in agg.prospects[:top]:
        lines.append(f"  {prospect:>2}  {score:>3}/100  {domain}")

    if agg.errors:
        lines.extend(["", f"{len(agg.errors)} errors recorded", ""])
        for domain, error in agg.errors[:10]:
            lines.append(f"  {domain}: {error}")

    return "\n".join(lines)


def main() -> None:
    _use_utf8_console()
    app()


if __name__ == "__main__":
    main()
