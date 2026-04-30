# PostgreSQL

**Category:** Core Infrastructure | **Maturity:** 🟢 Stable | **Image:** `postgres:16`

## What it does

Enterprise-grade relational database with high performance and reliability

## How to enable

```bash
labctl init --service postgresql
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for PostgreSQL
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `port` | integer | `5432` |  | Port for PostgreSQL connections |
| `database_name` | string | `homelab` | ✓ | Name of the default database to create |
| `superuser_name` | string | `postgres` | ✓ | PostgreSQL superuser username |
| `superuser_password` | password | `` | ✓ | PostgreSQL superuser password *(auto-generated)* |
| `max_connections` | integer | `100` |  | Maximum number of concurrent database connections |
| `shared_buffers` | choice | `256MB` |  | Amount of memory for shared buffers |
| `work_mem` | choice | `4MB` |  | Memory per query operation |
| `enable_backups` | boolean | `True` |  | Enable automated database backups with pg_dump |
| `backup_schedule` | choice | `daily_2am` |  | Cron schedule for automated backups |
| `backup_retention_days` | integer | `30` |  | Number of days to keep backup files |
| `compress_backups` | boolean | `True` |  | Compress backup files with gzip |
| `create_additional_databases` | boolean | `True` |  | Create additional databases for services |
| `additional_databases` | textarea | `` |  | List of additional databases to create (one per line) |

## Profile defaults

**Development:**
```yaml
  port: 5432
  max_connections: 50
  shared_buffers: 128MB
  work_mem: 2MB
  backup_retention_days: 7
```

**Production:**
```yaml
  port: 5432
  max_connections: 200
  shared_buffers: 512MB
  work_mem: 8MB
  backup_retention_days: 30
```

## Common customizations

- Change the **port**: `labctl init --service postgresql` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service postgresql` and answer `N` to "Enable PostgreSQL?"

## Related services
_No dependencies._
