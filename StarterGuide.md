# Enterprise Home Lab Boilerplate - Starter Guide

Welcome to the Enterprise Home Lab Boilerplate! This guide will walk you through setting up, configuring, and deploying your self-hosted infrastructure.

## 🚀 Quick Start

The fastest way to get up and running is using the `make quickstart` command. This will:
1.  Install dependencies (Python virtual environment, CLI tools).
2.  Initialize a default configuration.
3.  Validate your setup.
4.  Build Docker Compose files.
5.  Deploy the services.

```bash
make quickstart
```

Once complete, you can check the status of your services:

```bash
make status
```

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

*   **Docker & Docker Compose:** Required for running services.
*   **Python 3.8+:** Required for the CLI tool (`labctl`).
*   **Make:** Required for running automation commands.

## ⚙️ Configuration

The boilerplate uses a flexible configuration system.

### Main Configuration (`config.yaml`)
This file controls the core settings and which services are enabled.
Run `labctl init` to generate a default configuration if you haven't already.

**Example `config.yaml`:**
```yaml
version: 2
profile: prod  # 'prod' or 'dev'
core:
  domain: "example.com"
  email: "admin@example.com"

services:
  traefik:
    enabled: true
    domain: "example.com"
    # ...
  monitoring:
    enabled: true
    # ...
```

### Service Configurations (`config/services-v2/*.yaml`)
Each service has its own schema definition in `config/services-v2/`. You generally **do not** need to edit these unless you are adding custom services or modifying the default behavior of existing ones.

### Environment Variables (`.env`)
Secrets and sensitive information are stored in `.env` (generated from `.env.template`).
**Never commit `.env` to version control!**

## 🛠️ Common Operations

### Deploying Changes
After modifying `config.yaml`, deploy your changes:

```bash
# Build new compose files and deploy
make deploy
```

### Viewing Logs
To see logs for all services:
```bash
make logs
```
To see logs for a specific service (e.g., traefik):
```bash
docker compose -f config/compose/docker-compose.yml logs -f traefik
```

### Stopping Services
To stop all running services:
```bash
make stop
```

### Cleaning Up
To remove containers and volumes (WARNING: Data loss):
```bash
make clean
```

## 🔍 Troubleshooting

### "Configuration file already exists"
If `labctl init` says the config exists, you can choose to **skip** (keep existing), **reconfigure** (run wizard again), or **overwrite** (reset to defaults).

### "Validation failed"
Run `make validate` to see detailed errors.
- Check `config.yaml` for syntax errors.
- Ensure required fields (like `domain` and `email`) are set.

### "Docker path issues"
If you see errors about `docker-compose.yml` not found, ensure you ran `make build` or `labctl build` first.

## 📚 Advanced Usage

### Custom Services
You can add custom services by adding them to `config.yaml` under `services` if they have a schema, or by manually extending the generated `docker-compose.yml` (though manual edits will be overwritten on next build).

### CLI Tool (`labctl`)
The `labctl` CLI provides granular control. Run `labctl --help` to see all available commands.

---
*Happy Homelabbing!*
