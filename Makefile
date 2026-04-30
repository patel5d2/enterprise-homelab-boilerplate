# Enterprise Home Lab Boilerplate Makefile
# Provides convenient commands for managing the home lab infrastructure

.PHONY: help bootstrap bootstrap-ci bootstrap-dry-run init build deploy status stop clean install install-dev dev test lint format docs doctor guide check-prereqs version quickstart backup restore monitor security-scan docker-build docker-pull docker-logs docker-clean

# Virtual Environment
VENV ?= venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
LABCTL = $(VENV)/bin/labctl

# Default target
help: ## Show this help message
	@echo "Enterprise Home Lab Boilerplate"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Bootstrap — One-command fresh machine setup (Phase 1)
bootstrap: ## One-command fresh-machine setup (interactive)
	@echo "🚀 Starting Enterprise Home Lab bootstrap..."
	@bash bootstrap.sh

bootstrap-ci: ## Bootstrap in CI/non-interactive mode (no prompts)
	@echo "🚀 Starting non-interactive bootstrap (CI mode)..."
	@bash bootstrap.sh --non-interactive

bootstrap-dry-run: ## Show what bootstrap would do without doing it
	@echo "🔍 Dry-run bootstrap..."
	@bash bootstrap.sh --dry-run

# Installation and Setup
install: ## Install CLI dependencies (requires Python 3.11+)
	@echo "📦 Installing CLI dependencies..."
	@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null || \
	  { echo "❌ Python 3.11+ required. Current: $$(python3 --version 2>&1). Run: ./bootstrap.sh"; exit 1; }
	@if [ ! -d "$(VENV)" ]; then python3 -m venv $(VENV); fi
	$(PIP) install --quiet --upgrade pip
	$(PIP) install -e .
	@echo "✅ Installation complete!"

guide: ## Show the Starter Guide
	@cat StarterGuide.md

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	$(PIP) install -e ".[dev]"
	@echo "✅ Development installation complete!"

# Home Lab Management
init: ## Initialize home lab configuration
	@echo "🚀 Initializing home lab configuration..."
	$(LABCTL) init

validate: ## Validate configuration
	@echo "🔍 Validating configuration..."
	$(LABCTL) validate

build: ## Build Docker Compose files
	@echo "🔨 Building Docker Compose configurations..."
	$(LABCTL) build

deploy: ## Deploy home lab services
	@echo "🚀 Deploying home lab services..."
	$(LABCTL) deploy --build --wait

status: ## Show service status
	@echo "📊 Checking service status..."
	$(LABCTL) status

logs: ## Show service logs
	@echo "📋 Showing service logs..."
	$(LABCTL) logs --tail 50

stop: ## Stop all services
	@echo "🛑 Stopping services..."
	$(LABCTL) stop

clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	$(LABCTL) stop --volumes --images

# Development
dev: ## Set up development environment
	@echo "🔧 Setting up development environment..."
	python3 -m venv $(VENV)
	$(PIP) install -e .[dev]
	@echo "✅ Development environment ready!"

test: ## Run tests
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest tests/ -v

lint: ## Run linting
	@echo "🔍 Running linting..."
	$(PYTHON) -m flake8 cli/labctl/
	$(PYTHON) -m mypy cli/labctl/

format: ## Format code
	@echo "✨ Formatting code..."
	$(PYTHON) -m black cli/labctl/
	$(PYTHON) -m isort cli/labctl/

# Docker Management
docker-build: ## Build custom Docker images
	@echo "🐳 Building custom Docker images..."
	docker compose -f compose/docker-compose.yml build

docker-pull: ## Pull latest Docker images
	@echo "📥 Pulling latest Docker images..."
	docker compose -f compose/docker-compose.yml pull

docker-logs: ## Show Docker Compose logs
	@echo "📋 Showing Docker Compose logs..."
	docker compose -f compose/docker-compose.yml logs -f --tail=100

docker-clean: ## Clean Docker system
	@echo "🧹 Cleaning Docker system..."
	docker system prune -f
	docker volume prune -f

# Backup and Restore
backup: ## Run backup
	@echo "💾 Running backup..."
	$(LABCTL) backup run

restore: ## Restore from backup
	@echo "🔄 Restoring from backup..."
	$(LABCTL) backup restore --snapshot latest

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "Documentation generation not implemented yet"

# Monitoring
monitor: ## Open monitoring dashboard
	@echo "📊 Opening monitoring dashboard..."
	@echo "Visit: https://grafana.$(shell $(LABCTL) config --key core.domain || echo 'homelab.local')"

# Security
security-scan: ## Run security scan
	@echo "🔒 Running security scan..."
	$(LABCTL) security scan

# Quick Start
quickstart: install init validate build deploy status ## Complete quickstart setup
	@echo ""
	@echo "🎉 Home Lab setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  • Check status: make status"
	@echo "  • View logs: make logs" 
	@echo "  • Open monitoring: make monitor"
	@echo ""

# Utilities
doctor: ## Run post-install health check
	@echo "🩺 Running health check..."
	@$(LABCTL) doctor 2>/dev/null || { echo "doctor command not yet registered — run: ./labctl --help"; }

check-prereqs: ## Check prerequisites
	@echo "🔍 Checking prerequisites..."
	@bash scripts/bootstrap/check_prereqs.sh

version: ## Show version information
	@echo "📋 Version information:"
	$(LABCTL) version

# Default configuration values
CONFIG_FILE ?= config.yaml
COMPOSE_DIR ?= compose