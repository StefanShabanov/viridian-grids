# vg-scan

Non-intrusive website health scanner. Aggregates passive checks, normalizes them, scores them,
and renders a one-page report in English or Bulgarian.

Full spec: [../../docs/scanner-spec.md](../../docs/scanner-spec.md).

## Rule zero

Passive checks only against sites we do not own. No fuzzing, SQLi/XSS testing, brute forcing,
aggressive crawling, exploit attempts, authenticated scanning or intrusive port scanning without
written authorization. A whole scan costs the target **under ten requests**, all of them requests an
ordinary visitor could make, from a User-Agent that identifies us.

## Setup

The repo lives on the Windows filesystem, reachable from WSL at
`/mnt/d/code/viridian-grids`. **A Windows venv cannot be used from Linux and vice versa**, so keep
one per platform - both are gitignored.

### WSL / Linux

```sh
cd /mnt/d/code/viridian-grids/apps/scanner
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install -e ".[dev]"
```

Verified on Ubuntu 24.04 with Python 3.12. Installing across the `/mnt/d` mount is slow the first
time - a few minutes is normal, and it is a one-off.

### Windows / PowerShell

```powershell
cd d:\code\viridian-grids\apps\scanner
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Either way `vg-scan` lands on your PATH once the venv is active. Everything below is identical on
both platforms.

## Use

```sh
vg-scan scan example.bg                      # one site, full report
vg-scan scan a.bg b.bg c.bg                  # several, live progress then a ranked table
vg-scan scan -f prospects.txt -w 8           # from a file, 8 at a time
vg-scan scan example.bg --lang bg            # Bulgarian
vg-scan scan example.bg --customer           # exactly what a prospect would see
vg-scan scan example.bg -v                   # every finding with its id, status and weight
vg-scan scan example.bg --quick              # skip robots/sitemap/favicon and legacy TLS

vg-scan scan -f prospects.txt -o out --csv out/scans.csv --lang bg
vg-scan summary out                          # how the scanner behaves across the whole corpus
```

`--no-engines` skips the external tools for a fast look; `--engines a,b` picks specific ones.

`-f/--from` and inline domains combine, and duplicates are dropped. Multi-site runs print each
result the moment it lands and finish with a table ranked by prospect score. Add `--full` to print
every report as well.

Sample list for poking at it: [testdata/sample-domains.txt](testdata/sample-domains.txt).

## Reading a scan for outreach

The terminal view shows the numbers behind **passing** findings too, because they decide the timing:
`Certificate renews automatically — 78 days remaining (expires 2026-11-14)` tells you there is no
hook here and when to look again. The customer one-pager stays titles-only.

The CSV export carries `Cert expires`, `Cert days left` and `Cert renewal` so the prospect list can
be sorted by them. **`manual` is the column that matters** — a year-long certificate from a
commercial CA that nobody automated is one of the few findings that is specific, dated and genuinely
urgent. `automatic` means Let's Encrypt is handling it and there is nothing to say.

## Two numbers, never confused

| | Who sees it | What it means |
|---|---|---|
| **Score** /100 | the prospect | 100 minus the weight of what we found |
| **Prospect score** /17 | us only | how much this company is worth personal outreach |

The prospect score never appears in the HTML report or in `--customer` output. A test enforces it.

They move independently. wordpress.org scores 86/100 *and* ranks 12/17 - healthy site, obvious fit.
A neglected WordPress site scores low on both.

**What the prospect score actually ranks is how much of an opening there is for a cold email**, not
how good a customer the company would be. A well-run Bulgarian shop with a valid certificate, all its
headers and a fast server will score 4-6 even though it is exactly the kind of business the service is
for - there is simply nothing to lead the conversation with. Treat a low score as "no hook yet", not
as "not worth having", and use the health report's own findings to decide what to say.

## Calibrating it

This is what `-v` and `summary` are for.

- `vg-scan scan somesite.bg -v` shows every finding with its weight and the arithmetic
  (`100 - 17 = 83`), so you can judge whether a weight is fair.
- `vg-scan summary out` aggregates a directory of saved scans: score distribution, the most common
  problems with what share of sites carry them, platforms, and which prospect signals are firing.

A finding present on 85% of sites is not a talking point, and a **prospect signal** firing on 85% of
sites is not a signal. That is how `outdated_site` got fixed: it originally included server-side TLS
and compression settings and fired on 11 of the first 12 sites, mozilla.org included.

## Engines

The scanner is an aggregator. Where a proven tool covers something, the tool is
authoritative and our own approximation is dropped from the report rather than shown alongside it.

Install them once: `./bin/setup-engines.sh` (no sudo; everything lands in `.engines/`).

| Engine | Licence | What it gives us | When it runs |
|---|---|---|---|
| **Mozilla HTTP Observatory** | third-party API | Independent, versioned security-header grade | always |
| **webanalyze** (Wappalyzer fingerprints) | MIT | CMS, plugins, frameworks **with versions** | always |
| **testssl.sh** (official Docker image) | GPLv2 | Full TLS config + the known TLS CVEs | `--deep` |
| **nuclei** | MIT | 13,600 templates, WP plugin CVEs | `--authorized` **only** |

### The tier boundary is a business rule, not a setting

`nuclei` is gated because it is not passive. Measured against one real prospect,
`-t http/technologies/` issued **1,040 HTTP requests** at 9 RPS, 113 of them errors from probing
paths that do not exist. That is directory probing and aggressive crawling — on MVP.md's own
forbidden list.

This is not theoretical. Running it during development got this machine **IP-banned by
factortrade.bg**, which now refuses our connections outright while every other site answers
normally. One prospect burned, from one test.

So `nuclei` requires `--authorized`, which is only for a customer who has signed permission, and
`--authorized` refuses to run against more than one target at a time. `--engines nuclei` is not a
way around the gate; a test enforces that.

## Version intelligence

```sh
vg-scan intel out --top 10          # enrich the ten best prospects
vg-scan intel out --no-cves         # end-of-life dates only
```

Looks the detected versions up against **endoflife.date** and **NVD**. Both are free and need no
key. Crucially it runs against saved scans and **never touches the prospect** — this is the depth the
intrusive scanners promised, without the traffic that got us firewalled.

Two rules the wording follows, and must keep following:

**End of life is a fact.** "PHP 7.4 stopped receiving security updates on 28 November 2022" is a date
anyone can check, it is about maintenance rather than accusation, and it is the strongest single line
available for a cold email.

**A CVE match is not a fact about them.** Distributions backport fixes without changing the version
string, and Bulgarian shared hosting usually runs distribution PHP. Findings therefore say
vulnerabilities *have been reported against this version*, never *your site is vulnerable* — which we
do not know and must not imply to a stranger. A test enforces that phrasing.

WordPress, Drupal and Joomla are never declared end-of-life: they backport security fixes to old
branches. The scanner's own output caught this — it called WordPress 6.1 dead while naming 6.1.12 as
its latest release. For those, the accurate and stronger claim is that the site is behind on the very
line it chose to stay on.

NVD allows 5 requests per 30 seconds without a key (50 with a free one, via `--nvd-key` or
`NVD_API_KEY`). Results cache by product and version, so a corpus where eleven sites share a
WordPress version costs one lookup, not eleven.

## What it checks

Availability (reachable, HTTPS, status) · TLS (trust, hostname, expiry, negotiated version, whether
TLS 1.0/1.1 are still accepted) · security headers (HSTS, CSP, X-Content-Type-Options,
Referrer-Policy, Permissions-Policy, clickjacking) · cookie flags · configuration (HTTP→HTTPS,
www/non-www, redirect loops, robots/sitemap/favicon) · technology (CMS, ecommerce, booking, exposed
versions, mobile viewport) · performance (first-response time, document size, compression).

## When a site blocks us

Bot protection answers 401/403/429 or serves a challenge page. That is not a broken website. The scan
sets `inconclusive`, withholds every finding it could not actually observe, shows a banner on the
report, and marks the CRM row `Needs manual review: yes`. **Never send an inconclusive report.**

Roughly one Bulgarian institutional site in five blocks us. Expect it, and check the tally line.

## Layout

```
src/vg_scanner/
├── cli.py           typer entrypoint: scan, summary
├── models.py        Finding, ScanResult, ProspectScore
├── probe.py         the only module that touches the network
├── context.py       gathers everything once, on a fixed request budget
├── content.py       cheap HTML fingerprinting
├── checks/          one module per category, each returning list[Finding]
├── scoring.py       pure: findings -> score, findings + context -> prospect score
├── aggregate.py     pure: many results -> the calibration view
├── catalog.py       the only file with prose in it: id -> text, per language
└── report.py        text, HTML and CSV renderers
```

Checks emit **an id plus params, never prose**. Adding a language means adding a key to `catalog.py`,
not touching a check. Tests fail if an emitted id has no text in every language, or vice versa.

## Dev

```sh
pytest                          # 47 tests, all offline
ruff check src tests
ruff format src tests
```

The whole suite runs against synthetic contexts, so weights can be re-tuned without waiting on
anyone else's web server.

## Gotchas worth knowing

- **`brotli` is a real dependency, not an optional one.** Without it httpx cannot decode `br`
  responses and every content check silently reports finding nothing. There is a test guarding this.
- Latency is one request from one location. Enough to start a conversation, not a performance audit.
  Measuring from WSL adds a little overhead versus a VPS, so treat the absolute numbers as indicative.
- The legacy TLS 1.0/1.1 probe depends on the **local** OpenSSL policy. Where the local library
  refuses to attempt those versions, the check reports *not tested* rather than *switched off* -
  it never invents a reassurance. Verified working on both Windows and Ubuntu 24.04.
- CMS detection is header- and markup-based. It finds WordPress reliably; it will miss a hidden one.
- We send `Accept-Language: bg`, so sites with content negotiation serve us their Bulgarian page.
  That is what a Bulgarian visitor sees, which is what we want - but it means **language and Cyrillic
  prove nothing about whether the business is Bulgarian**. The `local_bg_sme` signal therefore counts
  only a `+359` number, an ЕИК/БУЛСТАТ registration, or a `.bg` domain.
- **`catalog.py` has not been reviewed by a native Bulgarian speaker.** Do that before the first
  report is sent: every prospect-facing sentence lives in that file.

## Not done, on purpose

No PDF export, no testssl.sh, no ZAP passive integration. Python covers everything the sales report
currently uses, and none of the three is needed to start scanning prospects.
