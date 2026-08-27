# ICP & prospecting

## Who we sell to

Businesses where the website actually matters — it takes bookings, generates leads, or sells.

- Hotels and guest houses
- Clinics / dentists
- Accountants / law firms
- Real-estate agencies
- Small ecommerce stores
- Restaurants with booking or ordering
- Service businesses receiving leads through forms
- Small manufacturers with catalogue/contact sites
- Local companies running WordPress

## Who we don't

Hobby sites, and any business whose owner fundamentally does not care whether the website works.
No amount of scan findings fixes indifference.

## First 100 prospects — deliberate mix

Do not assume hotels are the best vertical. Build a spread, then let conversion data decide.

| Vertical | Count |
|---|---|
| Hotels / guest houses | 30 |
| Dentists / clinics | 20 |
| Professional services (accountants, lawyers) | 20 |
| Ecommerce | 20 |
| Other local SMEs | 10 |

Target for the first validation milestone: **250 carefully selected prospects.**

## Prospect scoring

The scanner ranks who is worth 15 minutes of personalized outreach.

| Signal | Points |
|---|---|
| WordPress | +3 |
| WooCommerce | +3 |
| Slow response time | +2 |
| Missing important security headers | +2 |
| Outdated-looking site | +2 |
| Business-critical form | +2 |
| Booking / ecommerce functionality | +2 |
| Local Bulgarian SME | +1 |

"Local Bulgarian SME" means a `.bg` domain, a `+359` phone number, or an ЕИК/БУЛСТАТ registration on
the page — not Bulgarian text. Plenty of Bulgarian SMEs sit on `.com`, and conversely the scanner asks
for Bulgarian content, so a multinational will happily serve it a Bulgarian page.

These sum to **17**, so the scanner reports out of 17 rather than the 15 first sketched in the plan.

High score (e.g. 14/17) → personalized outreach. A fast, perfectly-configured static 3-page brochure
site that sells nothing online is probably not worth contacting.

## Building the list

[../harvest/](../harvest/) turns OpenStreetMap into a prospect list, by vertical, with websites,
towns and phone numbers:

```sh
cd harvest
vg-harvest collect dentist hotel guest_house lawyer accountant estate_agent
vg-harvest stats
```

Two sources were tried and rejected on evidence, so nobody repeats the work:

- **Top-lists (Majestic, Tranco)** hold 688 `.bg` domains, and they are google.bg, government.bg,
  uni-sofia.bg and the ministries. Backlink rank never surfaces a local SME.
- **Certificate Transparency (crt.sh)** is the right idea for breadth but was down when this was
  built, and gives domains with no vertical, town or phone number attached.

The harvester finds businesses with websites. It does not decide who is worth contacting - that is
the scanner's prospect score, then your judgement. A thousand harvested domains do not buy one extra
email; you can write ten personalized ones a day.

## CRM

One row per prospect. Template: [../ops/crm/prospects.template.csv](../ops/crm/prospects.template.csv).
A spreadsheet is the correct tool here — do not build a CRM. Copy the template to
`ops/crm/prospects.csv` (gitignored, it holds personal data).

Columns: Company, Domain, Industry, City, Email, Phone, Decision maker, Website platform, Scan score,
Interesting finding, Contacted, Follow-up 1, Follow-up 2, Response, Meeting, Trial, Customer, MRR, Notes.

## GDPR note

The CRM holds personal data of identifiable people (decision makers) processed under legitimate
interest for B2B outreach. Keep it out of git, honour opt-outs immediately and permanently, and make
sure the privacy policy on the site describes this processing before the first email goes out.

## Funnel expectations

These are signal, not benchmarks:

```
250 prospects → 150 contacted → 20–40 conversations → 10–15 serious discussions → 3–8 customers
```

If 250 targeted SMEs produce nobody willing to pay €29–59/month, the problem is one of:
target audience, pain, positioning, credibility, pricing, or sales approach. Find out which
**before** building a platform.
