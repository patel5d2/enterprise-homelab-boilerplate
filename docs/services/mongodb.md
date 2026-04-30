# MongoDB

**Category:** Core Infrastructure | **Maturity:** 🟢 Stable | **Image:** `mongo:7`

## What it does

High-performance document-oriented NoSQL database

## How to enable

```bash
labctl init --service mongodb
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for MongoDB
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `database_root_username` | string | `admin` |  | Root username for MongoDB |
| `database_root_password` | password | `` | ✓ | Root password for MongoDB *(auto-generated)* |
| `database_init_database` | string | `homelab` |  | Initial database name |
| `performance_cache_size` | string | `1GB` |  | WiredTiger cache size |
| `performance_max_connections` | integer | `1000` |  | Maximum number of connections |
| `backup_enabled` | boolean | `True` |  | Enable automated backups |
| `backup_schedule` | string | `0 3 * * *` |  | Backup schedule (cron format) |
| `backup_retention_days` | integer | `30` |  | Number of days to keep backups |

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

- Change the **port**: `labctl init --service mongodb` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service mongodb` and answer `N` to "Enable MongoDB?"

## Related services
_No dependencies._
