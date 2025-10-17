# Service Templates

This directory contains comprehensive service configuration templates for the Enterprise Home Lab platform. Each template defines a complete service with Docker configuration, customizable options, health checks, and dependencies.

## 📦 Available Service Templates

### 🏗️ Core Infrastructure
- **traefik.yaml** - Modern reverse proxy with automatic SSL certificates
- **postgresql.yaml** - Enterprise-grade relational database with automated backups
- **redis.yaml** - High-performance in-memory cache and message broker

### 📊 Monitoring & Observability
- **prometheus.yaml** - Time-series monitoring with node-exporter and cAdvisor
- **grafana.yaml** - Beautiful dashboards with pre-configured data sources
- **uptime-kuma.yaml** - Modern uptime monitoring with notifications

### 🌐 Networking & DNS
- **pihole.yaml** - Network-wide ad blocking and local DNS server with custom lists
- _(More networking services coming soon: Headscale, Cloudflared)_

### 🔒 Security & Secrets
- **vaultwarden.yaml** - Self-hosted Bitwarden-compatible password manager

### 📋 Dashboards
- **glance.yaml** - Beautiful minimal dashboard with weather, bookmarks, and monitoring

### 💻 Development & CI/CD
- **jenkins.yaml** - Full-featured CI/CD server with Docker integration
- **gitlab.yaml** - Complete DevOps platform (existing)

### 🗄️ Databases & Storage
- **mongodb.yaml** - Document database with Mongo Express web interface
- **nextcloud.yaml** - Self-hosted cloud storage and collaboration platform

### 🤖 Automation & Workflows
- **n8n.yaml** - Visual workflow automation with webhook support

### 📚 Documentation
- **bookstack.yaml** - Self-hosted wiki and documentation platform

### 🔄 Alternative Proxies
- **nginx-proxy-manager.yaml** - Web-based proxy management (conflicts with Traefik)

## 🏗️ Template Structure

Each service template follows a standardized structure:

```yaml
service_name: "service-name"
display_name: "Human Readable Name"
category: "category"
description: "Service description"
required: false|true
default_enabled: false|true
conflicts_with: ["other-service"] # Optional

docker:
  image: "docker/image:tag"
  container_name: "container-name"
  restart: "unless-stopped"
  ports: [...]
  volumes: [...]
  networks: [...]
  environment: [...]
  labels: [...] # Traefik labels

configuration:
  # Organized configuration options with types, defaults, and descriptions
  section:
    option:
      type: "string|password|boolean|choice|integer"
      default: "value"
      choices: [...] # For choice type
      required: true|false
      description: "Option description"

healthcheck:
  test: ["CMD", "command"]
  interval: "30s"
  timeout: "10s" 
  retries: 3

dependencies: ["service1", "service2"] # Optional

urls:
  web: "https://service.${DOMAIN}"

volumes:
  - name: "volume-name"
    description: "Volume description"

environment_variables:
  - name: "ENV_VAR"
    description: "Variable description"
    default: "value" # Optional
    generated: true|false # Optional
    type: "password|encryption_key" # Optional

additional_services: # Optional
  service_name:
    enabled_when: "condition"
    docker: {...}

config_files: # Optional
  filename.conf:
    path: "/path/to/file"
    content: |
      File content with ${VARIABLE} substitution

post_install_notes: | # Optional
  Instructions for post-installation setup
```

## 🎯 Key Features

### 🔧 Configuration Management
- **Typed Options**: All configuration options have defined types (string, password, boolean, choice, integer)
- **Validation**: Required fields, choice validation, and format checking
- **Defaults**: Sensible default values for quick setup
- **Environment Variables**: Automatic generation of secure passwords and keys

### 🐳 Docker Integration
- **Health Checks**: Comprehensive health monitoring for all services
- **Networks**: Automatic network configuration for service communication
- **Volumes**: Persistent storage management with clear descriptions
- **Labels**: Traefik integration for automatic SSL and routing

### 🔗 Service Dependencies
- **Dependency Management**: Automatic handling of service dependencies
- **Conflict Detection**: Prevention of conflicting services (e.g., multiple proxies)
- **Additional Services**: Support for helper containers (backups, cron jobs, etc.)

### 🎨 User Experience
- **Categories**: Organized service selection by purpose
- **Descriptions**: Clear explanations of what each service does
- **URLs**: Automatic generation of access URLs
- **Post-Install Notes**: Helpful setup instructions and default credentials

### 🛡️ Security
- **Password Generation**: Automatic generation of secure passwords
- **SSL Integration**: Built-in HTTPS support via Traefik
- **Authentication**: Configurable authentication options
- **Network Isolation**: Services run in isolated Docker networks

## 🚀 Usage

These templates are used by the CLI system (`./labctl init`) to:

1. **Present Options**: Display categorized services with descriptions
2. **Collect Configuration**: Interactive prompts based on template definitions
3. **Generate Infrastructure**: Create Docker Compose files and environment variables
4. **Validate Setup**: Ensure dependencies and conflicts are handled
5. **Provide Guidance**: Show URLs and post-installation instructions

## 📝 Adding New Services

To add a new service template:

1. Create a new YAML file following the structure above
2. Define all configuration options with proper types and validation
3. Include health checks and proper Docker configuration
4. Add to appropriate category
5. Test with the CLI system

## 🔄 Template Updates

When updating templates:
- Maintain backward compatibility
- Update version in comments if breaking changes
- Test with existing configurations
- Update documentation as needed

---

**Total Services**: 16 comprehensive templates covering all major home lab use cases!