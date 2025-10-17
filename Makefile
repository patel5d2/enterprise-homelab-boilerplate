# Enterprise Home Lab Boilerplate Makefile
# Provides convenient commands for managing the home lab infrastructure

.PHONY: help init build deploy status stop clean install dev test lint format docs

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
	cd cli && pip install -e .
	@echo "✅ Installation complete!"

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	cd cli && pip install -e ".[dev]"
	@echo "✅ Development installation complete!"

# Home Lab Management
init: ## Initialize home lab configuration
	@echo "🚀 Initializing home lab configuration..."
	labctl init

validate: ## Validate configuration
	@echo "🔍 Validating configuration..."
	labctl validate

build: ## Build Docker Compose files
	@echo "🔨 Building Docker Compose configurations..."
	labctl build

deploy: ## Deploy home lab services
	@echo "🚀 Deploying home lab services..."
	labctl deploy --build --wait

status: ## Show service status
	@echo "📊 Checking service status..."
	labctl status

logs: ## Show service logs
	@echo "📋 Showing service logs..."
	labctl logs --tail 50

stop: ## Stop all services
	@echo "🛑 Stopping services..."
	labctl stop

clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	labctl stop --volumes --images

# Development
dev: ## Set up development environment
	@echo "🔧 Setting up development environment..."
	python -m venv .venv
	. .venv/bin/activate && pip install -e cli/[dev]
	@echo "✅ Development environment ready!"

test: ## Run tests
	@echo "🧪 Running tests..."
	cd cli && python -m pytest tests/ -v

lint: ## Run linting
	@echo "🔍 Running linting..."
	cd cli && python -m flake8 labctl/
	cd cli && python -m mypy labctl/

format: ## Format code
	@echo "✨ Formatting code..."
	cd cli && python -m black labctl/
	cd cli && python -m isort labctl/

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
	labctl backup run

restore: ## Restore from backup
	@echo "🔄 Restoring from backup..."
	labctl backup restore --snapshot latest

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "Documentation generation not implemented yet"

# Monitoring
monitor: ## Open monitoring dashboard
	@echo "📊 Opening monitoring dashboard..."
	@echo "Visit: https://grafana.$(shell labctl config --key core.domain || echo 'homelab.local')"

# Security
security-scan: ## Run security scan
	@echo "🔒 Running security scan..."
	labctl security scan

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
	labctl version

# Default configuration values
CONFIG_FILE ?= config/config.yaml
COMPOSE_DIR ?= compose