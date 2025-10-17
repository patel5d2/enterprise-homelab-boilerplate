# 🏠 Enterprise Home Lab Boilerplate

A comprehensive, enterprise-grade home lab infrastructure boilerplate with **interactive service selection** and Docker Compose automation.

## ✨ Features

- **🎯 Interactive Service Selection** - Choose exactly what you want to install
- **🚀 One-Click Deployment** - Complete infrastructure setup in minutes
- **🔄 Full Lifecycle Management** - Build, deploy, monitor, and manage services
- **🌐 SSL Certificates** - Automatic HTTPS with Let's Encrypt
- **📊 Monitoring & Dashboards** - Built-in observability stack
- **🔒 Security First** - Enterprise security practices baked in

## 📦 Available Services

### Core Infrastructure
- **✅ Traefik** - Reverse proxy with automatic SSL
- **📊 Prometheus + Grafana** - Monitoring and visualization
- **🗄️ PostgreSQL & Redis** - Primary databases

### Networking & DNS
- **🌐 Cloudflared** - Zero Trust tunnel (no port forwarding needed)
- **🔗 Headscale** - Self-hosted Tailscale coordination server
- **🚫 Pi-hole** - DNS ad-blocking and local DNS resolution

### Security & Secrets
- **🔐 Vaultwarden** - Self-hosted Bitwarden password manager
- **🏛️ HashiCorp Vault** - Enterprise secrets management

### Dashboards & Monitoring
- **👀 Glance** - Beautiful home lab dashboard
- **📈 Uptime Kuma** - Uptime monitoring with notifications

### Development & CI/CD
- **🦊 GitLab CE** - Git repositories, CI/CD, and container registry
- **⚙️ Jenkins** - Classic CI/CD automation server

### Storage & Backups
- **📄 MongoDB** - Document database
- **💾 pgBackRest** - PostgreSQL backup solution
- **☁️ S3-Compatible Backups** - Automated backup workflows

### Automation & Docs
- **🔄 n8n** - Visual workflow automation
- **📚 Fumadocs** - Beautiful documentation platform

### Alternative Proxies
- **📡 Nginx Proxy Manager** - Web-based proxy management
- **⚡ Caddy** - Modern web server with automatic HTTPS

## 🚀 Quick Start

### 1. Prerequisites

- **Docker & Docker Compose** (included with Docker Desktop)
- **Git** (for cloning and version control)
- **Domain name** (optional, can use `.local` for testing)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/patel5d2/enterprise-homelab-boilerplate
cd home-lab-boilerplate

# Make scripts executable and install
chmod +x install.sh labctl
./install.sh

# This will:
# ✅ Check system requirements
# ✅ Create Python virtual environment
# ✅ Install dependencies
# ✅ Set up CLI command structure
```

### 3. Interactive Configuration

```bash
python3 -m venv venv
#-
source venv/bin/activate && pip install -e .
# Interactive setup wizard with rich CLI interface
./labctl init

# Generate your infrastructure
./labctl build

# Deploy services
./labctl deploy
```

The interactive wizard features:
- 🎨 **Beautiful CLI interface** with colors, panels, and progress bars
- 📋 **Step-by-step configuration** with helpful examples and tips
- 🎛️ **Categorized service selection** - choose exactly what you want
- ⚙️ **Detailed service configuration** - storage, SSL, themes, plugins
- 🔐 **Automatic secure password generation**
- 📊 **Configuration summary** before deployment
- 🚀 **Ready-to-deploy files** generated automatically

**Service Categories Available:**
- Core Infrastructure, Monitoring, Networking & DNS
- Security & Secrets, Development & CI/CD
- Storage & Databases, Automation & Workflows
- Documentation & Wiki, Media & Entertainment
- Alternative Proxies

## 🎮 CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Interactive setup wizard | `./labctl init` |
| `build` | Generate Docker Compose files | `./labctl build` |
| `deploy` | Deploy services | `./labctl deploy` |
| `status` | Check service status | `./labctl status` |
| `logs` | View service logs | `./labctl logs -f traefik` |
| `stop` | Stop services | `./labctl stop --volumes` |
| `config` | Manage configuration | `./labctl config --show` |

## 🌐 Service Access

After deployment, access your services at:

| Service | URL | Description |
|---------|-----|-------------|
| Traefik Dashboard | `https://traefik.yourdomain.com` | Reverse proxy management |
| Grafana | `https://grafana.yourdomain.com` | Metrics visualization |
| Pi-hole | `https://pihole.yourdomain.com` | DNS management |
| Vaultwarden | `https://vault.yourdomain.com` | Password manager |
| Glance | `https://dashboard.yourdomain.com` | Home lab dashboard |
| Uptime Kuma | `https://uptime.yourdomain.com` | Uptime monitoring |

## 🚨 Troubleshooting

### Common Issues

**❌ "Docker not found"**
```bash
# Install Docker Desktop from docker.com
docker --version
```

**❌ "Permission denied"**
```bash
chmod +x install.sh labctl
```

**❌ "Port already in use"**
```bash
# Check what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/awesome-service`)
3. Add your service to the compose generator
4. Test thoroughly
5. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for the self-hosting community**
