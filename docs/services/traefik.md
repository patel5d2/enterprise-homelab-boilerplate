# Traefik

**Category:** Core Infrastructure | **Maturity:** 🟢 Stable | **Image:** `traefik:v3.1`

## What it does

Modern reverse proxy with automatic SSL certificates and load balancing

## How to enable

```bash
labctl init --service traefik
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Traefik
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `domain` | string | `` | ✓ | Base domain for all services (e.g. example.com) |
| `email` | string | `` | ✓ | Email address for Let's Encrypt certificates |
| `cloudflare_auth_method` | choice | `api_token` |  | Choose authentication method for DNS challenge |
| `cloudflare_api_token` | password | `` | ✓ | Cloudflare API token with Zone:Read, DNS:Edit permissions |
| `cloudflare_global_key` | password | `` | ✓ | Cloudflare Global API Key (less secure than token) |
| `cloudflare_email` | string | `` | ✓ | Email associated with Cloudflare account |
| `acme_environment` | choice | `production` |  | Let's Encrypt environment to use |
| `enable_dashboard` | boolean | `True` |  | Enable Traefik web dashboard |
| `dashboard_subdomain` | string | `traefik` |  | Subdomain for Traefik dashboard |
| `dashboard_user` | string | `admin` |  | Username for dashboard basic auth |
| `dashboard_password` | password | `` | ✓ | Password for dashboard basic auth *(auto-generated)* |
| `enable_hsts` | boolean | `True` |  | Enable HTTP Strict Transport Security headers |
| `enable_ipv6` | boolean | `False` |  | Enable IPv6 support |

## Profile defaults

**Development:**
```yaml
  acme_environment: staging
  dashboard_subdomain: traefik-dev
  enable_hsts: False
```

**Production:**
```yaml
  acme_environment: production
  dashboard_subdomain: traefik
  enable_hsts: True
```

## Common customizations

- Change the **port**: `labctl init --service traefik` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service traefik` and answer `N` to "Enable Traefik?"

## Related services
_No dependencies._
