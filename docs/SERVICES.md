# Available Services (v2)

This document lists all services available in the Enterprise Home Lab CLI wizard.

## Service Categories

### Core Infrastructure
- **traefik** - Modern reverse proxy with automatic SSL certificates and load balancing
- **postgresql** - Enterprise-grade relational database with high performance and reliability
- **redis** - In-memory data structure store for caching and message queuing
- **mongodb** - Document-oriented NoSQL database

### Observability
- **prometheus** - Time-series database and monitoring system for metrics collection  
- **grafana** - Beautiful dashboards and visualization for monitoring data

### DevOps
- **gitlab** - Complete DevOps platform with Git, CI/CD, and project management
- **jenkins** - Extensible automation server for continuous integration and deployment

### Productivity
- **bookstack** - Self-hosted wiki platform for organizing and sharing knowledge

### Automation
- **n8n** - Visual workflow automation platform for connecting apps and services

### Networking  
- **nginx_proxy_manager** - Easy-to-use reverse proxy management with SSL certificates

### Monitoring
- **uptime_kuma** - Self-hosted monitoring tool for websites and services

### Dashboard
- **glance** - Self-hosted dashboard for quick access to your services and information

### Applications
- **nextcloud** - Self-hosted cloud platform for file storage and collaboration
- **pihole** - Network-wide ad blocker and DNS sinkhole
- **vaultwarden** - Bitwarden-compatible password manager server

### Observability Stack
- **monitoring** - Complete monitoring stack with Prometheus, Grafana, and exporters

## Service Dependencies

Some services automatically include their dependencies:

- **grafana** → requires **prometheus**
- **gitlab** → requires **postgresql** and **redis**
- **n8n** → requires **postgresql** and **redis**
- **bookstack** → requires **postgresql**

## Using the Services

### CLI Wizard
Run the interactive setup wizard:
```bash
labctl init --interactive
```

The wizard will:
1. Let you select from all available services
2. Automatically resolve dependencies 
3. Guide you through service-specific configuration
4. Generate optimized Docker Compose files

### Available Profiles
- **dev** - Development/staging environment with relaxed security
- **prod** - Production environment with enhanced security and performance

## Service Schema Format

Each service is defined using a standardized v2 schema with:

- **Metadata**: ID, name, category, description, maturity level
- **Dependencies**: Automatic dependency resolution
- **Configuration Fields**: Type-validated user inputs
- **Docker Compose**: Container definitions and networking
- **Profile Defaults**: Environment-specific presets

## Migration from v1

Services have been migrated from the legacy v1 format with:
- Improved field validation and types
- Standardized dependency management  
- Profile-based configuration defaults
- Enhanced security with password generation
- Better UX with conditional fields

For detailed migration information, see [Migration Guide](migration/MIGRATION.md).