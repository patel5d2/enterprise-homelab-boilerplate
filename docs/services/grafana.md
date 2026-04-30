# Grafana

**Category:** Observability | **Maturity:** 🟢 Stable | **Image:** `grafana/grafana:latest`

> ⚠️ **Requires:** prometheus

## What it does

Beautiful dashboards and visualization for monitoring data

## How to enable

```bash
labctl init --service grafana
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Grafana
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `admin_username` | string | `admin` |  | Admin username |
| `admin_password` | password | `` | ✓ | Admin password *(auto-generated)* |
| `web_subdomain` | string | `grafana` |  | Subdomain for web interface |
| `security_allow_signup` | boolean | `False` |  | Allow user self-registration |
| `security_anonymous_access` | boolean | `False` |  | Enable anonymous access |
| `plugins_enabled` | multiselect | `['grafana-piechart-panel', 'grafana-clock-panel']` |  | Grafana plugins to install |
| `datasources_prometheus_url` | string | `http://prometheus:9090` |  | Prometheus datasource URL |

## Profile defaults

**Development:**
```yaml
  _(same as prod)_
```

**Production:**
```yaml
  _(no overrides)_
```

## Common customizations

- Change the **port**: `labctl init --service grafana` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service grafana` and answer `N` to "Enable Grafana?"

## Related services
- 
prometheus
