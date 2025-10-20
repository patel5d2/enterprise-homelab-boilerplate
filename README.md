# 🏠 Enterprise Home Lab Boilerplate

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://docs.docker.com/get-docker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive, enterprise-grade home lab infrastructure management system with **interactive service selection**, automated Docker Compose generation, and full lifecycle management. Built for self-hosting enthusiasts who want enterprise-quality infrastructure at home.

## 📖 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [📦 Available Services](#-available-services)
- [🚀 Quick Start](#-quick-start)
- [📚 User Guide](#-user-guide)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration Workflow](#configuration-workflow)
  - [Service Deployment](#service-deployment)
  - [Service Management](#service-management)
- [🎮 CLI Reference](#-cli-reference)
- [🌐 Service Access Guide](#-service-access-guide)
- [🔧 Configuration Options](#-configuration-options)
- [🚨 Troubleshooting](#-troubleshooting)
- [🔒 Security & Maintenance](#-security--maintenance)
- [⚙️ Advanced Configuration](#️-advanced-configuration)
- [🤝 Contributing](#-contributing)

## ✨ Features

### Core Infrastructure Management
- **🎯 Interactive Service Selection** - Choose exactly what you want with guided wizards
- **🚀 One-Click Deployment** - Complete infrastructure setup in minutes
- **🔄 Full Lifecycle Management** - Init, build, deploy, monitor, and manage services
- **🎨 Beautiful CLI Interface** - Rich terminal UI with progress bars and panels
- **📊 Configuration Validation** - Schema validation and requirement checks

### Enterprise-Grade Services
- **🌐 Reverse Proxy & SSL** - Traefik with automatic Let's Encrypt certificates
- **📊 Monitoring Stack** - Prometheus, Grafana, and Uptime Kuma
- **🔒 Security First** - Vaultwarden, HashiCorp Vault, enterprise practices
- **🗄️ Database Support** - PostgreSQL, Redis, MongoDB with backup solutions
- **⚙️ CI/CD Pipeline** - GitLab CE, Jenkins integration
- **🏠 Home Automation** - Home Assistant, Node-RED compatibility
- **☁️ Cloud Integration** - Cloudflared tunnels, S3-compatible backups

### Developer Experience
- **📝 Configuration as Code** - YAML-based configuration with examples
- **🔐 Secure Defaults** - Automatic password generation and secrets management
- **📄 Documentation** - Built-in service documentation and help
- **🧩 Modular Design** - Enable only the services you need

## 🏗️ Architecture

```mermaid
graph TB
    User[👤 User] --> CLI[🎮 labctl CLI]
    CLI --> Config[📄 YAML Config]
    Config --> Generator[🏗️ Infrastructure Generator]
    Generator --> Compose[🐳 Docker Compose]
    
    subgraph "Infrastructure Layer"
        Traefik[🌐 Traefik Proxy]
        SSL[🔒 Let's Encrypt]
        Network[📡 Docker Networks]
    end
    
    subgraph "Core Services"
        DB[(🗄️ PostgreSQL)]
        Cache[(⚡ Redis)]
        Vault[🔐 Vaultwarden]
        Monitor[📊 Monitoring Stack]
    end
    
    subgraph "Application Services"
        GitLab[🦊 GitLab CE]
        Home[🏠 Home Assistant]
        Media[📺 Media Services]
        Docs[📚 Documentation]
    end
    
    Compose --> Traefik
    Traefik --> Core Services
    Traefik --> Application Services
    Core Services --> DB
    Core Services --> Cache
```

## 📦 Available Services

### Core Infrastructure
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **Traefik** | Reverse proxy with automatic SSL | 80, 443, 8080 | `traefik.yourdomain.com` |
| **PostgreSQL** | Primary database with pgBackRest | 5432 | N/A |
| **Redis** | Cache and session store | 6379 | N/A |

### Monitoring & Observability
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **Prometheus** | Metrics collection and storage | 9090 | `prometheus.yourdomain.com` |
| **Grafana** | Metrics visualization and dashboards | 3000 | `grafana.yourdomain.com` |
| **Uptime Kuma** | Uptime monitoring with notifications | 3001 | `uptime.yourdomain.com` |
| **Glance** | Beautiful home lab dashboard | 61208 | `dashboard.yourdomain.com` |

### Security & Secrets Management
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **Vaultwarden** | Self-hosted Bitwarden password manager | 80 | `vault.yourdomain.com` |
| **HashiCorp Vault** | Enterprise secrets management | 8200 | `vault-enterprise.yourdomain.com` |

### Networking & DNS
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **Pi-hole** | DNS ad-blocking and local DNS | 53, 80 | `pihole.yourdomain.com` |
| **Cloudflared** | Zero Trust tunnel (no port forwarding) | N/A | N/A |
| **Headscale** | Self-hosted Tailscale coordination | 8080 | `headscale.yourdomain.com` |

### Development & CI/CD
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **GitLab CE** | Git, CI/CD, container registry | 80, 22, 5050 | `gitlab.yourdomain.com` |
| **Jenkins** | Classic CI/CD automation | 8080 | `jenkins.yourdomain.com` |

### Storage & Databases
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **MongoDB** | Document database | 27017 | N/A |
| **MinIO** | S3-compatible object storage | 9000, 9001 | `minio.yourdomain.com` |
| **Nextcloud** | File sync and collaboration | 80 | `nextcloud.yourdomain.com` |

### Automation & Workflows
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **n8n** | Visual workflow automation | 5678 | `n8n.yourdomain.com` |
| **Home Assistant** | Home automation platform | 8123 | `homeassistant.yourdomain.com` |
| **Node-RED** | Visual flow-based programming | 1880 | `nodered.yourdomain.com` |

### Documentation & Knowledge
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **BookStack** | Wiki and documentation platform | 80 | `docs.yourdomain.com` |
| **Outline** | Team knowledge base | 3000 | `outline.yourdomain.com` |
| **DokuWiki** | Simple wiki platform | 80 | `wiki.yourdomain.com` |

### Media & Entertainment
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **Jellyfin** | Media streaming server | 8096 | `jellyfin.yourdomain.com` |
| **PhotoPrism** | Photo management and sharing | 2342 | `photos.yourdomain.com` |

### Alternative Reverse Proxies
| Service | Description | Default Port | Web UI |
|---------|-------------|--------------|--------|
| **Nginx Proxy Manager** | Web-based proxy management | 80, 443, 81 | `proxy.yourdomain.com` |
| **Caddy** | Modern web server with auto-HTTPS | 80, 443, 2019 | `caddy.yourdomain.com` |

## 🚀 Quick Start

### 1. Prerequisites Check
```bash
# Verify Docker and Docker Compose
docker --version
docker compose version

# Verify Python 3.11+
python3 --version

# Verify Git
git --version
```

### 2. Clone and Install
```bash
# Clone the repository
git clone https://github.com/patel5d2/enterprise-homelab-boilerplate.git
cd enterprise-homelab-boilerplate

# Run installation script
chmod +x install.sh labctl
./install.sh
```

### 3. Interactive Setup
```bash

python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install CLI package
pip install -e .

# Initialize configuration
./labctl init

# Build infrastructure
./labctl build

# Deploy services
./labctl deploy
```

### 4. Access Your Services
After deployment (2-3 minutes), access services at:
- **Traefik Dashboard**: `https://traefik.yourdomain.com`
- **Grafana**: `https://grafana.yourdomain.com`
- **Vaultwarden**: `https://vault.yourdomain.com`

## 📚 User Guide

### Prerequisites

#### System Requirements
| Requirement | Minimum | Recommended | Notes |
|-------------|---------|-------------|-------|
| **CPU** | 2 cores | 4+ cores | Multi-core for container orchestration |
| **RAM** | 4GB | 8GB+ | Memory per service varies (see service guide) |
| **Storage** | 50GB | 100GB+ | For persistent data and images |
| **OS** | macOS 10.15+, Linux, Windows 11 | Latest stable | Docker Desktop compatible |

#### Required Software
- **Docker Desktop** 4.0+ or Docker Engine 20.10+
- **Docker Compose** 2.0+ (included with Docker Desktop)
- **Python** 3.11+ with pip
- **Git** 2.30+ for version control

#### Optional but Recommended
- Domain name with DNS control (for Let's Encrypt SSL)
- CloudFlare account (for DNS automation)
- SMTP server details (for notifications)

#### Network Requirements
- Ports 80 and 443 available for reverse proxy
- Internet access for image pulls and SSL certificates
- Static IP or DDNS for external access (optional)

### Installation

#### 1. Environment Setup
```bash
# Create project directory
mkdir -p ~/homelab
cd ~/homelab

# Clone repository
git clone https://github.com/patel5d2/enterprise-homelab-boilerplate.git
cd enterprise-homelab-boilerplate

# Verify system requirements
./scripts/bootstrap/check_prereqs.sh  # If available
```

#### 2. Install Dependencies
```bash
# Make scripts executable
chmod +x install.sh labctl

# Run installation (creates virtual environment and installs Python deps)
./install.sh

# Verify installation
./labctl --version
```

#### 3. Create Configuration Structure
```bash
# Initialize project structure
mkdir -p {data,logs,ssl,backups,config}

# Copy example configuration
cp examples/config.yaml config/config.yaml
cp .env.template .env
```

### Configuration Workflow

#### 1. Basic Configuration
Edit `config/config.yaml`:

```yaml
core:
  domain: "homelab.local"        # Your domain name
  email: "admin@homelab.local"   # Admin email for SSL certs
  timezone: "America/New_York"   # Your timezone

reverse_proxy:
  provider: "traefik"            # Default reverse proxy
  ssl_provider: "letsencrypt"    # SSL certificate provider
  staging: false                # Use production Let's Encrypt

# Enable core services
databases:
  postgresql: true
  redis: true

monitoring:
  enabled: true
  retention: "30d"

security:
  enabled: true

passwords:
  vaultwarden: true

dashboards:
  glance: true
  uptime_kuma: true
```

#### 2. Domain and SSL Setup

**For Local Development (`.local` domain):**
```yaml
core:
  domain: "homelab.local"
reverse_proxy:
  ssl_provider: "self-signed"    # Use self-signed certificates
```

**For Production (real domain):**
```yaml
core:
  domain: "yourdomain.com"
  email: "your-email@domain.com"
reverse_proxy:
  ssl_provider: "letsencrypt"
  staging: false                 # Use production certificates
```

#### 3. Service Selection
Choose services based on your needs:

```yaml
# Development workflow
ci_cd:
  gitlab: true
  jenkins: false

# Home automation
automation:
  n8n: true
  home_assistant: true

# Media services (comment out if not needed)
# media:
#   jellyfin: true
#   photoprism: false
```

#### 4. Environment Variables
Edit `.env` file for sensitive configuration:
```bash
# Core domain settings
DOMAIN=homelab.local
ADMIN_EMAIL=admin@homelab.local
TZ=America/New_York

# SSL Configuration
LETSENCRYPT_STAGING=false
CLOUDFLARE_API_TOKEN=your_token_here

# Database passwords (generated automatically)
POSTGRES_PASSWORD=generated_secure_password
REDIS_PASSWORD=generated_secure_password

# Service-specific settings
GRAFANA_ADMIN_PASSWORD=generated_secure_password
VAULTWARDEN_ADMIN_TOKEN=generated_secure_token
```

### Service Deployment

#### 1. Validate Configuration
```bash
# Check configuration syntax and requirements
./labctl validate

# Preview what will be deployed
./labctl validate --strict
```

#### 2. Build Infrastructure
```bash
# Generate Docker Compose files
./labctl build

# Check generated files
ls -la docker-compose.yml .env prometheus.yml

# Preview services without deploying
docker compose config
```

#### 3. Deploy Services
```bash
# Deploy all enabled services
./labctl deploy

# Deploy specific services only
./labctl deploy --services traefik,grafana,prometheus

# Deploy to specific directory
./labctl deploy --compose-dir ./compose
```

#### 4. Verify Deployment
```bash
# Check service status
./labctl status

# View service logs
./labctl logs

# Follow logs for specific service
./labctl logs -f traefik

# Check container health
docker compose ps
```

### Service Management

#### Daily Operations
```bash
# Check overall system status
./labctl status

# Start all services
./labctl deploy
# or
docker compose up -d

# Stop all services
./labctl stop

# Stop and remove volumes (destructive!)
./labctl stop --volumes

# Restart specific service
docker compose restart grafana

# Update service images
docker compose pull
docker compose up -d
```

#### Configuration Updates
```bash
# Modify config/config.yaml
vim config/config.yaml

# Regenerate infrastructure
./labctl build

# Apply changes
./labctl deploy
```

#### Log Management
```bash
# View logs for all services
docker compose logs

# Follow logs with timestamps
docker compose logs -f -t

# Logs for specific service
docker compose logs grafana

# Filter logs by time
docker compose logs --since="2h" grafana
```

## 🎮 CLI Reference

### Core Commands

| Command | Description | Options | Example |
|---------|-------------|---------|----------|
| `init` | Interactive setup wizard | `--force`, `--no-interactive` | `./labctl init` |
| `validate` | Validate configuration | `--strict` | `./labctl validate --strict` |
| `build` | Generate compose files | `--services`, `--output`, `--force` | `./labctl build --services traefik,grafana` |
| `deploy` | Deploy services | `--services`, `--compose-dir` | `./labctl deploy` |
| `status` | Check service status | `--format json` | `./labctl status` |
| `logs` | View service logs | `-f`, `--tail` | `./labctl logs -f traefik` |
| `stop` | Stop services | `--volumes` | `./labctl stop` |
| `config` | Manage configuration | `--show`, `--validate` | `./labctl config --show` |

### Global Options
- `--config`, `-c`: Path to configuration file
- `--verbose`, `-v`: Enable verbose output  
- `--debug`: Enable debug output
- `--version`: Show version information

### Advanced Usage
```bash
# Initialize with custom config location
./labctl init --config custom-config.yaml

# Build only specific services
./labctl build --services "traefik,postgresql,grafana"

# Deploy with custom compose directory
./labctl deploy --compose-dir ./production

# Validate configuration strictly
./labctl validate --strict

# Show current configuration
./labctl config --show

# Enable debug logging
./labctl --debug status
```

## 🌐 Service Access Guide

### Web Interface Access

After deployment, services are accessible via your configured domain:

| Service | URL Pattern | Default Credentials |
|---------|-------------|-------------------|
| Traefik Dashboard | `https://traefik.{domain}` | No auth (configure in production) |
| Grafana | `https://grafana.{domain}` | `admin` / `${GRAFANA_ADMIN_PASSWORD}` |
| Vaultwarden | `https://vault.{domain}` | Create account on first visit |
| Pi-hole | `https://pihole.{domain}/admin` | Password: `${PIHOLE_PASSWORD}` |
| Uptime Kuma | `https://uptime.{domain}` | Create admin on first visit |
| GitLab | `https://gitlab.{domain}` | `root` / `${GITLAB_ROOT_PASSWORD}` |
| Nextcloud | `https://nextcloud.{domain}` | `admin` / `${NEXTCLOUD_ADMIN_PASSWORD}` |

### Initial Setup Steps

#### 1. Grafana Setup
```bash
# Find admin password
grep GRAFANA_ADMIN_PASSWORD .env

# Access Grafana at https://grafana.yourdomain.com
# Login: admin / password_from_env_file
# Import dashboards from config/grafana/
```

#### 2. Vaultwarden Setup  
```bash
# Find admin token
grep VAULTWARDEN_ADMIN_TOKEN .env

# Access admin panel at https://vault.yourdomain.com/admin
# Use token from env file
# Create your first user account
```

#### 3. Pi-hole Setup
```bash
# Find web password
grep PIHOLE_PASSWORD .env

# Configure DNS settings in your router:
# Primary DNS: <your-server-ip>
# Secondary DNS: 1.1.1.1
```

### Local Development Access

For `.local` domains, add entries to your `/etc/hosts` file:
```bash
# Add to /etc/hosts (requires sudo)
127.0.0.1 traefik.homelab.local
127.0.0.1 grafana.homelab.local
127.0.0.1 vault.homelab.local
127.0.0.1 pihole.homelab.local
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Port Conflicts
**Problem**: `Port 80/443 already in use`
```bash
# Check what's using the ports
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting services (macOS)
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.apache.httpd.plist

# Or change ports in docker-compose.yml
ports:
  - "8080:80"
  - "8443:443"
```

#### DNS Resolution Issues
**Problem**: Services unreachable via domain name
```bash
# Test DNS resolution
nslookup traefik.homelab.local

# Add to /etc/hosts if using .local domain
echo "127.0.0.1 traefik.homelab.local" | sudo tee -a /etc/hosts

# Flush DNS cache (macOS)
sudo dscacheutil -flushcache
```

#### SSL Certificate Issues
**Problem**: SSL certificate generation fails
```bash
# Check Traefik logs
docker compose logs traefik

# Common fixes:
# 1. Verify domain DNS points to your server
# 2. Check firewall allows ports 80/443
# 3. Verify email address in config
# 4. Use staging environment first

# Switch to staging for testing
reverse_proxy:
  ssl_provider: "letsencrypt"
  staging: true
```

#### Container Startup Failures
**Problem**: Services fail to start
```bash
# Check service status
docker compose ps

# View detailed logs
docker compose logs [service-name]

# Common issues:
# - Volume permission issues
# - Environment variable errors
# - Port conflicts
# - Insufficient resources

# Fix volume permissions
sudo chown -R 1000:1000 ./data
```

```

## 🔒 Security & Maintenance

### Security Best Practices

#### 1. Secrets Management
```bash
# Use strong, unique passwords
# Passwords are auto-generated in .env file
grep -E "_PASSWORD|_TOKEN" .env

# Rotate secrets periodically
./labctl build --regenerate-secrets

# Never commit .env to version control
echo ".env" >> .gitignore
```

#### 2. Access Control
```yaml
# Disable unnecessary admin interfaces
traefik:
  dashboard: false              # Disable in production

vaultwarden:
  signups_allowed: false        # Close registration after setup
  admin_enabled: false          # Disable admin panel after config

# Configure authentication for sensitive services
grafana:
  auth:
    anonymous: false
    oauth: true                 # Configure OAuth if available
```

#### 3. Network Security
```yaml
# Use internal networks for database connections
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true              # No internet access

# Restrict exposed ports
ports:
  - "127.0.0.1:5432:5432"      # Bind to localhost only
```

### Maintenance Tasks

#### Daily Checks
```bash
# Service health
./labctl status

# Resource usage
docker stats --no-stream

# Log review for errors
docker compose logs --since="24h" | grep -i error
```

#### Weekly Tasks
```bash
# Update container images
docker compose pull
docker compose up -d

# Clean unused resources
docker system prune -f

# Backup verification
ls -la backups/
```

#### Monthly Tasks
```bash
# Security updates
./labctl validate --strict

# Certificate renewal (automatic with Let's Encrypt)
docker compose logs traefik | grep -i certificate

# Capacity planning
docker system df
df -h ./data
```

### Backup Strategy

#### 1. Configuration Backup
```bash
# Backup configuration files
tar -czf config-backup-$(date +%Y%m%d).tar.gz \
  config/ .env docker-compose.yml

# Store in safe location
cp config-backup-*.tar.gz /path/to/backup/location/
```

#### 2. Database Backup
```bash
# PostgreSQL backup (automatic with pgBackRest)
docker compose exec postgres pg_dumpall > backup-postgres.sql

# Redis backup
docker compose exec redis redis-cli --rdb /data/dump.rdb
```

#### 3. Volume Backup
```bash
# Stop services before backup
docker compose stop

# Backup data volumes
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/

# Restart services
docker compose start
```

## ⚙️ Advanced Configuration

### GPU Acceleration

For services requiring GPU support (Jellyfin, PhotoPrism):

```yaml
# Add to docker-compose.yml for GPU services
services:
  jellyfin:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### External Database Configuration

Connect to external databases:

```yaml
# Use external PostgreSQL
databases:
  postgresql:
    enabled: false              # Disable internal database
    external:
      host: "postgres.example.com"
      port: 5432
      database: "homelab"
      user: "${POSTGRES_USER}"
      password: "${POSTGRES_PASSWORD}"
```

### Custom Certificates

Use custom SSL certificates:

```yaml
reverse_proxy:
  ssl_provider: "custom"
  custom_certs:
    cert_file: "/ssl/custom.crt"
    key_file: "/ssl/custom.key"
    ca_file: "/ssl/ca.crt"
```

### Multi-Node Setup

For distributed deployments:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  traefik:
    deploy:
      placement:
        constraints:
          - node.role == manager
  
  postgres:
    deploy:
      placement:
        constraints:
          - node.labels.database == true
```

### Environment Profiles

Create environment-specific overrides:

```bash
# Development
cp config/config.yaml config/config.dev.yaml
# Modify for development settings

# Production  
cp config/config.yaml config/config.prod.yaml
# Modify for production settings

# Deploy with specific profile
./labctl build --config config/config.prod.yaml
```

### GitOps Integration

Integrate with CI/CD for automated deployments:

```yaml
# .github/workflows/deploy.yml
name: Deploy Home Lab
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v3
      - name: Deploy infrastructure
        run: |
          ./labctl validate --strict
          ./labctl build
          ./labctl deploy
```

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Development Setup

```bash
# Clone repository
git clone https://github.com/patel5d2/enterprise-homelab-boilerplate.git
cd enterprise-homelab-boilerplate

# Create development branch
git checkout -b feature/your-feature-name

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Lint code
black src/
isort src/
flake8 src/
```

### Adding New Services

1. **Create service configuration** in `config/services/yourservice.yaml`
2. **Add generator method** in `generate-infrastructure.py`
3. **Update documentation** in README.md
4. **Add tests** for the new service
5. **Submit pull request** with clear description

### Service Template

```yaml
# config/services/example.yaml
name: "example"
description: "Example service description"
image: "example/service:latest"
ports:
  - "8080:80"
environment:
  - "ENV_VAR=value"
volumes:
  - "example-data:/data"
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.example.rule=Host(`example.${DOMAIN}`)"
dependencies:
  - "postgres"
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/health"]
  interval: "30s"
  timeout: "10s"
  retries: 3
```

### Reporting Issues

When reporting issues, please include:

- **Environment details** (OS, Docker version, Python version)
- **Configuration files** (sanitized of secrets)
- **Error logs** from relevant services
- **Steps to reproduce** the issue
- **Expected vs actual behavior**

### Community Guidelines

- **Be respectful** and inclusive
- **Search existing issues** before creating new ones
- **Use clear, descriptive titles** for issues and PRs
- **Follow code style** guidelines
- **Write tests** for new features
- **Update documentation** for changes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Docker Community** - For containerization platform
- **Traefik Team** - For excellent reverse proxy
- **Self-hosting Community** - For inspiration and feedback
- **Contributors** - For making this project better

## 📈 Project Status

- ✅ **Stable**: Core infrastructure management
- ✅ **Stable**: Interactive CLI and service selection
- ✅ **Stable**: Docker Compose generation
- 🔄 **Active Development**: Advanced networking features
- 🔄 **Active Development**: Multi-node deployment
- 📋 **Planned**: Kubernetes support
- 📋 **Planned**: Web-based management interface

---

**Made with ❤️ for the self-hosting community**

*If you find this project useful, please consider giving it a ⭐ on GitHub!*
