# Jenkins

**Category:** DevOps | **Maturity:** 🟢 Stable | **Image:** `jenkins/jenkins:lts`

## What it does

Open source automation server for continuous integration and deployment

## How to enable

```bash
labctl init --service jenkins
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Jenkins
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `web_subdomain` | string | `jenkins` |  | Subdomain for web interface |
| `resources_memory_limit` | string | `2g` |  | Java heap memory limit |
| `resources_cpu_limit` | string | `2` |  | CPU limit |
| `security_admin_username` | string | `admin` |  | Initial admin username |
| `security_admin_password` | password | `` | ✓ | Initial admin password *(auto-generated)* |
| `features_enable_agents` | boolean | `True` |  | Enable Jenkins agents |
| `features_max_agents` | integer | `5` |  | Maximum number of agents |
| `features_enable_docker_plugin` | boolean | `True` |  | Enable Docker plugin for container builds |
| `backup_enabled` | boolean | `True` |  | Enable automated backups |
| `backup_schedule` | string | `H 2 * * 0` |  | Backup schedule (cron format) |

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

- Change the **port**: `labctl init --service jenkins` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service jenkins` and answer `N` to "Enable Jenkins?"

## Related services
_No dependencies._
