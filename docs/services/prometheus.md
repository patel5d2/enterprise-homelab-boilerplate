# Prometheus

**Category:** Observability | **Maturity:** 🟢 Stable | **Image:** `prom/prometheus:latest`

## What it does

Time-series database and monitoring system for metrics collection

## How to enable

```bash
labctl init --service prometheus
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Prometheus
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `storage_retention_time` | string | `30d` |  | How long to retain metrics data |
| `storage_retention_size` | string | `10GB` |  | Maximum storage size for metrics |
| `scraping_global_interval` | string | `15s` |  | Global scrape interval |
| `scraping_timeout` | string | `10s` |  | Scrape timeout |
| `web_subdomain` | string | `prometheus` |  | Subdomain for web interface |
| `web_enable_auth` | boolean | `True` |  | Enable authentication for web interface |

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

- Change the **port**: `labctl init --service prometheus` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service prometheus` and answer `N` to "Enable Prometheus?"

## Related services
_No dependencies._
