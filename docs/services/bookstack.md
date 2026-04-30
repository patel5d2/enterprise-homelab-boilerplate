# BookStack

**Category:** Productivity | **Maturity:** 🟢 Stable | **Image:** `lscr.io/linuxserver/bookstack:latest`

> ⚠️ **Requires:** postgresql

## What it does

Self-hosted documentation and wiki platform with rich editing features

## How to enable

```bash
labctl init --service bookstack
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for BookStack
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `web_subdomain` | string | `docs` |  | Subdomain for documentation site |
| `database_password` | password | `` | ✓ | Database password *(auto-generated)* |
| `features_enable_registration` | boolean | `False` |  | Allow user self-registration |
| `features_default_theme` | string | `default` |  | Default theme |
| `features_enable_ldap` | boolean | `False` |  | Enable LDAP authentication |
| `email_mail_driver` | string | `smtp` |  | Email driver |
| `email_mail_host` | string | `` |  | SMTP host |
| `email_mail_port` | integer | `587` |  | SMTP port |
| `email_mail_username` | string | `` |  | SMTP username |
| `email_mail_password` | password | `` |  | SMTP password *(auto-generated)* |

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

- Change the **port**: `labctl init --service bookstack` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service bookstack` and answer `N` to "Enable BookStack?"

## Related services
- 
postgresql
