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

- **Out-of-allowance work: €30/hour.** For anything larger, we write down what it involves and
  how long it will take, and start only after the customer approves. Set at €20 on 2026-08-27, then raised to €30 on 2026-08-28 after an outside
  review independently flagged €20 as under-priced. Originally drafted at €45. It sits below the Bulgarian freelance market rate and it caps what
  project work and the Infrastructure Care upsell can be quoted at later — revisit once there
  is real data on minutes per customer per month.
- **One-time onboarding: €49** — assessment, access setup, configuration. Waived for
  founding customers and on annual plans.
- **Annual plans: pay 10 months, use 12** (~17% off, the standard convention). Setup waived and
  the price locked for the term. €290 / €590 / €990.
  **Do not lead with it.** Nobody prepays a stranger twelve months, and the founding offer is
  the opposite motion. Sell annual as an upgrade at month 3–4, once the customer has seen two
  reports and ideally one handled incident — that is where the discount buys a renewal decision
  instead of trying to buy trust that has not been earned. Treat prepayments as **deferred
  revenue**: stopping in month four means owing roughly €400 back.
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
Against the originally drafted €45/hour that was underwater — 3 hours inside a €99 plan
prices support at €33/hour. The site publishes 30 and 60 minutes instead.

**That argument weakened when the rate dropped** (€45 → €20 → €30). At €30, three hours is
€90 of labour inside a €99 plan, which is close to break-even rather than clearly underwater. So the
tight allowances are now a *caution* rather than a necessity, and there is room to be more
generous than competitors once there is real data on minutes used per customer per month.
Generosity here is cheap and visible; the hourly rate is what has to stay defensible.

## Still to decide

- [ ] Company name check + domain purchase (repo name "Viridian Grids" is provisional)
- [ ] Terms of service, privacy policy and DPA — the website footer already names all three
- [ ] Payment processor (must handle EUR + Bulgarian invoicing requirements)
