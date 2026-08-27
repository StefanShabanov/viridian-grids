# Internal control plane — NOT YET

Deliberately empty. This app gets built at **Gate 3 (~20–30 customers)**, not before.

Until then, customers are onboarded and configured by hand. See
[../../docs/roadmap.md](../../docs/roadmap.md).

When it is time, it manages: tenants, domains, subscriptions, scan history, monitoring
configuration, findings, reports, tickets, alert routing — as a control plane over Prometheus /
Grafana / Zabbix / Alertmanager / MainWP / Ansible. It does **not** replace any of them.
