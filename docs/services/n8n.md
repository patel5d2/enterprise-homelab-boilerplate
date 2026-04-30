# n8n

**Category:** Automation | **Maturity:** 🟢 Stable | **Image:** `n8nio/n8n:latest`

> ⚠️ **Requires:** postgresql, redis

## What it does

Visual workflow automation platform for connecting apps and services

## How to enable

```bash
labctl init --service n8n
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for n8n
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `web_subdomain` | string | `n8n` |  | Subdomain for web interface |
| `basic_auth_enabled` | boolean | `True` |  | Enable basic authentication |
| `basic_auth_user` | string | `admin` |  | Basic auth username |
| `basic_auth_password` | password | `` | ✓ | Basic auth password *(auto-generated)* |
| `encryption_key` | password | `` | ✓ | Encryption key for sensitive data *(auto-generated)* |

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

- Change the **port**: `labctl init --service n8n` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service n8n` and answer `N` to "Enable n8n?"

## Related services
- 
postgresql- redis
