# Service Schema DSL Specification

This document defines the YAML schema format for service definitions in the Home Lab configuration system v2.

## Schema Structure

Each service is defined in a YAML file with the following top-level structure:

```yaml
# Service metadata
id: string                    # Unique service identifier
name: string                  # Human-readable service name  
category: string              # Service category for UI grouping
description: string           # Brief description
maturity: string              # stable, beta, alpha
required_capabilities: []     # System capabilities needed
dependencies: []              # Service dependencies (service IDs)

# Interactive form fields
fields:
  - key: string               # Field identifier
    label: string             # UI label
    type: string              # Field type (see Field Types)
    description: string       # Help text
    default: any              # Default value
    required: boolean         # Required field
    # ... type-specific attributes

# Docker Compose generation
compose:
  image: string               # Docker image
  container_name: string      # Container name template
  restart: string             # Restart policy
  environment:               # Environment variables
    - key: string
      from_field: string      # From user input field
      # or from_service: string  # From other service
      # or value: string         # Literal value
      # or generate: string      # Generated value type
  ports:                     # Port mappings
    - "host:container"
  volumes:                   # Volume mounts  
    - "name:/path"
  networks:                  # Networks to join
    - network_name
  labels:                    # Docker labels (Traefik routing)
    - "key=value"
  depends_on:               # Service dependencies
    service_name:
      condition: service_healthy
  healthcheck:              # Health check
    test: ["CMD", "command"]
    interval: 30s
    timeout: 5s
    retries: 3

# Profile-specific defaults
defaults:
  dev:
    field_name: value
  prod:
    field_name: value
```

## Field Types

### String
```yaml
- key: admin_user
  label: Admin username
  type: string
  description: Administrator username
  default: admin
  required: true
  placeholder: Enter username
  validate_regex: "^[a-zA-Z0-9_]+$"
  min_length: 3
  max_length: 32
```

### Password
```yaml
- key: admin_password
  label: Admin password
  type: password
  description: Administrator password
  required: true
  generate: true          # Auto-generate if not provided
  length: 32              # Generated password length
  mask: true              # Mask input display
```

### Boolean
```yaml
- key: enable_feature
  label: Enable advanced features
  type: boolean
  description: Enable additional functionality
  default: false
```

### Integer
```yaml
- key: http_port
  label: HTTP port
  type: integer
  description: Port for HTTP traffic
  default: 8080
  min: 1024
  max: 65535
```

### Choice (Single Select)
```yaml
- key: log_level
  label: Log level
  type: choice
  description: Application log level
  default: info
  choices:
    - debug
    - info
    - warn
    - error
```

### Multiselect
```yaml
- key: enabled_modules
  label: Enabled modules
  type: multiselect
  description: Select modules to enable
  default: [api, web]
  choices:
    - api
    - web
    - admin
    - metrics
  min_selections: 1
  max_selections: 3
```

### Textarea
```yaml
- key: custom_config
  label: Custom configuration
  type: textarea
  description: Additional configuration
  placeholder: "key: value\nother: setting"
```

## Conditional Fields

Fields can be shown/hidden based on other field values:

```yaml
- key: ssl_cert_path
  label: SSL certificate path
  type: string
  description: Path to SSL certificate
  show_if: "ssl_enabled == true"

- key: database_host
  label: Database host
  type: string
  description: External database host
  hidden_if: "use_internal_db == true"
  depends_on: [use_internal_db]
```

## Environment Variable Sources

### From User Field
```yaml
environment:
  - key: ADMIN_USER
    from_field: admin_user
```

### From Other Service
```yaml
environment:
  - key: POSTGRES_HOST
    from_service: postgresql.host
  - key: REDIS_URL
    from_service: redis.connection_url
```

### Generated Value
```yaml
environment:
  - key: SECRET_KEY
    generate: password
    length: 64
  - key: AUTH_HASH
    generate: htpasswd
    from_field: admin_password
```

### Literal Value
```yaml
environment:
  - key: NODE_ENV
    value: production
```

## Volume Types

### Named Volume
```yaml
volumes:
  - "service_data:/var/lib/service"
```

### Bind Mount with Variable
```yaml
volumes:
  - "${DATA_DIR}/service:/var/lib/service"
```

## Traefik Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.${SERVICE_ID}.rule=Host(`${SERVICE_ID}.${DOMAIN}`)"
  - "traefik.http.routers.${SERVICE_ID}.tls.certresolver=letsencrypt"
  - "traefik.http.services.${SERVICE_ID}.loadbalancer.server.port=${from_field:http_port}"
```

## Profile Defaults

Services can have different defaults for development vs production:

```yaml
defaults:
  dev:
    http_port: 8080
    log_level: debug
    acme_staging: true
  prod:
    http_port: 80
    log_level: info
    acme_staging: false
```

## Dependencies

Services can depend on other services:

```yaml
dependencies:
  - postgresql    # Service ID dependency
  - redis
```

The system will:
1. Auto-include dependencies when a service is selected
2. Order services by dependencies in compose generation
3. Set appropriate `depends_on` conditions

## Service Categories

Standard categories for UI grouping:

- `Core Infrastructure` - Essential services (Traefik, databases)
- `Networking & DNS` - Network services (Pi-hole, Headscale)
- `Security & Secrets` - Security tools (Vault, Vaultwarden)
- `Storage & Collaboration` - File and collaboration tools (Nextcloud)
- `Development & CI/CD` - Development tools (GitLab, Jenkins)
- `Automation & Documentation` - Workflow and docs (n8n, Fumadocs)
- `Monitoring & Observability` - Monitoring tools (Prometheus, Grafana)

## Validation Rules

1. `id` must be unique across all services
2. `dependencies` must reference valid service IDs
3. Field `key` values must be unique within a service
4. `from_service` references must be valid
5. `show_if`/`hidden_if` expressions must reference valid fields
6. Port ranges must be valid (1-65535)
7. Volume paths must be absolute or use valid variables