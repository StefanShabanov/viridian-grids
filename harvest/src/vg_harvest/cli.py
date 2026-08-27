"""vg-harvest - build the prospect list.

    vg-harvest verticals                       what can be harvested
    vg-harvest collect dentist hotel           two verticals into data/prospects.csv
    vg-harvest collect --all                   everything (slow, paced for Overpass)
    vg-harvest stats                           what is in the list now

The output feeds the scanner directly:

    vg-scan scan -f harvest/data/domains.txt --no-engines -o triage
"""

from __future__ import annotations

import contextlib
import random
import sys
from pathlib import Path

import typer

from .normalize import is_shared_host, is_social, to_domain
from .sources import overpass
from .store import Row, load, save, write_domains

app = typer.Typer(
    add_completion=False,
    help="Build lists of candidate Bulgarian business domains.",
    no_args_is_help=True,
)

DEFAULT_OUT = Path("data/prospects.csv")
DEFAULT_CACHE = Path("data/cache")
NEWLINE = chr(10)


def _echo(text: str = "") -> None:
    print(text)


@app.command()
def verticals() -> None:
    """List the verticals that can be harvested."""
    for name, selectors in overpass.VERTICALS.items():
        _echo(f"  {name:14} {' '.join(selectors)}")


@app.command()
def collect(
    wanted: list[str] = typer.Argument(None, help="Verticals to harvest"),
    every: bool = typer.Option(False, "--all", help="Harvest every known vertical"),
    country: str = typer.Option("BG", "--country", help="ISO country code"),
    out: Path = typer.Option(DEFAULT_OUT, "--out", "-o", help="Prospect CSV to merge into"),
    domains_out: Path = typer.Option(
        None, "--domains", help="Also write a plain domain list (default: alongside --out)"
    ),
    cache_dir: Path = typer.Option(DEFAULT_CACHE, "--cache", help="Where raw OSM responses live"),
    refresh: bool = typer.Option(False, "--refresh", help="Ignore the cache and re-query"),
    keep_shared: bool = typer.Option(
        False, "--keep-shared", help="Keep sites hosted on someone else's domain"
    ),
) -> None:
    """Harvest businesses with websites and merge them into the prospect list."""
    names = list(overpass.VERTICALS) if every else (wanted or [])
    if not names:
        raise typer.BadParameter("name at least one vertical, or pass --all")
    unknown = [n for n in names if n not in overpass.VERTICALS]
    if unknown:
        raise typer.BadParameter(f"unknown vertical(s): {', '.join(unknown)}")

    harvest = load(out)
    before = len(harvest)
    skipped = {"social": 0, "shared": 0, "unusable": 0, "duplicate": 0}

    for index, vertical in enumerate(names, start=1):
        _echo(f"[{index}/{len(names)}] {vertical} ...")
        try:
            businesses = overpass.fetch_vertical(
                vertical, country=country, cache_dir=cache_dir, refresh=refresh
            )
        except overpass.OverpassError as exc:
            _echo(f"    skipped: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001 - one vertical failing is not fatal
            _echo(f"    failed: {type(exc).__name__}: {exc}")
            continue

        added = 0
        for business in businesses:
            if is_social(business.website):
                skipped["social"] += 1
                continue
            domain = to_domain(business.website)
            if not domain:
                skipped["unusable"] += 1
                continue
            if not keep_shared and is_shared_host(business.website):
                skipped["shared"] += 1
                continue
            row = Row(
                domain=domain,
                company=business.name,
                industry=vertical,
                city=business.city,
                phone=business.phone,
                email=business.email,
                website=business.website,
                source=f"osm:{country.lower()}",
                osm_id=business.osm_id,
            )
            if harvest.add(row):
                added += 1
            else:
                skipped["duplicate"] += 1
        _echo(f"    {len(businesses)} with a website, {added} new")

    save(harvest, out)
    write_domains(harvest, domains_out or out.with_name("domains.txt"))

    _echo("")
    _echo(f"{len(harvest)} prospects ({len(harvest) - before} new)")
    _echo(
        "skipped: " + ", ".join(f"{count} {reason}" for reason, count in skipped.items() if count)
    )
    _echo(f"csv     -> {out}")
    _echo(f"domains -> {domains_out or out.with_name('domains.txt')}")


@app.command()
def sample(
    spec: list[str] = typer.Argument(..., help="vertical=count, e.g. dentist=20 hotel=15"),
    source: Path = typer.Option(DEFAULT_OUT, "--from", "-f", help="Prospect CSV to draw from"),
    out: Path = typer.Option(Path("data/sample.txt"), "--out", "-o", help="Domain list to write"),
    seed: int = typer.Option(1, "--seed", help="Change to draw a different sample"),
) -> None:
    """Draw a deliberate mix of domains for scanning.

    The plan wants conversion data per vertical - 30 hotels, 20 dentists, 20
    professional services - not whichever vertical happens to dominate the harvest.
    Ours is 74% hotels, so an unweighted sample would answer the wrong question.
    """
    harvest = load(source)
    if not harvest:
        raise typer.BadParameter(f"{source} is empty or missing")

    wanted: dict[str, int] = {}
    for item in spec:
        name, _, count = item.partition("=")
        if not count.isdigit():
            raise typer.BadParameter(f"expected vertical=count, got {item!r}")
        wanted[name] = int(count)

    by_vertical: dict[str, list[str]] = {}
    for row in harvest.rows.values():
        by_vertical.setdefault(row.industry, []).append(row.domain)

    rng = random.Random(seed)
    picked: list[str] = []
    for vertical, count in wanted.items():
        available = sorted(by_vertical.get(vertical, []))
        if not available:
            _echo(f"  {vertical}: nothing harvested yet")
            continue
        take = min(count, len(available))
        picked.extend(rng.sample(available, take))
        _echo(f"  {vertical:14} {take:>3} of {len(available)}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(NEWLINE.join(sorted(set(picked))) + NEWLINE, encoding="utf-8")
    _echo("")
    _echo(f"{len(set(picked))} domains -> {out}")


@app.command()
def stats(
    source: Path = typer.Argument(DEFAULT_OUT, help="Prospect CSV to summarize"),
) -> None:
    """What is in the prospect list, by vertical and by town."""
    harvest = load(source)
    if not harvest:
        raise typer.BadParameter(f"{source} is empty or missing")

    by_vertical: dict[str, int] = {}
    by_city: dict[str, int] = {}
    with_phone = 0
    with_email = 0
    for row in harvest.rows.values():
        by_vertical[row.industry or "?"] = by_vertical.get(row.industry or "?", 0) + 1
        if row.city:
            by_city[row.city] = by_city.get(row.city, 0) + 1
        with_phone += bool(row.phone)
        with_email += bool(row.email)

    _echo(f"{len(harvest)} prospects, {with_phone} with a phone, {with_email} with an email")
    _echo("")
    _echo("by vertical")
    for name, count in sorted(by_vertical.items(), key=lambda kv: -kv[1]):
        _echo(f"  {count:>5}  {name}")
    _echo("")
    _echo("top towns")
    for name, count in sorted(by_city.items(), key=lambda kv: -kv[1])[:12]:
        _echo(f"  {count:>5}  {name}")


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):
                reconfigure(encoding="utf-8", errors="replace")
    app()


if __name__ == "__main__":
    main()
