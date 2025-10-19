#!/bin/bash

# WARP.md CLI Command Sync Script
# This script helps maintain the CLI commands section in WARP.md by comparing
# with the actual CLI help output

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WARP_FILE="$PROJECT_ROOT/WARP.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

if [ ! -f "$PROJECT_ROOT/labctl" ]; then
    print_error "labctl not found. Please run ./install.sh first"
    exit 1
fi

if [ ! -f "$WARP_FILE" ]; then
    print_error "WARP.md not found at $WARP_FILE"
    exit 1
fi

print_status "Checking CLI commands consistency..."

# Get current CLI help
cd "$PROJECT_ROOT"
CLI_COMMANDS=$(./labctl --help 2>/dev/null | grep -A20 "Commands" | grep "│" | grep -E "init|validate|build|deploy|status|logs|stop|config|version" | wc -l || echo "0")

if [ "$CLI_COMMANDS" -lt 5 ]; then
    print_warning "CLI help output seems incomplete (found $CLI_COMMANDS commands)"
    print_warning "This might indicate the CLI installation needs refresh"
    exit 0
fi

print_status "Found $CLI_COMMANDS CLI commands"

# Check if WARP.md mentions the main commands
MISSING_COMMANDS=""
for cmd in "init" "validate" "build" "deploy" "status" "logs" "stop" "config"; do
    if ! grep -q "./labctl $cmd" "$WARP_FILE"; then
        MISSING_COMMANDS="$MISSING_COMMANDS $cmd"
    fi
done

if [ -n "$MISSING_COMMANDS" ]; then
    print_warning "The following commands are missing from WARP.md:$MISSING_COMMANDS"
    print_status "Consider updating the Essential Commands section"
else
    print_status "All main CLI commands are documented in WARP.md"
fi

# Check make commands
MAKE_COMMANDS=$(make help 2>/dev/null | grep -E "build|deploy|status|logs|lint|format|test" | wc -l || echo "0")
print_status "Found $MAKE_COMMANDS relevant make commands"

if [ "$MAKE_COMMANDS" -lt 5 ]; then
    print_warning "Some make commands might be missing from documentation"
fi

print_status "WARP.md CLI consistency check completed"