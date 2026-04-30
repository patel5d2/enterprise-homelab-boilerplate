# Uptime Kuma

**Category:** Monitoring | **Maturity:** 🟢 Stable | **Image:** `louislam/uptime-kuma:1`

## What it does

Beautiful and modern uptime monitoring with notifications

## How to enable

```bash
labctl init --service uptime_kuma
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Uptime Kuma
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `web_subdomain` | string | `uptime` |  | Subdomain for web interface |
| `monitoring_check_interval` | integer | `60` |  | Default check interval in seconds |
| `monitoring_retry_interval` | integer | `60` |  | Retry interval for failed checks |
| `monitoring_resend_interval` | integer | `0` |  | Resend interval for notifications (0 = disabled) |
| `notifications_enable_discord` | boolean | `False` |  | Enable Discord notifications |
| `notifications_discord_webhook` | string | `` |  | Discord webhook URL |
| `notifications_enable_slack` | boolean | `False` |  | Enable Slack notifications |
| `notifications_slack_webhook` | string | `` |  | Slack webhook URL |
| `notifications_enable_telegram` | boolean | `False` |  | Enable Telegram notifications |
| `notifications_telegram_bot_token` | string | `` |  | Telegram bot token |
| `notifications_telegram_chat_id` | string | `` |  | Telegram chat ID |
| `docker_enable_docker_monitoring` | boolean | `False` |  | Enable Docker container monitoring |

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

- Change the **port**: `labctl init --service uptime_kuma` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service uptime_kuma` and answer `N` to "Enable Uptime Kuma?"

## Related services
_No dependencies._
