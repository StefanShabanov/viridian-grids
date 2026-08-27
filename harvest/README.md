# vg-harvest

Builds the prospect list: Bulgarian businesses, in the verticals from
[../docs/icp-and-prospecting.md](../docs/icp-and-prospecting.md), that have a website worth
maintaining.

Feeds [../apps/scanner/](../apps/scanner/) directly.

## Where the domains come from

**OpenStreetMap, via the Overpass API.** Free, no key, and tagged by business type and town — so a
query returns *dentists in Bulgaria with a website*, not a heap of undifferentiated domains.

Two sources were tried first and rejected on evidence:

- **Top-lists (Majestic Million, Tranco).** Majestic contains 688 `.bg` domains and they are
  google.bg, government.bg, uni-sofia.bg and the ministries. Backlink rank will never surface a
  dentist in Plovdiv. Wrong tool for an SME list.
- **Certificate Transparency (crt.sh).** The right idea — every domain that ever got a certificate,
  including tiny ones — but its API and public database were both down while this was built, and CT
  gives undifferentiated domains with no vertical, no town and no phone number. Worth adding later as
  a breadth source; it cannot be the primary one.

## Use

```sh
source ../apps/scanner/.venv-linux/bin/activate
pip install -e .

vg-harvest verticals                              # what can be harvested
vg-harvest collect dentist hotel                  # two verticals
vg-harvest collect --all                          # everything, paced
vg-harvest stats                                  # what the list holds now
```

Then scan what it produced:

```sh
cd ../apps/scanner
vg-scan scan -f ../../harvest/data/domains.txt --no-engines -o triage -w 8
```

Re-running `collect` **merges**; it never replaces. Raw Overpass responses are cached under
`data/cache/`, so a second run costs nothing. `--refresh` re-queries.

## What gets filtered out, and why

| Dropped | Reason |
|---|---|
| Facebook / Instagram / LinkedIn pages | Not a website. We cannot monitor, update or back up someone else's Facebook, and offering to would be dishonest |
| booking.com / superdoc.bg / directory listings | The business does not control it |
| `kornelia-petkova.add.bg` style subdomains | A template page on a hosting provider. Nothing to maintain, and usually nobody who can authorize us |
| Duplicate domains | Two dentists on one domain is a chain — one contract, one row |

Pass `--keep-shared` to keep the hosted-subdomain ones.

## Being a good citizen

Overpass is donated infrastructure with a two-slot-per-client limit. Asking for every vertical in one
query was refused outright by its dispatcher timeout, so this queries **one vertical at a time**,
paces requests, backs off on overload, and caches everything. Do not remove that pacing.

## The output is personal data

`data/prospects.csv` holds names, phone numbers and email addresses of identifiable people,
processed under legitimate interest for B2B outreach. It is gitignored and must stay that way.
Honour opt-outs immediately and permanently, and make sure the privacy policy describes this
processing before the first email goes out. See [../docs/icp-and-prospecting.md](../docs/icp-and-prospecting.md).

## What this does not do

It finds businesses with websites. It does not decide whether they are worth contacting — that is the
scanner's prospect score, and then your judgement. A harvest of a thousand domains does not get you
one extra email: you can write ten personalized ones a day. Use this to fill the vertical lists the
plan asks for, not to replace choosing verticals.
