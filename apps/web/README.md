# apps/web — the marketing site

Bulgarian-first, English second. Built from the Claude Design mock
(`Website monitoring for SMEs.zip` in the repo root), which stays the reference for
colours, type and layout.

```sh
npm install
npm run dev      # http://localhost:4321
npm run build    # writes .vercel/output
npm run check    # astro + typescript diagnostics
```

## Deploying

Vercel, **Root Directory `apps/web`**. Not the VPS: the VPS exists to deliver the
service and should be able to restart without taking the sales site down. Vercel
also gives clean TLS and headers for free, which matters more here than usual —
prospects will point our own kind of check back at us.

Environment variables (see `.env.example`):

| Variable | Why |
| --- | --- |
| `LEAD_TO_EMAIL` | Where both forms are delivered. |
| `RESEND_API_KEY` | Mail provider. Without it, submissions are **rejected**, not silently dropped. |
| `LEAD_FROM_EMAIL` | Verified sender in Resend. |
| `SITE_URL` | Canonical origin, once the domain is bought. |

## Structure

| Path | What |
| --- | --- |
| `src/content/site.ts` | Prices, rates, page list, slugs, which sections each page shows. |
| `src/content/bg.ts` · `en.ts` | All copy. `bg.ts` is type-checked against `en.ts`, so a key added to one must be added to the other. |
| `src/pages/[...path].astro` | Every page, both languages, from `PAGES` × `LANGS`. |
| `src/components/*.astro` | One per section of the design. |
| `src/pages/api/*.ts` | The two form endpoints (serverless). |
| `vercel.json` | Security headers. |

## Two deliberate departures from the mock

**1. The free check is a form, not a live scanner.** The mock typed a URL, played a
scan log, and printed results. Here the same page collects the URL and emails the
request; the scan is run by hand with `vg-scan` and reviewed before it is sent.
Three reasons, in order of weight: an unauthenticated public scan endpoint points
our infrastructure at any domain a stranger names (we have been IP-banned twice
already by accident); MVP.md requires a human to review every report; and the
scanner shells out to Docker and webanalyze and takes 5–20s, which does not fit in
a serverless function. The example results are still shown — labelled as an example,
because printing invented numbers under a visitor's own domain would be a lie, and
the entire offer rests on the report being true.

Wire the real flow at Gate 2: form → queue on the VPS → worker → approval → send.

**2. Troubleshooting allowances and coverage follow `docs/offer-and-pricing.md`,
not the mock.** The mock offered 1h on Care and 3h on Business, and a seven-day
coverage window. The doc says 30 and 60 minutes, five days. Three hours inside a
€99 plan prices the included work at €33/hour against a published €45/hour rate.
The doc's numbers are in the site; changing them means changing both files.

## Known gaps before launch

- [ ] **Bulgarian copy has not been reviewed by a native speaker.** Same gate as `catalog.py`.
- [ ] **The three legal pages need a lawyer.** `/poveritelnost`, `/usloviya` and `/obrabotvane-na-danni` are written and accurate about what the site does — two forms, no cookies, two processors — but they are not legal advice and nobody qualified has read them.
- [ ] **`legal.entity` is a placeholder.** It must carry the registered company name, ЕИК and registered address before the privacy notice is lawful.
- [ ] `hello@viridiangrids.com` and the domain are placeholders — see the naming decision.
- [ ] `style-src` still needs `'unsafe-inline'` because components use inline `style` attributes. Moving them into `global.css` would let the CSP tighten further.
- [ ] No OG image.

## Per-client pages

A prospect gets a link and a six-digit code in the same email:

```
https://viridiangrids.com/r/<slug>     their initial report
https://viridiangrids.com/d/<slug>     a browsable demo of a rebuilt site
```

```sh
node bin/client.mjs add "Hotel Chiflika" hotelchiflika.com   # prints URL + code, once
node bin/client.mjs demo <slug> "../../Web-demos/hotel chiflika.zip" <code>
node bin/client.mjs report <slug> ../scanner/out/thatsite.json <code>
node bin/client.mjs list
```

`add` prints the code once and never stores it — only key material derived from it.
Put it straight into the email; losing it means re-adding the client.

**How the gate works.** The page ships only ciphertext. The code plus the page salt
derives an AES-GCM key (PBKDF2, 600k iterations) and the browser decrypts on entry;
a wrong code simply fails to decrypt. Nothing readable sits in the HTML. For demos
what is encrypted is the *folder path*, so the demo cannot be found without the code
either. All of it is static — no server, no session, no database.

**What it is not.** Six digits is a million combinations, which would not survive a
determined offline attack on its own. That is why the slug carries 128 bits of
randomness: an attacker needs the link *and* the code, and the link only comes from
your client. Proportionate for a report about someone's own public website — not a
vault, and it should not be described as one.

| Path | Holds |
| --- | --- |
| `Web-demos/*.zip` | Where you drop exports. Gitignored — source material, not output. |
| `clients/<slug>/client.json` | Name, domain, sealed report and demo. Committed. |
| `public/demo/<token>/` | The extracted demo, under an unguessable folder name. |

`/r/`, `/d/` and `/demo/` are excluded from the sitemap, disallowed in `robots.txt`
and carry `noindex`. `/demo/` also gets a looser CSP in `vercel.json`, because a
Claude Design export needs inline scripts to run — the strict policy still applies
to every other path.

## Promises this site makes that need a procedure behind them

The site is deliberately specific, which is what makes it credible — and which means
every line below is a commitment from customer #1, not from customer #20. Walk this
list before the first onboarding, not after.

| Promised on the site | Needs to exist |
| --- | --- |
| Signed DPA at onboarding | The actual document, not just the page describing it |
| Encrypted vault, 2FA | The password manager, set up, with the account structure decided |
| Backups encrypted at rest, EU, separate from hosting | The object storage and the Restic policy |
| Documented retention period | A number, written down, that matches the privacy notice |
| Access removed, confirmed in writing within 5 working days | A checklist so it happens under pressure |
| Written list of required access before onboarding | The template |
| Breach notification without undue delay | Knowing who you tell and how fast |
| Alerts by email **and SMS** (Monitor tier) | An SMS provider — currently nothing sends SMS |
| Checks every 5 min / 1 min / 30 sec | The VPS and Uptime Kuma |
| Investigation starts in 60 / 30 / 15 min | Alerting that actually wakes you, and the coverage discipline |
| Monthly PDF report on the 1st | A generator; the scanner renders HTML today |
| One restore test per month (shown in the sample report) | The procedure, and somewhere to restore to |
| Forms & checkout tested end to end (Business) | Synthetic checks configured per customer |

Two of these are load-bearing and currently missing entirely: **SMS alerting** and the
**monthly PDF**. Both are promised on the pricing page.

## Fonts

IBM Plex is self-hosted through `@fontsource`, imported at the top of `global.css`.
Not from Google: the visitor's browser then contacts no third party, which is what
lets the privacy notice say so plainly; the CSP drops two external origins; and the
page stops depending on someone else's uptime. Each face carries a `unicode-range`,
so a Bulgarian reader downloads Cyrillic and an English one does not.
