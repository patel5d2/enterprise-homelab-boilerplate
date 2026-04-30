# Monitoring Stack

**Category:** Monitoring & Observability | **Maturity:** 🟢 Stable | **Image:** `prom/prometheus:latest`

## What it does

Prometheus, Grafana, and AlertManager for comprehensive monitoring

## How to enable

```bash
labctl init --service monitoring
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Monitoring Stack
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `prometheus_port` | integer | `9090` |  | Internal port for Prometheus server |
| `grafana_port` | integer | `3000` |  | Internal port for Grafana web interface |
| `prometheus_subdomain` | string | `prometheus` | ✓ | Subdomain for Prometheus web interface |
| `grafana_subdomain` | string | `grafana` | ✓ | Subdomain for Grafana web interface |
| `retention_days` | integer | `30` |  | Number of days to keep metrics data |
| `scrape_interval` | choice | `15s` |  | How often to scrape metrics from targets |
| `grafana_admin_user` | string | `admin` | ✓ | Grafana administrator username |
| `grafana_admin_password` | password | `` | ✓ | Grafana administrator password *(auto-generated)* |
| `enable_alertmanager` | boolean | `True` |  | Enable AlertManager for alert routing and management |
| `alertmanager_port` | integer | `9093` |  | Internal port for AlertManager |
| `alertmanager_subdomain` | string | `alerts` |  | Subdomain for AlertManager web interface |
| `smtp_smarthost` | string | `` |  | SMTP server for sending email alerts (optional) |
| `smtp_from` | string | `` |  | From email address for alerts |
| `smtp_auth_username` | string | `` |  | SMTP username for authentication |
| `smtp_auth_password` | password | `` |  | SMTP password for authentication |
| `enable_node_exporter` | boolean | `True` |  | Enable Node Exporter for system metrics |
| `enable_cadvisor` | boolean | `True` |  | Enable cAdvisor for container metrics |
| `custom_dashboards` | multiselect | `['docker', 'system', 'traefik']` |  | Additional dashboards to install |

## Profile defaults

**Development:**
```yaml
  prometheus_port: 9090
  grafana_port: 3000
  retention_days: 7
  scrape_interval: 30s
  enable_alertmanager: False
  enable_node_exporter: True
  enable_cadvisor: False
  custom_dashboards: ['docker', 'system']
```

**Production:**
```yaml
  prometheus_port: 9090
  grafana_port: 3000
  retention_days: 30
  scrape_interval: 15s
  enable_alertmanager: True
  enable_node_exporter: True
  enable_cadvisor: True
  custom_dashboards: ['docker', 'system', 'traefik', 'postgresql', 'redis']
```

## Common customizations

- Change the **port**: `labctl init --service monitoring` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service monitoring` and answer `N` to "Enable Monitoring Stack?"

## Related services
_No dependencies._
