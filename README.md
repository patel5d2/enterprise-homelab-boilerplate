# 🏠 Enterprise Home Lab Boilerplate

A comprehensive, production-ready infrastructure-as-code solution for self-hosted services with advanced DevSecOps features, monitoring, and enterprise-grade security.

## ✨ Features

### 🔧 Core Infrastructure
- **Docker Compose** orchestration with advanced networking
- **Traefik** reverse proxy with automatic SSL/TLS (Let's Encrypt)
- **PostgreSQL & Redis** with performance tuning and security hardening
- **Automated backups** with S3-compatible storage support

### 🦊 DevSecOps Platform
- **GitLab Enterprise** with CI/CD, Container Registry, and Security Scanning
- **GitLab Runner** with multiple executors and auto-scaling
- **Vault** secret management with PKI and dynamic secrets
- **Integrated security scanning** (SAST, DAST, dependency scanning)

### 📊 Monitoring & Observability
- **Prometheus** metrics collection with custom exporters
- **Grafana** dashboards with alerting and team management
- **Loki** log aggregation and analysis
- **Alert Manager** with multi-channel notifications
- **Node Exporter** and **cAdvisor** for system and container metrics

### 🔒 Security & Compliance
- **Zero-trust networking** with service mesh architecture
- **LDAP/SAML integration** for enterprise SSO
- **Security headers** and **HSTS** enforcement
- **Automated vulnerability scanning** and compliance reporting
- **Encrypted communications** with mutual TLS

### 🎮 Management & CLI
- **`labctl`** - Powerful CLI for infrastructure management
- **Interactive setup wizard** with guided configuration
- **Health checking** and service monitoring
- **Automated deployment** with rollback capabilities

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Domain name with DNS control
- 4GB+ RAM, 20GB+ storage

### Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/patel5d2/enterprise-homelab-boilerplate.git
   cd enterprise-homelab-boilerplate
   ```

2. **Install CLI**:
   ```bash
   cd cli
   pip install -e .
   ```

3. **Initialize configuration**:
   ```bash
   labctl init
   ```

4. **Deploy infrastructure**:
   ```bash
   labctl build
   labctl deploy --wait
   ```

5. **Check status**:
   ```bash
   labctl status
   ```

## 📋 Configuration

The CLI provides an interactive setup wizard that configures:
- Domain and SSL certificates
- Email for Let's Encrypt
- Timezone and localization
- Feature selection (GitLab, Monitoring, Security, Vault)
- Network and storage settings

### Example Configuration
```yaml
core:
  domain: "homelab.example.com"
  email: "admin@example.com"
  timezone: "America/New_York"

reverse_proxy:
  provider: "traefik"
  ssl:
    provider: "letsencrypt"
    staging: false

monitoring:
  enabled: true
  retention: "30d"

gitlab:
  enabled: true
  runners: 3
  registry: true
  pages: true
  
security:
  enabled: true
  vulnerability_scanning: true
  compliance_reporting: true

vault:
  enabled: true
  auto_unseal: true
```

## 🛠️ CLI Commands

### Core Operations
```bash
# Initialize new configuration
labctl init [--interactive]

# Validate configuration
labctl validate [--strict]

# Build Docker Compose files
labctl build [--services service1,service2]

# Deploy services
labctl deploy [--build] [--wait] [--timeout 300]

# Check service status
labctl status [--watch]

# View logs
labctl logs [--follow] [--services service1,service2]

# Stop services
labctl stop [--volumes] [--images]
```

### Configuration Management
```bash
# View configuration
labctl config [--show] [--format yaml|json]

# Edit configuration
labctl config --edit

# Show specific setting
labctl config --key monitoring.enabled
```

## 🌐 Service Access

After deployment, services are available at:

- **Traefik Dashboard**: `https://traefik.yourdomain.com`
- **GitLab**: `https://gitlab.yourdomain.com`
- **Grafana**: `https://grafana.yourdomain.com`
- **Prometheus**: `https://prometheus.yourdomain.com`
- **Vault**: `https://vault.yourdomain.com`

## 📊 Monitoring & Alerts

### Pre-configured Dashboards
- System overview with CPU, memory, disk, network
- Docker container metrics and health
- GitLab CI/CD pipeline performance  
- Application-specific metrics and SLAs
- Security events and compliance status

### Alert Rules
- Resource utilization thresholds
- Service availability and health checks
- Security incidents and anomalies
- Backup and data protection status
- Certificate expiration warnings

## 🔧 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Traefik     │    │     GitLab      │    │   Monitoring    │
│  (Reverse Proxy)│    │   (DevSecOps)   │    │ (Prometheus +   │
│      + SSL      │    │                 │    │   Grafana)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis      │    │      Vault      │
│   (Database)    │    │     (Cache)     │    │   (Secrets)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔒 Security Features

- **Network Segmentation**: Isolated networks for different service tiers
- **Secret Management**: HashiCorp Vault integration for credential storage
- **SSL/TLS Everywhere**: Automatic certificate provisioning and renewal
- **Security Scanning**: Integrated vulnerability assessment tools
- **Access Control**: RBAC with LDAP/SAML integration
- **Audit Logging**: Comprehensive logging for compliance

## 🔄 Backup & Recovery

### Automated Backups
- Database backups (PostgreSQL dumps)
- Configuration backups (encrypted)
- Volume snapshots with retention policies
- S3-compatible remote storage support

### Disaster Recovery
- Infrastructure-as-code for easy rebuilding
- Documented recovery procedures
- Backup verification and testing
- RTO/RPO targets for critical services

## 🎯 Customization

### Adding New Services
1. Create service configuration in `services/`
2. Add Compose template
3. Update CLI command modules
4. Configure monitoring and alerts
5. Test deployment and rollback

### Custom Dashboards
- Grafana dashboard templates in `monitoring/dashboards/`
- Prometheus rules in `monitoring/rules/`
- Custom exporters and metrics

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [Service Documentation](docs/services/)
- [Monitoring Setup](docs/monitoring.md)
- [Security Hardening](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Docker and the containerization ecosystem
- Traefik for reverse proxy excellence
- GitLab for comprehensive DevSecOps platform
- Prometheus and Grafana for monitoring
- HashiCorp Vault for secret management

## 💬 Support

- 🐛 [Issue Tracker](https://github.com/patel5d2/enterprise-homelab-boilerplate/issues)
- 💬 [Discussions](https://github.com/patel5d2/enterprise-homelab-boilerplate/discussions)
- 📧 Email: support@yourdomain.com

---

**Made with ❤️ for the self-hosting community**