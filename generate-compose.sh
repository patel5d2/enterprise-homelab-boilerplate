#!/bin/bash

# Quick Docker Compose Generator for Home Lab
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

main() {
    print_status "🐳 Generating Docker Compose configuration..."
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_warning "Virtual environment not found. Run ./install.sh first."
        exit 1
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Set Python path
    export PYTHONPATH="$SCRIPT_DIR/cli:$PYTHONPATH"
    
    # Run the compose generator
    python3 -c "
from cli.labctl.core.config import Config
from cli.labctl.core.compose import ComposeGenerator
from pathlib import Path

try:
    # Load config
    config_file = Path('examples/config.yaml') if Path('examples/config.yaml').exists() else Path('config.yaml')
    if not config_file.exists():
        print('❌ No configuration file found. Please create config.yaml or run ./install.sh init')
        exit(1)
    
    print(f'📋 Loading configuration from {config_file}')
    config = Config.load_from_file(config_file)
    
    # Generate compose
    generator = ComposeGenerator(config)
    
    # Save files
    generator.save_compose_file(Path('docker-compose.yml'))
    generator.save_env_template(Path('.env.template'))
    
    print('✅ Generated docker-compose.yml')
    print('✅ Generated .env.template')
    
    # Show summary
    compose_config = generator.generate_compose()
    services = list(compose_config['services'].keys())
    print(f'📦 Generated {len(services)} services:')
    for service in sorted(services):
        print(f'  • {service}')
        
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Docker Compose configuration generated!"
        echo ""
        echo "Next steps:"
        echo "  1. Review docker-compose.yml"
        echo "  2. Copy .env.template to .env and configure secrets"
        echo "  3. Deploy with: ./labctl deploy"
        echo ""
        print_warning "Don't forget to configure environment variables in .env file!"
    else
        exit 1
    fi
}

main "$@"