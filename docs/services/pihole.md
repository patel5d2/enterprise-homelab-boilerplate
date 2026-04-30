# Pi-hole

**Category:** Networking & DNS | **Maturity:** 🟢 Stable | **Image:** `pihole/pihole:latest`

## What it does

Network-wide ad blocking and local DNS server

## How to enable

```bash
labctl init --service pihole
```

Or during full setup:

```bash
labctl init
# Answer Y when prompted for Pi-hole
```

## Configuration variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `subdomain` | string | `pihole` | ✓ | Subdomain for Pi-hole web interface |
| `web_password` | password | `` | ✓ | Password for Pi-hole admin web interface *(auto-generated)* |
| `server_ip` | string | `` | ✓ | IP address of the server running Pi-hole |
| `primary_dns` | choice | `cloudflare` |  | Primary upstream DNS server |
| `secondary_dns` | choice | `cloudflare_secondary` |  | Secondary upstream DNS server |
| `enable_dhcp` | boolean | `False` |  | Enable built-in DHCP server (disable your router's DHCP first) |
| `dhcp_start` | string | `192.168.1.100` |  | Starting IP address for DHCP range |
| `dhcp_end` | string | `192.168.1.200` |  | Ending IP address for DHCP range |
| `dhcp_router` | string | `192.168.1.1` |  | Router IP address for DHCP clients |
| `default_blocklists` | multiselect | `['stevenblack', 'malware_domain_list']` |  | Select default blocklists to enable |
| `custom_blocklists` | textarea | `` |  | Additional blocklist URLs (one per line) |
| `whitelist_domains` | textarea | `` |  | Always allowed domains (one per line) |
| `local_dns_records` | textarea | `` |  | Local DNS entries in format 'IP domain' (one per line) |
| `log_queries` | boolean | `True` |  | Enable logging of DNS queries (impacts performance) |
| `privacy_level` | choice | `anonymous` |  | Level of privacy for query logging |

## Profile defaults

**Development:**
```yaml
  log_queries: False
  privacy_level: anonymous
  enable_dhcp: False
  default_blocklists: ['stevenblack']
```

**Production:**
```yaml
  log_queries: True
  privacy_level: hide_domains
  enable_dhcp: False
  default_blocklists: ['stevenblack', 'malware_domain_list', 'disconnect']
```

## Common customizations

- Change the **port**: `labctl init --service pihole` and update the port field
- All **passwords/tokens** are auto-generated — re-generate by removing from `.env` and re-running init
- Disable: `labctl init --service pihole` and answer `N` to "Enable Pi-hole?"

## Related services
_No dependencies._
