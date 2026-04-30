# Redis

**Category:** Core Infrastructure | **Maturity:** 🟢 Stable | **Image:** `redis:7-alpine`

## What it does

In-memory data structure store used as database, cache, and message broker

## How to enable

```bash
labctl init --service redis
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Redis
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `port` | integer | `6379` |  | Port for Redis connections |
| `password` | password | `` |  | Authentication password for Redis (leave empty for no auth) *(auto-generated)* |
| `max_memory` | choice | `512mb` |  | Maximum memory Redis can use |
| `eviction_policy` | choice | `allkeys-lru` |  | Policy for evicting keys when memory limit is reached |
| `persistence_mode` | choice | `rdb` |  | Data persistence strategy |
| `rdb_save_frequency` | choice | `standard` |  | How often to save RDB snapshots |
| `aof_fsync` | choice | `everysec` |  | How often to sync AOF file to disk |
| `enable_clustering` | boolean | `False` |  | Enable Redis cluster mode (requires multiple nodes) |
| `cluster_nodes` | integer | `3` |  | Number of cluster nodes to deploy |
| `log_level` | choice | `notice` |  | Redis server log level |

## Profile defaults

**Development:**
```yaml
  port: 6379
  max_memory: 256mb
  persistence_mode: rdb
  rdb_save_frequency: standard
  log_level: debug
```

**Production:**
```yaml
  port: 6379
  max_memory: 1gb
  persistence_mode: both
  rdb_save_frequency: conservative
  aof_fsync: everysec
  log_level: notice
```

## Common customizations

- Change the **port**: `labctl init --service redis` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service redis` and answer `N` to "Enable Redis?"

## Related services
_No dependencies._
