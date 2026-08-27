# Viridian Grids — working context

Managed website monitoring & maintenance for Bulgarian SMEs, expanding later into servers,
networks, facilities and industrial monitoring. Started 2026-08-27 from an empty repo.
Full strategy lives in [MVP.md](MVP.md); do not restate it here, read it when strategy matters.

## Non-negotiable rules

1. **The public scanner is passive.** Against any domain we do not own and are not authorized on:
   HTTP/redirect behaviour, TLS inspection, security headers, cookie flags, header-based tech
   fingerprinting, robots/sitemap/favicon presence, latency and size estimates, ZAP *passive* only.
   Never fuzzing, SQLi/XSS, brute force, aggressive crawling, exploit attempts, authenticated scans
   or intrusive port scanning. Active checks live behind a per-customer authorization flag.
2. **No alarmism.** A missing CSP header is not a critical risk. Reports are one page, proportionate,
   and always carry: *"This is a public, non-intrusive website health assessment. Deeper security
   testing requires authorization."*
3. **Never say "we secure your website."** The positioning is *monitoring, maintenance and website
   security hygiene*. Deeper security is a separate, scoped, authorized engagement.
4. **Sell before building.** Manual onboarding until 10–20 customers. Do not build multi-tenancy,
   self-service provisioning, automated billing, a customer API or RBAC before ~20–30 customers.
   If asked for one of those, say what the manual alternative is first.
5. **EUR everywhere.** Bulgaria adopted the euro on 2026-01-01. No lev-denominated pricing or
   invoicing anywhere in code, docs or copy.
6. **Never commit customer credentials.** Hosting/WordPress access goes in a password manager,
   never in this repo, never in Ansible inventories in plain text.

## Stack

- Custom code: **Python 3.14 + FastAPI + SQLAlchemy + PostgreSQL**. Package manager: pip + venv.
- Monitoring plane: off-the-shelf OSS via Docker Compose on 1–3 VPSs — Uptime Kuma, Prometheus,
  Blackbox Exporter, Grafana, Alertmanager, Loki, Postgres. Later Zabbix, later still Mosquitto /
  Node-RED / Telegraf / VictoriaMetrics.
- Ops tooling: MainWP, Ansible, Restic, WireGuard.
- **No Kubernetes.** Do not propose it.
- Do not reimplement what Grafana/Prometheus/Zabbix already do — our app is the control plane.

## Conventions

- Python: `ruff` for lint+format, `pytest` for tests, type hints on public functions.
- Scanner checks are independent modules under `apps/scanner/src/vg_scanner/checks/`, each returning
  a normalized `Finding`; scoring is a separate pure function so it can be tuned without touching checks.
- Scanner output is JSON first; the human report renders from that JSON, never the other way round.
- Internal docs and code in English. Customer-facing copy, reports and outreach need Bulgarian.
- Windows dev machine, PowerShell primary, but **the scanner is run from WSL** (Ubuntu 24.04,
  Python 3.12) at `/mnt/d/code/viridian-grids`. Give shell examples in POSIX form by default.
- Separate venvs per platform: `.venv-linux` (WSL) and `.venv` (Windows). Neither is interchangeable.
- busybox `ls`/`find` reject GNU flags (`ls -la` fails) — use `ls -1a` or the Read/Glob tools.

## Environment notes

- Docker is not on PATH on this dev machine; the compose stack is meant for the VPS.
- `testssl.sh` and OWASP ZAP are external dependencies the scanner shells out to — both optional,
  the scanner must degrade gracefully when they are absent.
