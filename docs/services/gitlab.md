# Gitlab

**Category:** DevOps | **Maturity:** 🟢 Stable | **Image:** `gitlab:latest`

> ⚠️ **Requires:** postgresql, redis

## What it does

gitlab service

## How to enable

```bash
labctl init --service gitlab
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Gitlab
```

## Configuration variables

_No configuration required._

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

- Change the **port**: `labctl init --service gitlab` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service gitlab` and answer `N` to "Enable Gitlab?"

## Related services
- 
postgresql- redis
