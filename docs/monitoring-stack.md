# Monitoring stack

Runs on 1–3 well-managed VPSs. **No Kubernetes.** A significant business fits comfortably here.

```
Docker Compose
│
├── Uptime Kuma        external uptime checks
├── Prometheus         metrics collection
├── Blackbox Exporter  HTTP/TCP/SSL probing
├── Grafana            operational dashboards
├── Alertmanager       internal alert routing
├── Loki               logs, if/when needed
├── PostgreSQL         our own data
└── vg internal app    scanner + control plane (later)
```

Alongside, where appropriate:

| Tool | Purpose |
|---|---|
| MainWP | Central WordPress administration |
| Ansible | Repeatable updates and configuration |
| Restic | Backups where we are responsible for them |
| WireGuard | Private access to customer infrastructure |

## Division of labour

Grafana/Prometheus/Zabbix stay. Our app never becomes another Grafana — it is the **control plane**:

```
Our application
      ↓
customers · sites · plans · billing · configuration · reports · permissions
------------------------------------------------------------------------
Underlying infrastructure
------------------------------------------------------------------------
Prometheus · Grafana · Zabbix · Loki · Alertmanager · MainWP · Ansible
```

## Later additions, only when customers create the need

| Trigger | Add |
|---|---|
| Customers ask "can you monitor our VPS?" | Node exporter targets, Infrastructure Care plan |
| Traditional infra: SNMP, switches, routers, UPS, printers, NAS, IPMI, VMware | **Zabbix** |
| Facility monitoring demand | Mosquitto, Node-RED, Telegraf, ESPHome, VictoriaMetrics |

Eventual split: web → Blackbox/Prometheus · servers → Prometheus/Zabbix · network → Zabbix ·
logs → Loki · visualization → Grafana.

## Operational rules

- Customer credentials live in a password manager, **never in this repo**, never in plain-text
  Ansible inventories.
- Alert routing is internal-first. Customers get notified per their stated preference, not by
  raw Alertmanager output.
- Every alert that fires must be actionable; tune or delete anything that pages without a response.
- The monitoring host itself needs monitoring — an external uptime check on our own stack.

## Status

Docker is not installed on the dev machine. `infra/compose/docker-compose.yml` is a skeleton for the
VPS; provisioning the VPS is Week 1 work — see [30-day-plan.md](30-day-plan.md).
