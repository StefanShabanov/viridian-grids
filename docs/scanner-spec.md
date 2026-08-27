# Scanner spec — `vg-scan`

The scanner is an **aggregator**, not a scanning engine. It orchestrates a few HTTP requests and two
external tools, normalizes the output, scores it, and renders a one-page report.

```
             Domain
                ↓
         Scanner service
                ↓
   ┌────────────┼────────────┐
   ↓            ↓            ↓
 HTTP       testssl.sh      ZAP
 checks        TLS        passive
   ↓            ↓            ↓
   └────────────┼────────────┘
                ↓
          normalize data
                ↓
           score findings
                ↓
          generate report
```

## This is an aggregator

External engines are authoritative; our own Python checks fill the gaps nothing else covers
(redirect behaviour, www/non-www, blocked-request detection, favicon declaration). Where an engine
covers the same ground, our version is dropped from the output — see `supersedes` in
`engines/base.py`.

| Tier | Engines | May be pointed at |
|---|---|---|
| prospecting | Observatory, webanalyze, testssl.sh | anyone, unannounced |
| authorized | nuclei (later: ZAP active, WPScan) | customers with signed permission only |

The split is measured, not assumed: nuclei's technology templates alone issue **1,040 requests** per
host. During development that got the dev machine IP-banned by a live prospect. Anything in the
authorized tier is capable of the same.

## Rule zero — passive only

Against any site we do not own and have not been explicitly authorized on, the scanner performs
**non-intrusive checks only**. OWASP ZAP documents active scanning as an attack that must not be
pointed at applications you do not own; we honour that.

**Never, without written authorization:** password attacks, fuzzing, SQLi testing, XSS testing,
directory brute forcing, aggressive crawling, exploit attempts, authenticated scanning, intrusive
port scanning.

Once a prospect becomes a customer and authorizes it in writing, deeper assessment is a separate,
scoped engagement — implemented behind a per-target `authorized` flag, never in the public path.

Also: identify ourselves in the User-Agent, respect a low request budget per domain, and rate-limit.

## Checks

### Availability
- HTTP status
- HTTPS reachable
- Redirect behaviour
- Response time

### TLS
- Certificate validity
- Days to expiry
- Protocol configuration
- Obvious TLS weaknesses

### HTTP headers
- HSTS
- CSP
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy

### Cookies
- Secure
- HttpOnly
- SameSite

### Technology
- Obvious CMS detection
- Server headers
- Exposed technology/version information

### Configuration
- www / non-www behaviour
- HTTP → HTTPS enforcement
- Obvious redirect loops
- robots.txt / sitemap.xml / favicon availability

### Performance
- Initial request latency
- Page-size estimate where appropriate

## Output contract

JSON first. The report renders from the JSON; never the reverse.

```jsonc
{
  "domain": "example.bg",
  "scanned_at": "2026-08-27T10:00:00Z",
  "scanner_version": "0.1.0",
  "score": 74,
  "inconclusive": false,
  "findings": [
    {
      "id": "http.hsts_missing",
      "category": "http",          // availability|tls|http|cookies|technology|configuration|performance
      "severity": "medium",        // info|low|medium|high
      "status": "warn",            // pass|warn|fail|info|skipped
      "title": "HSTS not configured",
      "detail": "No Strict-Transport-Security header on https://example.bg",
      "evidence": {"header": null},
      "weight": 5
    }
  ],
  "prospect_score": {"total": 14, "max": 17, "signals": [{"name": "wordpress", "points": 3}]},
  "errors": []
}
```

Each check is an independent module under `src/vg_scanner/checks/` returning `list[Finding]`.
Scoring is a **separate pure function** over findings so weights can be tuned without touching checks.
A check that cannot run (tool missing, timeout) returns `status: "skipped"` — it never fails the scan.

Checks emit an **id plus params, never prose**. Text lives in `catalog.py`, keyed by id and language,
which is what keeps the English and Bulgarian reports in sync. A test fails the build if any emitted
id has no catalog entry in every language, or if the catalog carries an id nothing emits.

Findings never make requests. Everything the checks need is gathered once, in `context.py`, on a fixed
request budget of under ten requests per domain. If you want to know what we did to someone's server,
that one file is the whole answer.

## Blocked requests are not findings

Bot protection returns 401/403/429, or a challenge page behind a 503. That is **not** a broken website,
and reporting it as one puts a false accusation in front of a prospect. When it happens the scan sets
`inconclusive: true`, the availability finding becomes `availability.request_blocked` (skipped, no
weight), and dependent checks such as robots/sitemap/favicon are skipped rather than reported missing.
Every renderer shows a banner, and the CRM row carries `Needs manual review: yes`.

This was not theoretical: the first batch run scored `sofia.bg` at 59/100 with "Homepage returns an
error" as the headline finding, purely because it blocks automated requests. It scores 82 now.

## Scoring

Start simple: 100 minus the sum of weights of failed/warned findings, floored at 0.
Keep weights conservative and proportionate.

**Do not** produce dramatic output. `CRITICAL SECURITY RISK!!!! 38/100` for a missing header destroys
the trust the whole sales motion depends on.

## Report

One page. Overall score, a short list of ✅ passes and ⚠ observations, plain language.

```
example.bg Website Health Check

Overall: 74/100

✅ HTTPS configured
✅ Certificate valid
✅ HTTP redirect working

⚠ CSP missing
⚠ HSTS missing
⚠ Server technology exposed
⚠ Initial response: 2.6 seconds
⚠ Certificate expires in 38 days
```

Every report ends with, verbatim:

> This is a public, non-intrusive website health assessment. Deeper security testing requires authorization.

A Bulgarian-language version of the report template is required before outreach starts.

## Manual review gate

For the launch period, **every report is reviewed by a human before it is sent.** The free-check form
on the website queues a report; it does not auto-email results. This prevents embarrassing false
positives in front of prospects. Automate the send only once the false-positive rate is known.

## External dependencies

Both optional; the scanner degrades gracefully and marks checks `skipped` when they are absent.

- `testssl.sh` — TLS configuration analysis
- OWASP ZAP — **passive** scanner only

## Build order

1. ~~HTTP/availability + configuration checks (pure Python, no external tools)~~ **done**
2. ~~TLS via Python `ssl`/`cryptography` for validity, expiry and protocol~~ **done**;
   testssl.sh for cipher-level depth still to do
3. ~~Header + cookie checks~~ **done**
4. ~~Technology fingerprinting + prospect scoring~~ **done**
5. ~~JSON → one-page report renderer~~ **done** (HTML); HTML → PDF still to do
6. ZAP passive, only if it earns its place — **not started, and possibly never needed**

## Calibration

Scoring is a pure function over findings, and `aggregate.py` is a pure function over many results.
Together they mean weights can be re-tuned against a saved corpus without making a single request:

```sh
vg-scan scan -f prospects.txt -o out      # once
vg-scan summary out                       # as often as you like
vg-scan scan somesite.bg -v               # the arithmetic for one site
```

Two rules that came out of the first corpus run:

- A **finding** present on 85% of sites is not a talking point for outreach.
- A **prospect signal** firing on 85% of sites is not a signal. `outdated_site` originally included
  server-side TLS and compression settings; it fired on 11 of the first 12 sites, mozilla.org
  included, and now covers only things that make the site itself look dated.

A site that never answered has no health to report. An unreachable domain scored 57/100 - above a
live 15/17 prospect at 43 - which put dead businesses in the middle of the ranked list. Unreachable
now floors the score, and the two causes are separated because they mean opposite things: **no DNS
record** means the domain lapsed and the business is probably gone (drop it), while a **refused
connection or timeout** means the domain is still paid for and the server is down (call them today).

Absence must be established, never inferred, and it must be established the way a browser would.
A missing `/favicon.ico` is not a missing favicon: almost every site points at its icon with
`<link rel="icon">`, and we were reporting well-run shops as having none. The page is consulted first
and the request is skipped entirely when it already answers the question.

Absence must be established, never inferred. A 404 means a file is missing; a 500, a timeout or a
blocked request means we did not find out. Reporting the second as the first put "Sitemap is missing
(HTTP 500)" in front of a real prospect whose sitemap was probably fine.

Certificate expiry is judged against the certificate's own validity period, not a fixed threshold.
A ~90-day certificate comes from an automated ACME client that renews at about 30 days, so warning
at 45 is noise; the same certificate at under 10 days means the automation has broken, which is a
genuinely useful alert. Manually-renewed year-long certificates keep the 45-day warning.

Watch `missing_headers` too - it currently fires on roughly three quarters of sites, which is close
to the point where it stops discriminating between prospects.

### Known gaps

- No PDF output yet. The HTML prints cleanly, so this is a convenience, not a blocker.
- No testssl.sh integration. Python covers validity, expiry, negotiated version and whether TLS 1.0/1.1
  are still accepted, which is everything the sales report actually uses.
- CMS detection is header- and markup-based. It finds WordPress reliably; it will miss a well-hidden one.
- `brotli` is a hard dependency. Without it httpx cannot decode `br` responses, and every content
  check silently reports finding nothing rather than failing. A test guards this; do not remove it.
- Latency is one request from one location. Enough to start a conversation, not a performance audit.
