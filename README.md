# Viridian Grids

Managed monitoring and maintenance for Bulgarian SMEs — websites first, infrastructure later.

> **We monitor the systems your business depends on and help keep them running.**

This repo holds the business plan, the operational docs, the monitoring stack definition, and the
small amount of custom software the service actually needs.

## Where things live

| Path | What it is |
|---|---|
| [MVP.md](MVP.md) | The original full business plan. Source of truth for strategy. |
| [docs/](docs/) | Working docs derived from the plan: offer, ICP, scanner spec, roadmap, 30-day plan. |
| [infra/](infra/) | Docker Compose monitoring stack + Ansible for repeatable maintenance. |
| [apps/scanner/](apps/scanner/) | `vg-scan` — the non-intrusive website health scanner. Python. |
| [apps/api/](apps/api/) | Internal control-plane API. **Deliberately empty until ~20 customers.** |
| [apps/web/](apps/web/) | Marketing site — Astro, Bulgarian + English, deployed to Vercel. See its [README](apps/web/README.md). |
| [harvest/](harvest/) | `vg-harvest` — builds the prospect list from OpenStreetMap, by vertical. |
| [ops/](ops/) | Onboarding form, prospect CRM template, report templates. |

## The plans

| Plan | Price | For |
|---|---|---|
| Monitor | €29/mo | Entry — monitoring only, no repair work included |
| Care | €59/mo | Main product — monitoring + WordPress upkeep + 30 min support |
| Business | €99/mo | Ecommerce/booking — everything + priority + 60 min support |

Prices are in EUR and invoiced in EUR. See [docs/offer-and-pricing.md](docs/offer-and-pricing.md).

## Two rules that govern this repo

1. **The public scanner is passive.** Never run active/intrusive tests against a site we do not own
   and have not been authorized on. See [docs/scanner-spec.md](docs/scanner-spec.md).
2. **Sell before building.** Custom software gets written only when manual repetition proves it is
   needed. See [docs/roadmap.md](docs/roadmap.md).

## Getting started

```sh
# scanner, from WSL
cd apps/scanner
python3 -m venv .venv-linux && source .venv-linux/bin/activate && pip install -e ".[dev]"
vg-scan scan example.bg

# monitoring stack (needs Docker on the VPS; not installed on the dev machine yet)
cd infra/compose && cp .env.example .env && docker compose up -d
```

Windows/PowerShell setup and everything else the scanner does:
[apps/scanner/README.md](apps/scanner/README.md).
