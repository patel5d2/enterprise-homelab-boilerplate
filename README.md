# 🏠 Enterprise Home Lab CLI

A comprehensive, enterprise-grade home lab infrastructure tool that orchestrates 15+ self-hosted services with automatic SSL, monitoring, and Docker Compose deployment.

## 🚀 Quick Links

- [Quick Start (5 minutes)](#-quick-start)
- [Installation](#-installation) 
- [CLI Commands](#-cli-commands)
- [Use Cases](#-use-cases)
- [Troubleshooting](#-troubleshooting)

## ✨ What This Tool Does

The Home Lab CLI (`labctl`) simplifies deploying and managing self-hosted services by:

- **Interactive Service Selection** - Choose exactly what you want to install
- **Automatic Configuration** - Generates Docker Compose files and environment variables
- **SSL Certificates** - Automatic HTTPS with Let's Encrypt via Traefik
- **Monitoring Stack** - Built-in Prometheus, Grafana, and health checks
- **Dependency Management** - Handles service dependencies automatically
- **Enterprise Security** - Network isolation, secrets management, secure defaults

**Architecture**: Python CLI → YAML config → Docker Compose + `.env` → Traefik reverse proxy with automatic SSL

## 🎯 Available Services

### Core Infrastructure
- **Traefik** - Reverse proxy with automatic SSL certificates
- **PostgreSQL** - Primary relational database
- **Redis** - In-memory cache and message broker

### Monitoring & Observability  
- **Prometheus** - Metrics collection and monitoring
- **Grafana** - Beautiful dashboards and visualization
- **Uptime Kuma** - Uptime monitoring with notifications

### Networking & DNS
- **Pi-hole** - Network-wide ad blocking and DNS server

### Security & Secrets
- **Vaultwarden** - Self-hosted Bitwarden-compatible password manager

### Development & Automation
- **GitLab** - Complete DevOps platform with CI/CD
- **Jenkins** - Classic CI/CD automation server
- **n8n** - Visual workflow automation platform

### Storage & Databases
- **MongoDB** - Document database with web interface
- **Nextcloud** - Self-hosted cloud storage and collaboration

### Documentation & Dashboards  
- **BookStack** - Self-hosted wiki and documentation
- **Glance** - Beautiful home lab dashboard

### Alternative Proxies
- **Nginx Proxy Manager** - Web-based proxy management

## 📋 Prerequisites

### System Requirements
- **OS**: macOS or Linux (x86_64/ARM64)
- **CPU**: 2+ cores recommended
- **RAM**: 4-8 GB minimum (depends on selected services)
- **Storage**: 20-100 GB available space
- **Docker**: Docker Desktop or Docker Engine with Compose v2

### Network Requirements  
- **Domain**: A domain name you control (e.g., `homelab.example.com`)
- **DNS**: A/AAAA records pointing to your server's public IP
- **Ports**: 80 and 443 must be open and forwarded to your server
- **No Conflicts**: No other services using ports 80/443 (nginx, apache, etc.)

### Software Prerequisites
```bash
# Check requirements
docker --version          # Docker 20.10+ required
docker compose version    # Compose v2 required
python3 --version         # Python 3.8+ required
```

## 🏗️ Installation

### Option 1: Quick Install (Recommended)
```bash
# Download and install CLI
./install.sh

# Verify installation
./labctl --help
```

### Option 2: Using Makefile
```bash
# Full quickstart (install + configure + deploy)
make quickstart

# Or step by step
make install
make init
make deploy
```

### Option 3: Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pyyaml pydantic rich typer requests

# Make CLI executable
chmod +x labctl
```

## ⚡ Quick Start

Get your home lab running in 5 minutes:

```bash
# 1. Install the CLI
./install.sh

# 2. Initialize configuration (interactive wizard)
./labctl init

# 3. Validate your setup
./labctl validate

# 4. Generate Docker Compose files
./labctl build

# 5. Deploy services (this takes a few minutes)
./labctl deploy --build --wait

# 6. Check status and get access URLs
./labctl status
```

**Important**: Ensure DNS records are configured and ports 80/443 are accessible before running `deploy` for automatic SSL certificates.

## 🎛️ CLI Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|----------|
| `init` | Interactive configuration wizard | `./labctl init` |
| `validate` | Check configuration and requirements | `./labctl validate --preflight` |
| `build` | Generate Docker Compose files | `./labctl build` |
| `deploy` | Deploy and start services | `./labctl deploy --build --wait` |
| `status` | Show service status and URLs | `./labctl status` |
| `logs` | View service logs | `./labctl logs --follow --tail 100` |
| `stop` | Stop services and cleanup | `./labctl stop --volumes` |
| `config` | Manage configuration | `./labctl config --show` |

### Advanced Options

```bash
# Deploy specific services only
./labctl deploy --services traefik,grafana,prometheus

# View logs for specific services  
./labctl logs --services traefik --follow

# Build with custom output directory
./labctl build --output ./my-compose-files

# Stop and remove volumes (destructive!)
./labctl stop --volumes --images

# Show specific config values
./labctl config --key core.domain

# Migrate from old config format
./labctl migrate old-config.yaml --output config.yaml
```

### Makefile Shortcuts

```bash
make help           # Show all available commands
make quickstart     # Complete setup: install + init + build + deploy
make install        # Install CLI dependencies only
make validate       # Validate configuration  
make build          # Generate Docker Compose files
make deploy         # Deploy services (build + wait)
make status         # Check service status
make logs           # Show service logs (tail 50)
make stop           # Stop all services
make clean          # Stop and remove volumes/images
make backup         # Run backup (if configured)
make monitor        # Show monitoring dashboard URL
```

## 💼 Use Cases

### 1. Home Network Setup (Pi-hole + Monitoring)

**Goal**: Block ads network-wide and monitor your infrastructure.

**Services**: Traefik, Pi-hole, Prometheus, Grafana, Uptime Kuma

```bash
./labctl init
# During setup, select:
# ✅ Traefik (required)
# ✅ Pi-hole  
# ✅ Prometheus
# ✅ Grafana
# ✅ Uptime Kuma

./labctl deploy --build --wait

# Access your services:
# Pi-hole: https://pihole.homelab.example.com
# Grafana: https://grafana.homelab.example.com  
# Uptime: https://uptime.homelab.example.com
```

### 2. Personal Cloud Storage (Nextcloud)

**Goal**: Self-hosted alternative to Google Drive/Dropbox.

**Services**: Traefik, Nextcloud, PostgreSQL, Redis

```bash
./labctl init
# Select: Traefik, Nextcloud, PostgreSQL, Redis

./labctl deploy --build --wait

# Access: https://nextcloud.homelab.example.com
# Initial admin setup required on first visit
```

### 3. Development Platform (GitLab)

**Goal**: Complete DevOps platform with Git, CI/CD, and container registry.

**Services**: Traefik, GitLab, PostgreSQL, Redis  

```bash
./labctl init
# Select: Traefik, GitLab, PostgreSQL, Redis

./labctl deploy --build --wait

# Access: https://gitlab.homelab.example.com
# First login: root / check generated password in logs
./labctl logs --services gitlab --tail 50 | grep password
```

### 4. Password Management (Vaultwarden)

**Goal**: Self-hosted Bitwarden server for password management.

**Services**: Traefik, Vaultwarden, PostgreSQL

```bash
./labctl init
# Select: Traefik, Vaultwarden, PostgreSQL

./labctl deploy --build --wait

# Access: https://vaultwarden.homelab.example.com
# Create admin account on first visit
```

### 5. Monitoring-Only Stack

**Goal**: Comprehensive monitoring without other services.

**Services**: Traefik, Prometheus, Grafana, Uptime Kuma

```bash
./labctl init
# Select monitoring services only

./labctl deploy --build --wait

# Access:
# Grafana: https://grafana.homelab.example.com
# Uptime Kuma: https://uptime.homelab.example.com
```

## ⚙️ Configuration

### Configuration Files

| File | Purpose |
|------|----------|
| `config/config.yaml` | Main configuration (generated by `init`) |
| `config/config.example.yaml` | Configuration template |
| `.env` | Generated secrets and environment variables |
| `docker-compose.yml` | Generated Docker Compose file |

### Basic Configuration Example

```yaml
# Minimal config.yaml example
core:
  domain: homelab.example.com
  email: admin@homelab.example.com
  timezone: America/New_York

reverse_proxy:
  provider: traefik
  ssl_provider: letsencrypt
  staging: false  # Set to true for testing

services:
  traefik:
    enabled: true
  prometheus: 
    enabled: true
  grafana:
    enabled: true
  pihole:
    enabled: false

# Custom environment variables for services
custom_env:
  variables:
    grafana:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=your_secure_password
```

### Service URLs

Services are automatically available at `https://{service}.{domain}`:

- Traefik Dashboard: `https://traefik.homelab.example.com`
- Grafana: `https://grafana.homelab.example.com`  
- Pi-hole: `https://pihole.homelab.example.com`
- Nextcloud: `https://nextcloud.homelab.example.com`
- GitLab: `https://gitlab.homelab.example.com`

### Security Notes

- Generated passwords are stored in `.env` - keep this file secure
- Never commit `.env` to version control
- Use `staging: true` for testing to avoid Let's Encrypt rate limits
- Generated certificates are stored in `ssl/` directory

## 🔧 Troubleshooting

### Common Issues

#### Ports 80/443 Already in Use
```bash
# Check what's using the ports
sudo lsof -i :80 -i :443

# Common culprits: nginx, apache, other reverse proxies
sudo systemctl stop nginx
sudo systemctl stop apache2
```

#### SSL Certificates Not Issuing
```bash
# Check Traefik logs
./labctl logs --services traefik --tail 200

# Common causes:
# 1. DNS records not pointing to your server
# 2. Ports 80/443 not accessible from internet  
# 3. Domain validation failing

# Use staging for testing:
# Set staging: true in config.yaml, then:
./labctl build
./labctl deploy --build
```

#### Services Not Starting/Unhealthy
```bash  
# Check overall status
./labctl status

# View logs for problematic service
./labctl logs --services {service-name} --tail 100

# Validate configuration
./labctl validate --preflight

# Check generated Docker Compose
cat docker-compose.yml
```

#### Permission Errors on Volumes
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
sudo chmod -R 755 data/

# Restart affected services
./labctl stop --services {service-name}
./labctl deploy --services {service-name}
```

#### Docker/Compose Issues  
```bash
# Update Docker and Compose
# macOS: Update Docker Desktop
# Linux: Update docker-ce and docker-compose-plugin

# Verify versions
docker --version      # Should be 20.10+
docker compose version  # Should be v2.x

# Clean Docker system
docker system prune -f
```

### Getting Help

```bash
# CLI help for any command
./labctl --help
./labctl {command} --help

# Enable debug output
./labctl --debug {command}

# Check system status
./labctl validate --preflight
```

## 🔄 Maintenance

### Updates

```bash
# Update Docker images
make docker-pull

# Redeploy with new images
./labctl deploy --build --wait

# Or use shortcut
make deploy
```

### Backups

```bash
# Run backup (if configured)
make backup

# Restore from backup  
make restore
```

### Adding New Services

```bash
# Re-run init to select additional services
./labctl init --force

# Rebuild and deploy
./labctl build
./labctl deploy --build --wait
```

### Monitoring

```bash
# Check service status
./labctl status

# View real-time logs
./labctl logs --follow

# Open monitoring dashboard
make monitor
```

## 💡 Best Practices

### Security
- Keep `.env` file secure and never commit to version control
- Use strong domain names (avoid common subdomains)
- Enable staging certificates for initial testing
- Regularly update Docker images
- Monitor service logs for security issues

### DNS and Certificates
- Ensure time synchronization (NTP) for proper certificate validation
- Use DNS validation for Let's Encrypt when possible
- Test with staging certificates before going production
- Monitor certificate expiration dates

### Resource Management  
- Start with core services, add more incrementally
- Monitor resource usage with Grafana dashboards
- Plan storage requirements for each service
- Regular cleanup of unused Docker images/volumes

### Configuration Management
- Keep configuration files in version control (except `.env`)
- Document custom environment variables
- Use descriptive service URLs/hostnames
- Test configuration changes in staging first

## 📚 Key File Locations

### CLI and Configuration
- `labctl` - Main CLI wrapper script
- `cli/labctl/` - CLI source code and commands  
- `config/config.yaml` - Main configuration (generated)
- `config/services/` - Service template definitions
- `.env` - Generated environment variables and secrets

### Generated Infrastructure  
- `docker-compose.yml` - Generated Docker Compose file
- `prometheus.yml` - Generated Prometheus configuration
- `compose/` - Additional Docker Compose files

### Runtime Data
- `data/` - Persistent service data volumes
- `ssl/` - SSL certificates and ACME storage  
- `logs/` - Application log files
- `backups/` - Backup storage location

### Project Management
- `Makefile` - Task automation and shortcuts
- `install.sh` - Installation and setup script
- `pyproject.toml` - Python package configuration

---

## 🎉 You're Ready!

Your enterprise home lab infrastructure is now ready to deploy. Start with the [Quick Start](#-quick-start) section and you'll have a fully functional home lab in minutes.

For questions or issues, check the [Troubleshooting](#-troubleshooting) section or run commands with `--debug` for detailed output.

**Happy self-hosting!** 🚀
