#!/bin/bash

# Home Lab CLI Installation Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$SCRIPT_DIR/cli"
VENV_DIR="$SCRIPT_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed."
        print_status "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is required but not available."
        print_status "Please ensure Docker Compose is installed with Docker Desktop"
        exit 1
    fi
    
    print_success "All requirements satisfied"
}

setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_success "Created virtual environment"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install pyyaml pydantic rich typer requests
    
    print_success "Dependencies installed"
}

create_labctl_wrapper() {
    print_status "Creating labctl command wrapper..."
    
    cat > "$SCRIPT_DIR/labctl" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
export PYTHONPATH="$SCRIPT_DIR/cli:$PYTHONPATH"
python3 -m labctl.cli.main "$@"
EOF
    
    chmod +x "$SCRIPT_DIR/labctl"
    print_success "Created labctl wrapper"
}

initialize_project() {
    print_status "Initializing home lab project..."
    
    # Create basic directory structure
    mkdir -p examples
    mkdir -p config
    mkdir -p compose
    
    # Create directories for proper structure
    mkdir -p data logs ssl backups
    
    print_success "Project initialized"
}

show_usage() {
    echo ""
    print_success "🎉 Home Lab CLI installed successfully!"
    echo ""
    echo "CLI Usage:"
    echo "  ./labctl --help              Show help"
    echo "  ./labctl init                Interactive configuration wizard"
    echo "  ./labctl build              Generate Docker Compose files"
    echo "  ./labctl deploy             Deploy services"
    echo "  ./labctl status             Check service status"
    echo "  ./labctl stop               Stop services"
    echo ""
    echo "Quick Start:"
    echo "  1. Run: ./labctl init"
    echo "  2. Run: ./labctl build"
    echo "  3. Run: ./labctl deploy"
    echo ""
    print_warning "Use './labctl init' for the interactive setup wizard!"
}

main() {
    case "${1:-install}" in
        "install")
            print_status "🏠 Installing Home Lab CLI..."
            check_requirements
            setup_venv
            create_labctl_wrapper
            show_usage
            ;;
        "init")
            print_status "🚀 Initializing Home Lab project..."
            initialize_project
            show_usage
            ;;
        *)
            echo "Usage: $0 [install|init]"
            echo "  install - Install the CLI (default)"
            echo "  init    - Initialize project structure"
            exit 1
            ;;
    esac
}

main "$@"