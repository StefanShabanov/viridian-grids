# Offer & pricing

**The offer, in one sentence:** we continuously monitor your website, keep it updated and backed up,
and help when something breaks.

Not "cybersecurity consultancy", not "DevOps", not "digital transformation", not "IoT". Those come later.

All prices in **EUR**, invoiced in EUR.

## Monitor — €29/month

Entry product. Must be near-fully automated; if it isn't, it loses money.

- Uptime monitoring
- SSL certificate expiry monitoring
- DNS / HTTP availability
- Response-time monitoring
- Basic security-header monitoring
- Monthly report
- Notification if a major problem is detected

**Not included: any repair work.** If something breaks → hourly rate or fixed quote.

## Care — €59/month

Expected to become the main product.

- Everything in Monitor
- WordPress core / plugin / theme updates
- Backup monitoring
- Backup verification
- Basic security checks
- Basic performance monitoring
- **30 minutes/month troubleshooting**
- Monthly report

Work beyond the allowance is billed separately.

## Business — €99/month

For ecommerce, booking systems and business-critical sites.

- Everything in Care
- More frequent checks
- Checkout / form monitoring
- Priority response
- **60 minutes/month troubleshooting**
- Database / server monitoring where possible
- Staging + testing before risky updates
- More detailed monthly report

**Do not promise 24/7 human incident response at this price.**

## Founding-customer offer

> Founding customers receive free onboarding and their first three months discounted.

First 3 months at €39/mo, then normal €59. Time-limited, **not** a lifetime discount — never create a
"€19 forever because I was customer #2" account.

## Billing rules

- Out-of-allowance work: hourly rate or fixed quote agreed **before** the work starts.
- Included minutes do not roll over.
- Track support minutes per customer from day one — see [roadmap.md](roadmap.md#the-metric).

## Later: Infrastructure Care — €199–399/month

Sold to *existing* website customers when they ask "can you also monitor our VPS?" Covers Linux
(and Windows where appropriate), CPU/RAM/disk, databases, Docker, backups, NAS, VPN, router,
internet, UPS. Turns a €59 customer into a €299 customer — this is where the economics improve.

## Published on the website

[apps/web](../apps/web/) states these publicly, so they are now commitments rather than
drafts. Changing one means changing both files in the same commit.

- **Out-of-allowance work: €45/hour**, or a fixed quote agreed before the work starts.
- **One-time onboarding: €90** — assessment, access setup, configuration. Waived for
  founding customers and on annual plans.
- **Response times**, per tier:

  | | Monitor | Care | Business |
  | --- | --- | --- | --- |
  | Site down — we start investigating | 60 min | 30 min | 15 min |
  | Coverage window (Mon–Fri) | 09:00–18:00 | 08:00–20:00 | 07:00–22:00 |
  | Non-urgent request reply | 2 business days | 1 business day | 4 business hours |

  Monitoring runs 24/7 and overnight alerts are recorded; human response starts at the
  beginning of the next window. The design mock proposed seven-day coverage on Business —
  105 hours a week for one person. Five days is what a solo operator can actually honour.

**Note on allowances.** The design mock offered 1 hour on Care and 3 hours on Business.
That would price Business support at €33/hour against our own €45/hour rate. The site
publishes the numbers above — 30 and 60 minutes — deliberately. Revisit once there is
real data on minutes per customer per month.

## Still to decide

- [ ] Company name check + domain purchase (repo name "Viridian Grids" is provisional)
- [ ] Terms of service, privacy policy and DPA — the website footer already names all three
- [ ] Payment processor (must handle EUR + Bulgarian invoicing requirements)
