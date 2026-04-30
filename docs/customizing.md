# Customizing Your Home Lab

How to add new services, override defaults, and understand the schema → compose pipeline.

---

## Adding a New Service

1. **Create a schema file** at `config/services-v2/<your-service>.yaml`:

```yaml
id: myapp
name: My App
category: Development & CI/CD
description: Short description shown in the wizard
maturity: beta        # stable | beta | alpha
dependencies: [postgresql]   # other service IDs required
required_capabilities: []

fields:
  - key: enabled
    label: Enable My App
    type: boolean
    default: false

  - key: port
    label: HTTP port
    type: integer
    default: 8888
    min: 1024
    max: 65535

  - key: admin_password
    label: Admin password
    type: password
    required: true
    generate: true    # auto-generate if user presses Enter
    length: 24

compose:
  image: myapp:latest
  container_name: myapp
  restart: unless-stopped
  ports:
    - "${port}:8888"
  environment:
    - key: ADMIN_PASSWORD
      from_field: admin_password
    - key: DATABASE_URL
      value: "postgresql://postgres@postgres/myapp"
  networks:
    - traefik
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.myapp.rule=Host(`myapp.${global:domain}`)"
    - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8888/health"]
    interval: 30s
    timeout: 5s
    retries: 3

defaults:
  dev:
    port: 8888
    enabled: false
  prod:
    port: 8888
    enabled: false
```

2. **Run the wizard** — your service will appear in the appropriate category:

```bash
labctl init
```

3. **Build and deploy**:

```bash
labctl build && labctl deploy
```

That's it. No Python code to write.

---

## Field Types Reference

| Type | Use case | Key attributes |
|---|---|---|
| `boolean` | Enable/disable | `default: true\|false` |
| `string` | Text input | `validate_regex`, `min_length`, `max_length` |
| `password` | Secrets | `generate: true`, `length`, `mask: true` |
| `integer` | Ports, counts | `min`, `max` |
| `choice` | Dropdown | `choices: [a, b, c]` |
| `multiselect` | Multi-dropdown | `choices`, `min_selections`, `max_selections` |
| `textarea` | Multi-line | `placeholder` |

---

## Conditional Fields

Show a field only when another field has a specific value:

```yaml
- key: smtp_password
  label: SMTP password
  type: password
  show_if: 'smtp_host != ""'    # only shown when smtp_host is set
```

Supported expressions:
- `field == "value"` / `field != "value"` (string)
- `field == true` / `field == false` (boolean)

---

## Overriding Profile Defaults

The `defaults:` block lets you set different values for `dev` vs `prod`:

```yaml
defaults:
  dev:
    retention_days: 7
    log_level: debug
    enabled: true
  prod:
    retention_days: 30
    log_level: info
    enabled: false
```

The wizard picks the right defaults based on the profile the user chose.

---

## Compose Template Variables

In the `compose:` block, reference field values with `${field_key}`:

```yaml
ports:
  - "${port}:8080"
environment:
  - key: DOMAIN
    template: "https://${subdomain}.${global:domain}"
  - key: DB_URL
    from_field: database_name        # reference a specific field value
labels:
  - "traefik.http.routers.myapp.rule=Host(`${subdomain}.${global:domain}`)"
```

Special prefixes:
- `${global:domain}` — the core domain configured during init
- `${global:email}` — the admin email
- `from_field: <key>` — value of another field in this service

---

## Reconfiguring One Service

```bash
labctl init --service myapp
```

Only that service's prompts run. All other services are untouched.

---

## Manual Config Edits

`config/config.yaml` is plain YAML — you can edit it directly:

```yaml
services:
  myapp:
    enabled: true
    port: 9000          # override a field
```

Then rebuild: `labctl build && labctl deploy`

---

## Adding a New Category

Categories come from the `category:` field in each schema. Just use a new string:

```yaml
category: Home Automation
```

It will appear as a new section in the `labctl init` wizard automatically.
