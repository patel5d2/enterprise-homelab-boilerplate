# Vaultwarden

**Category:** Security & Secrets | **Maturity:** 🟢 Stable | **Image:** `vaultwarden/server:latest`

> ⚠️ **Requires:** postgresql

## What it does

Self-hosted Bitwarden-compatible password manager

## How to enable

```bash
labctl init --service vaultwarden
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Vaultwarden
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `subdomain` | string | `vault` | ✓ | Subdomain for Vaultwarden web vault |
| `http_port` | integer | `8080` |  | Internal container port for HTTP traffic |
| `database_name` | string | `vaultwarden` | ✓ | PostgreSQL database name for Vaultwarden |
| `database_user` | string | `vaultwarden` | ✓ | PostgreSQL user for Vaultwarden database |
| `database_password` | password | `` | ✓ | PostgreSQL password for Vaultwarden user *(auto-generated)* |
| `admin_token` | password | `` |  | Token for accessing admin panel (leave empty to disable admin panel) *(auto-generated)* |
| `signups_allowed` | boolean | `True` |  | Allow users to register new accounts |
| `invitations_allowed` | boolean | `True` |  | Allow users to invite others (requires signups disabled) |
| `show_password_hint` | boolean | `False` |  | Allow users to see password hints on login page |
| `enable_websocket` | boolean | `True` |  | Enable real-time sync notifications |
| `websocket_port` | integer | `3012` |  | Port for WebSocket notifications |
| `smtp_host` | string | `` |  | SMTP server for email notifications (optional) |
| `smtp_port` | integer | `587` |  | SMTP server port |
| `smtp_ssl` | choice | `starttls` |  | SMTP encryption method |
| `smtp_username` | string | `` |  | SMTP username for authentication |
| `smtp_password` | password | `` |  | SMTP password for authentication |
| `smtp_from` | string | `` |  | Email address for outgoing emails |
| `enable_2fa` | boolean | `True` |  | Enable two-factor authentication support |
| `icon_service` | choice | `internal` |  | Service to use for website icons |
| `log_level` | choice | `info` |  | Application log level |

## Profile defaults

**Development:**
```yaml
  http_port: 8080
  signups_allowed: True
  invitations_allowed: True
  show_password_hint: True
  enable_websocket: False
  log_level: debug
```

**Production:**
```yaml
  http_port: 8080
  signups_allowed: False
  invitations_allowed: True
  show_password_hint: False
  enable_websocket: True
  log_level: info
```

## Common customizations

- Change the **port**: `labctl init --service vaultwarden` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service vaultwarden` and answer `N` to "Enable Vaultwarden?"

## Related services
- 
postgresql
