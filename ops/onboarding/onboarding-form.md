# Onboarding form

Sent to the customer immediately after they subscribe. Everything is then configured **by hand** —
see [../../docs/roadmap.md](../../docs/roadmap.md) Gate 1. Needs a Bulgarian version.

## Business

- Company name (legal name for invoicing)
- VAT / EIK
- Invoicing address and email
- Plan: Monitor / Care / Business
- Business contact — name, email, phone
- Technical contact — name, email, phone (if different)

## The website

- Primary domain
- Additional domains / subdomains to monitor
- CMS and version (WordPress / other / custom)
- Ecommerce or booking system in use?
- Business-critical forms or checkout flows to monitor (list the URLs)
- Expected busy hours / seasonality
- Anything on the site we must never touch

## Hosting & access

- Hosting provider + control panel URL
- Domain registrar
- DNS provider
- WordPress admin access (**via password manager invite, never by email**)
- Hosting/SFTP/SSH access if required for the plan
- Existing staging environment?

## Backups

- Who currently takes backups, and where do they go?
- Retention?
- Has a restore ever been tested?
- Do we take over backups, or monitor theirs?

## Notifications & expectations

- Notification preference: email / phone / SMS / other
- Who should be alerted, and out of hours?
- Preferred maintenance window for updates
- Preferred language for reports (BG / EN)

## Authorization

- [ ] Customer confirms they own or are authorized to manage the listed domains
- [ ] Customer authorizes monitoring and maintenance as described in the plan
- [ ] Deeper security testing: **not** authorized by default — separate scoped agreement

## Internal checklist after the form comes back

- [ ] Credentials stored in the password manager (never in git)
- [ ] Uptime Kuma monitors created
- [ ] Blackbox targets added to Prometheus
- [ ] Alert routing configured
- [ ] Certificate expiry monitoring confirmed
- [ ] MainWP connected (WordPress customers)
- [ ] Backup monitoring / Restic configured per plan
- [ ] Baseline scan run and archived
- [ ] Customer row added to CRM with plan + MRR
- [ ] First monthly report scheduled
