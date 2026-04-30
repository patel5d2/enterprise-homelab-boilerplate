# Glance Dashboard

**Category:** Dashboard | **Maturity:** 🟢 Stable | **Image:** `glanceapp/glance:latest`

## What it does

Beautiful and minimal dashboard for your home lab services

## How to enable

```bash
labctl init --service glance
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Glance Dashboard
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `web_subdomain` | string | `dashboard` |  | Subdomain for dashboard |
| `theme_color_scheme` | string | `auto` |  | Dashboard color scheme |
| `widgets_enable_weather` | boolean | `True` |  | Enable weather widget |
| `widgets_weather_location` | string | `New York` |  | Location for weather widget |
| `widgets_enable_bookmarks` | boolean | `True` |  | Enable bookmarks widget |
| `widgets_enable_calendar` | boolean | `False` |  | Enable calendar widget |
| `widgets_enable_rss` | boolean | `False` |  | Enable RSS feed widget |

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

- Change the **port**: `labctl init --service glance` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service glance` and answer `N` to "Enable Glance Dashboard?"

## Related services
_No dependencies._
