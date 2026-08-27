# Roadmap — and the gates that control it

The point of this document is to say **what is not allowed to be built yet.**

The business is service-first. Revenue arrives at every stage. Custom software is written only when
manual repetition has proven it is needed.

## Gates

### Gate 0 — now → first customer

Build: scanner + one-page report + marketing site + monitoring stack + onboarding form + billing +
prospect list. That's it. That is the *real* MVP.

Everything else is off-the-shelf.

### Gate 1 — first 10–20 customers: onboard manually

Onboarding is: customer subscribes → send onboarding form → configure everything by hand.

**Do not build** in this window:
- self-service agent installation
- automatic tenant creation
- automated billing provisioning
- customer-facing API
- complex RBAC
- SaaS provisioning

Do it 10–20 times by hand. Then you know exactly what deserves automation.

### Gate 2 — 10 customers / €500–800 MRR: automate exactly one thing

Do not celebrate by rebuilding the backend. Ask: what takes the most of my time? WordPress updates?
Reports? Onboarding? Alerts? Billing? Credential management? Automate whichever one hurts. One.

### Gate 3 — 20–30 customers: build the platform

Now the internal control plane is justified:

```
      Web UI
         ↓
    API / backend
         ↓
     PostgreSQL
         ↓
  ┌──────┴──────┐
  ↓             ↓
Customer     Job system
 config          ↓
             scan workers
                 ↓
    ┌────────────┼────────────┐
    ↓            ↓            ↓
HTTP checks   testssl   passive checks
```

Manages: tenants, domains, subscriptions, scan history, monitoring configuration, findings, reports,
tickets, alert routing. It does **not** replace Grafana.

### Gate 4 — customers ask about servers

Infrastructure Care, €199–399/mo. Add Zabbix once there is real traditional infrastructure
(SNMP, switches, routers, UPS, NAS, IPMI, VMware).

### Gate 5 — real customer demand for facilities

IoT/facility monitoring: Mosquitto, Node-RED, Telegraf, ESPHome, VictoriaMetrics. Sell to
**commercial** property first — hotels, warehouses, restaurants, offices, guest houses, Airbnb
portfolios — not individual apartment owners at €9.99/mo. Roughly €300 setup + €99/mo for
server-room temperature, leak detection, UPS, internet, freezer temperature.

### Gate 6 — industrial

Much later. Modbus, RS485, OPC-UA, PLC integrations, industrial gateways, power meters, vibration,
machine runtime, counters.

## Expansion path

```
Website Monitoring → Website Maintenance & Security Hygiene → Server/VPS Monitoring
→ Networks/NAS/Routers/UPS → Business Hardware → IoT/Facility Monitoring
→ Hotels/Warehouses/Commercial Property → Industrial → Machines/PLC/Modbus/OPC-UA
```

The underlying concept never changes:

```
System/Device → collect metrics & events → store and analyze → detect problems
→ alert → troubleshoot/automate → report to customer
```

## The metric

**MRR per support hour.** Not traffic, not scan count, not dashboard count.

| Customer | MRR | Support/month | Verdict |
|---|---|---|---|
| A | €59 | 8 min | excellent |
| B | €99 | 35 min | good |
| C | €29 | 3.5 h | problem |

Improve the product around this. Track support minutes per customer from the first customer.

## Milestones

| Horizon | Target |
|---|---|
| Days 30–60 | 10 new prospects per working day (~200/month); 10–20 agency/freelancer contacts |
| Months 3–6 | 10–20 paying customers; review MRR, avg revenue, hours/customer, acquisition source, response/meeting/trial rates, churn, tickets, incidents |
| Months 6–12 | 30–50 websites, roughly €2k–4k MRR; launch first infrastructure offering to existing customers |

## The trajectory

```
Freelancer → Managed service → Standardized managed service
→ Platform-enabled service → Monitoring platform
```

Revenue starts as time and gradually becomes automated: monitoring → reports → updates → onboarding
→ billing → alerts → scanner. Eventually one engineer supports hundreds of simple sites while
high-value infrastructure customers get human attention.
