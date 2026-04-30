# Nginx Proxy Manager

**Category:** Networking | **Maturity:** 🟢 Stable | **Image:** `jc21/nginx-proxy-manager:latest`

## What it does

Web-based reverse proxy management with automatic SSL certificates

## How to enable

```bash
labctl init --service nginx_proxy_manager
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Nginx Proxy Manager
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `web_admin_port` | integer | `81` |  | Admin interface port |
| `web_subdomain` | string | `proxy` |  | Subdomain for admin interface |
| `ssl_default_email` | string | `` | ✓ | Default email for SSL certificates |
| `ssl_use_letsencrypt` | boolean | `True` |  | Enable Let's Encrypt integration |
| `ssl_staging` | boolean | `False` |  | Use Let's Encrypt staging environment |
| `security_initial_admin_email` | string | `admin@${DOMAIN}` |  | Initial admin email |
| `security_initial_admin_password` | password | `` | ✓ | Initial admin password *(auto-generated)* |
| `features_enable_access_lists` | boolean | `True` |  | Enable access control lists |
| `features_enable_custom_locations` | boolean | `True` |  | Enable custom location blocks |
| `features_enable_advanced_config` | boolean | `False` |  | Enable advanced nginx configuration |

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

- Change the **port**: `labctl init --service nginx_proxy_manager` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service nginx_proxy_manager` and answer `N` to "Enable Nginx Proxy Manager?"

## Related services
_No dependencies._
