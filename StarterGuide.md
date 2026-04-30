# Enterprise Home Lab — Starter Guide

Fresh-machine walkthrough: **clone → bootstrap → init → deploy**.

---

## 1. Clone the repo

```bash
git clone https://github.com/you/enterprise-homelab-boilerplate
cd enterprise-homelab-boilerplate
```

---

## 2. Bootstrap (one command)

```bash
./bootstrap.sh
```

Expected output (macOS example):

```
▶ Detecting operating system
[OK]      macOS (Darwin) detected

▶ Checking Homebrew
[OK]      Homebrew is installed

▶ Checking Python 3.11+
[OK]      Found compatible Python: Python 3.12.3

▶ Checking Docker
[OK]      Docker 26.1.0 with Compose v2.27.0 found

▶ Checking essential tools (make, git, curl)
[OK]      make / git / curl are installed

▶ Setting up Python virtual environment
[OK]      Created venv at ./venv with Python 3.12

▶ Installing labctl package (pip install -e .[dev])
[OK]      labctl package installed

▶ Adding labctl to PATH
? Choice [1/2/3, default=1]: 1    ← adds symlink to ~/.local/bin

▶ Setting up .env file
[OK]      Generated .env with auto-filled secrets

▶ Running post-install health check
✓  Python 3.11+
✓  Virtual environment
✓  Docker + Compose
✓  .env file
...

╔════════════════════════════════════════════╗
║  🎉  Bootstrap complete!                   ║
╚════════════════════════════════════════════╝
```

> **Tip — CI / non-interactive mode:**
> ```bash
> ./bootstrap.sh --non-interactive   # or: make bootstrap-ci
> ```

---

## 3. Configure your services

```bash
labctl init
```

The wizard walks you through each service category:

```
── Core Infrastructure ──
  Enable Traefik  Modern reverse proxy with automatic SSL certificates? [Y/n]: Y
  Enable PostgreSQL  Enterprise-grade relational database? [Y/n]: Y
  Enable Redis  In-memory data structure store? [Y/n]: Y

── Monitoring & Observability ──
  Enable Monitoring Stack  Prometheus, Grafana, and AlertManager? [y/N]: Y

── Security & Secrets ──
  Enable Vaultwarden  Self-hosted Bitwarden-compatible password manager? [y/N]: n
...

⚙  Configuring Traefik
──────────────────────────────────────────────────────────────
  Primary domain  (e.g. homelab.example.com): homelab.example.com
  Admin email: admin@example.com
  Generate secure password for Dashboard password? [Y/n]: Y ✓

...

Enabled (4): traefik, postgresql, redis, monitoring
Disabled: 13 other service(s)
🔐 6 secret(s) written to .env

✅ Configuration saved → config/config.yaml
✅ Secrets merged   → .env
```

**Re-run safely at any time** — existing values appear as defaults, press Enter to keep:

```bash
labctl init                    # reconfigure everything
labctl init --service grafana  # reconfigure one service only
```

---

## 4. Review your .env

```bash
cat .env
```

Auto-generated secrets are already filled in. Fill in the `# TODO` entries for external providers:

```bash
# TODO: Set CLOUDFLARE_TUNNEL_TOKEN — your Cloudflare API token
CLOUDFLARE_TUNNEL_TOKEN=<paste your token here>
```

---

## 5. Deploy

```bash
labctl build    # generates docker-compose files from config
labctl deploy   # starts all enabled services
labctl status   # shows what's running
```

---

## 6. Health check (anytime)

```bash
labctl doctor
```

```
╭──────────────────────────────────────────────╮
│ 🩺 labctl doctor — Post-install health check │
╰──────────────────────────────────────────────╯

✓  Python 3.11+                Python 3.12.3 ✓, package importable ✓
✓  Virtual environment         venv at ./venv/ active ✓
✓  Docker + Compose            Docker 26.1.0, Compose v2.27.0
✓  .env file                   .env found (14 variable(s) set)
✗  .env required vars          1 variable(s) still need manual values: CLOUDFLARE_TUNNEL_TOKEN
✓  config.yaml                 config.yaml OK — 4 service(s) enabled
✓  Service env vars            All required service env vars are set

Remediation hints:
  ▶ .env required vars
    Edit .env and fill in the # TODO entries, then re-run: labctl doctor

6/7 checks passed
```

---

## 🔍 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `venv not found` | Run `./bootstrap.sh` |
| `labctl: command not found` | Run `./bootstrap.sh` and choose option 1 (symlink to `~/.local/bin`) |
| `Python 3.8 found (need ≥ 3.11)` | `brew install python@3.11` or use `pyenv install 3.11` |
| `Docker daemon not running` | Start Docker Desktop |
| `config.yaml not found` | Run `labctl init` |
| `7/7 checks failed` | Run `./bootstrap.sh` from scratch |
| Port conflict | Edit the port field in `labctl init --service <name>` |
| Let's Encrypt staging cert | Set `acme_environment: production` in `labctl init --service traefik` |

---

*Questions? Run `labctl --help` or `labctl <command> --help`.*
