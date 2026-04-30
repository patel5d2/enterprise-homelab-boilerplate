# 🏠 Enterprise Home Lab CLI

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://docs.docker.com/get-docker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive, enterprise-grade home lab infrastructure management system with **interactive service selection**, automated Docker Compose generation, and full lifecycle management.

## 🚀 Quick Start

```bash
git clone https://github.com/patel5d2/enterprise-homelab-boilerplate
cd enterprise-homelab-boilerplate
./bootstrap.sh
```

That's it. Bootstrap handles everything: prerequisites, Python venv, package install, `.env` generation, and a final health check. See the [Starter Guide](StarterGuide.md) for a step-by-step walkthrough with expected output.

## 🏗️ Architecture

```mermaid
graph TB
    User[👤 User] --> CLI[🎮 labctl CLI]
    CLI --> Init[labctl init\nSetup Wizard]
    CLI --> Build[labctl build\nCompose Generator]
    CLI --> Deploy[labctl deploy\nLifecycle Mgmt]
    CLI --> Doctor[labctl doctor\nHealth Checks]

    Init --> ConfigYAML[📄 config/config.yaml\nnon-secrets]
    Init --> DotEnv[🔐 .env\nsecrets]

    Build --> Schemas[config/services-v2/*.yaml\n17 service schemas]
    Build --> Compose[🐳 Docker Compose files]

    subgraph "Core Infrastructure"
        Traefik[🌐 Traefik + Let's Encrypt]
        PG[(🗄️ PostgreSQL)]
        Redis[(⚡ Redis)]
    end

    subgraph "Optional Services"
        Monitor[📊 Prometheus + Grafana]
        Vault[🔐 Vaultwarden]
        Cloud[☁️ Nextcloud]
        Git[🦊 GitLab CE]
        More[... 11 more]
    end

    Compose --> Traefik
    Compose --> PG
    Compose --> Redis
    Compose --> Monitor
    Compose --> Vault
```

## 📦 Available Services (17)

| Category | Services |
|---|---|
| **Core Infrastructure** | Traefik, PostgreSQL, Redis, MongoDB |
| **Monitoring** | Prometheus, Grafana, Monitoring Stack, Uptime Kuma |
| **Security & Secrets** | Vaultwarden |
| **Storage & Collaboration** | Nextcloud, BookStack |
| **Networking & DNS** | Pi-hole, Nginx Proxy Manager |
| **Dev & CI/CD** | GitLab, Jenkins, n8n |
| **Dashboards** | Glance |

## 🎮 CLI Reference

```
labctl init       — Interactive service setup wizard
labctl init -s postgresql  — Reconfigure one service only
labctl doctor     — Post-install health check
labctl build      — Generate Docker Compose files
labctl deploy     — Start services
labctl status     — Show running services
labctl validate   — Validate config.yaml
labctl logs       — Tail service logs
labctl stop       — Stop all services
```

## 📚 Documentation

- **[Starter Guide](StarterGuide.md)** — Fresh machine walkthrough with expected output
- **[Architecture](docs/architecture.md)** — How the modules fit together
- **[Customizing](docs/customizing.md)** — Adding services, overriding defaults
- **[Service Docs](docs/services/)** — Per-service configuration reference

## 🔒 Security Notes

- Secrets are generated automatically and stored only in `.env` (never in `config.yaml`)
- `.env` is in `.gitignore` — never commit it
- Traefik uses Let's Encrypt automatically via Cloudflare DNS challenge
- All service passwords are cryptographically random (≥24 chars)

## 🤝 Contributing

1. Fork → branch → PR
2. `make test` must pass
3. New services: add a schema to `config/services-v2/` following [SCHEMA.md](config/services-v2/SCHEMA.md)
