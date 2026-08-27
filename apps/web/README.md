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
- [ ] Privacy policy, Terms and DPA do not exist. The footer names all three.
- [ ] `hello@viridiangrids.com` and the domain are placeholders — see the naming decision.
- [ ] `style-src` still needs `'unsafe-inline'` because components use inline `style` attributes. Moving them into `global.css` would let the CSP tighten, which is worth doing on a site that sells header hygiene.
- [ ] No OG image.
