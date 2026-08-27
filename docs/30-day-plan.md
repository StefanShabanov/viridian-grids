# First 30 days — starting 2026-08-27

The single most important instruction in this plan: **Week 4 is when you stop building and start
prospecting.** Do not let Week 2 expand into Week 5.

## Week 1 — 27 Aug – 2 Sep: decide and provision

**Business**
- [ ] Confirm company name, check availability, buy domain
- [ ] Basic branding (logo, colours, one-page identity)
- [ ] Lock the €29 / €59 / €99 package definitions — see [offer-and-pricing.md](offer-and-pricing.md)
- [ ] Write terms of service
- [ ] Write down exactly what is and is not included per tier
- [ ] Decide hourly rate for out-of-allowance work
- [ ] Choose payment processor (EUR, Bulgarian invoicing)

**Technology**
- [ ] Provision VPS
- [ ] Install Docker + Compose
- [ ] Bring up Uptime Kuma
- [ ] Bring up Prometheus + Blackbox Exporter
- [ ] Bring up Grafana
- [ ] Bring up Alertmanager
- [ ] External uptime check on our own stack

## Week 2 — 3–9 Sep: build the scanner

Started early, on 27 Aug. Most of it is done:

- [x] Scanner CLI skeleton + normalized JSON output
- [x] HTTP/availability + configuration checks
- [x] TLS checks (Python: validity, expiry, protocol, legacy TLS 1.0/1.1)
- [x] Security header + cookie checks
- [x] Technology fingerprinting + prospect scoring
- [x] Basic scoring algorithm — conservative weights, no alarmism
- [x] One-page HTML report, English and Bulgarian
- [x] Batch mode + CRM-shaped CSV export
- [x] Corpus aggregation (`vg-scan summary`) for tuning weights against real sites
- [x] testssl.sh integration (official Docker image, `--deep`)
- [x] webanalyze (Wappalyzer fingerprints) for CMS/plugin versions
- [x] Mozilla HTTP Observatory for an independent header grade
- [x] nuclei wired but gated behind `--authorized` (1040 requests/host: customers only)
- [ ] HTML → PDF
- [ ] Passive ZAP integration *only if it earns its place*

Spec: [scanner-spec.md](scanner-spec.md). Usage: [../apps/scanner/README.md](../apps/scanner/README.md).

**Before the first report goes out:** have a Bulgarian speaker review `catalog.py`. Every prospect-facing
sentence lives in that one file, and it was written without a native review.

## Week 3 — 10–16 Sep: website and sales assets

**Website**
- [ ] Homepage — *"Your website should work when your customers need it."* / *"Monitoring, updates,
      backups and troubleshooting for Bulgarian businesses."* CTA: **Check my website**, secondary: **See plans**
- [ ] Pricing page with real prices visible — do not hide everything behind "contact us"
- [ ] Free Website Check form (URL, name, email, company) → queues a report, does **not** auto-send
- [ ] How it works: 1) we check your website 2) we set up monitoring 3) we handle maintenance
      4) you receive monthly reports
- [ ] Security / FAQ page: what we monitor, where credentials are stored, what we don't do without
      permission, backups, GDPR, cancellation, response expectations
- [ ] Contact page
- [ ] Privacy policy + GDPR basics (must cover the CRM processing before any outreach)
- [ ] Bulgarian copy throughout

**Sales assets**
- [ ] Branded one-page report template (EN + BG)
- [ ] Onboarding form — [../ops/onboarding/onboarding-form.md](../ops/onboarding/onboarding-form.md)
- [ ] Prospect CRM from [../ops/crm/prospects.template.csv](../ops/crm/prospects.template.csv)

## Week 4 — 17–24 Sep: stop building

**Seriously. Stop.**

- [ ] Assemble the first 100 prospects using the vertical mix in [icp-and-prospecting.md](icp-and-prospecting.md)
- [ ] Scan them, score them, rank them
- [ ] Start outreach — [outreach-playbook.md](outreach-playbook.md)

## Days 30–60 — from 25 Sep

Daily rhythm: **10 new prospects every working day** (~200/month). For each:

```
find company → scan website → manually inspect results → identify one useful observation
→ contact → record result
```

Also:
- [ ] Contact 10–20 web agencies / freelancers about white-label maintenance
- [ ] Post educational content in relevant Facebook groups
- [ ] Contact the existing network
- [ ] Try direct calls
- [ ] Offer 3–5 early-adopter slots (€39/mo for 3 months + free onboarding)

## Definition of done for the MVP

The MVP is complete the moment there is:

website + safe scanner + monitoring stack + onboarding process + billing + first real prospect list.

Everything after that is driven by what actual prospects and customers ask for.
