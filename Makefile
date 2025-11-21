# Enterprise Home Lab Boilerplate Makefile
# Provides convenient commands for managing the home lab infrastructure

.PHONY: help init build deploy status stop clean install dev test lint format docs

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

# Installation and Setup
install: ## Install CLI dependencies
	@echo "📦 Installing CLI dependencies..."
	$(PIP) install -e .
	@echo "✅ Installation complete!"

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
check-prereqs: ## Check prerequisites
	@echo "🔍 Checking prerequisites..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
	@echo "✅ Prerequisites check passed!"

version: ## Show version information
	@echo "📋 Version information:"
	$(LABCTL) version

# Default configuration values
CONFIG_FILE ?= config.yaml
COMPOSE_DIR ?= compose