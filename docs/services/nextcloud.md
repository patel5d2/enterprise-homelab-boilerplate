# Nextcloud

**Category:** Storage & Collaboration | **Maturity:** 🟢 Stable | **Image:** `nextcloud:28`

> ⚠️ **Requires:** postgresql, redis

## What it does

Self-hosted cloud storage and collaboration platform

## How to enable

```bash
labctl init --service nextcloud
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Nextcloud
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `subdomain` | string | `cloud` | ✓ | Subdomain for Nextcloud (e.g. 'cloud' for cloud.example.com) |
| `http_port` | integer | `8081` |  | Internal container port for HTTP traffic |
| `admin_user` | string | `admin` | ✓ | Nextcloud administrator username |
| `admin_password` | password | `` | ✓ | Nextcloud administrator password *(auto-generated)* |
| `database_name` | string | `nextcloud` | ✓ | PostgreSQL database name for Nextcloud |
| `database_user` | string | `nextcloud` | ✓ | PostgreSQL user for Nextcloud database |
| `database_password` | password | `` | ✓ | PostgreSQL password for Nextcloud user *(auto-generated)* |
| `max_upload_size` | choice | `512M` |  | Maximum file upload size |
| `memory_limit` | choice | `512M` |  | PHP memory limit for Nextcloud |
| `enable_preview_generator` | boolean | `True` |  | Enable preview generation for files (requires more resources) |
| `enable_office_integration` | boolean | `False` |  | Enable Collabora Online for document editing |
| `enable_talk` | boolean | `False` |  | Enable Nextcloud Talk for video/audio calls |
| `turn_server` | string | `` |  | TURN server for Talk (required for NAT traversal) |
| `turn_secret` | password | `` |  | Shared secret for TURN server authentication *(auto-generated)* |
| `trusted_proxies` | textarea | `` |  | List of trusted proxy IP addresses (one per line) |
| `mail_server` | string | `` |  | SMTP server for sending emails (optional) |
| `mail_port` | integer | `587` |  | SMTP server port |
| `mail_username` | string | `` |  | SMTP username for authentication |
| `mail_password` | password | `` |  | SMTP password for authentication |

## Profile defaults

**Development:**
```yaml
  http_port: 8081
  max_upload_size: 256M
  memory_limit: 256M
  enable_preview_generator: False
  enable_office_integration: False
  enable_talk: False
```

**Production:**
```yaml
  http_port: 8081
  max_upload_size: 2G
  memory_limit: 1G
  enable_preview_generator: True
  enable_office_integration: True
  enable_talk: False
```

## Common customizations

- Change the **port**: `labctl init --service nextcloud` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service nextcloud` and answer `N` to "Enable Nextcloud?"

## Related services
- 
postgresql- redis
