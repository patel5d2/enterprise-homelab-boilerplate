#!/bin/bash

# Prerequisites checker for Enterprise Home Lab Boilerplate

set -e

echo "🔍 Checking prerequisites for Enterprise Home Lab Boilerplate..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to check command
check_command() {
    local cmd=$1
    local name=$2
    local install_url=$3
    
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name is installed"
        "$cmd" --version 2>/dev/null | head -n 1 || echo "  Version info not available"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not installed"
        if [ -n "$install_url" ]; then
            echo -e "  Install: ${YELLOW}$install_url${NC}"
        fi
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Function to check Docker Compose specifically
check_docker_compose() {
    if docker compose version &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker Compose is available"
        docker compose version
        return 0
    else
        echo -e "${RED}✗${NC} Docker Compose is not available"
        echo -e "  Install Docker Compose V2: ${YELLOW}https://docs.docker.com/compose/install/${NC}"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Function to check Python version
check_python_version() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.11"
        
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION (meets requirement: $REQUIRED_VERSION+)"
        else
            echo -e "${YELLOW}⚠${NC} Python $PYTHON_VERSION (recommend $REQUIRED_VERSION+ for best compatibility)"
        fi
        return 0
    else
        echo -e "${RED}✗${NC} Python 3 is not installed"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# Function to check system resources
check_resources() {
    echo ""
    echo "📊 System Resources:"
    
    # Check available memory (in MB)
    if command -v free &> /dev/null; then
        MEM=$(free -m | grep '^Mem:' | awk '{print $2}')
        if [ "$MEM" -gt 4000 ]; then
            echo -e "${GREEN}✓${NC} Memory: ${MEM}MB (sufficient)"
        else
            echo -e "${YELLOW}⚠${NC} Memory: ${MEM}MB (recommend 4GB+ for full stack)"
        fi
    elif command -v sysctl &> /dev/null; then
        # macOS
        MEM=$(($(sysctl -n hw.memsize) / 1024 / 1024))
        if [ "$MEM" -gt 4000 ]; then
            echo -e "${GREEN}✓${NC} Memory: ${MEM}MB (sufficient)"
        else
            echo -e "${YELLOW}⚠${NC} Memory: ${MEM}MB (recommend 4GB+ for full stack)"
        fi
    fi
    
    # Check available disk space
    if command -v df &> /dev/null; then
        DISK_INFO=$(df -h . | tail -1)
        DISK_AVAIL=$(echo "$DISK_INFO" | awk '{print $4}')
        echo -e "${GREEN}✓${NC} Disk Space: $DISK_AVAIL available"
        
        # Extract numeric value for comparison (rough)
        DISK_NUM=$(echo "$DISK_AVAIL" | sed 's/[^0-9.]//g' | cut -d'.' -f1)
        if [ "$DISK_NUM" -lt 20 ] && [[ "$DISK_AVAIL" == *"G"* ]]; then
            echo -e "  ${YELLOW}⚠${NC} Recommend 20GB+ for containers and data"
        fi
    fi
}

# Check network connectivity
check_network() {
    echo ""
    echo "🌐 Network Connectivity:"
    
    if command -v ping &> /dev/null; then
        if ping -c 1 8.8.8.8 &> /dev/null; then
            echo -e "${GREEN}✓${NC} Internet connectivity"
        else
            echo -e "${YELLOW}⚠${NC} Limited internet connectivity"
        fi
        
        if ping -c 1 hub.docker.com &> /dev/null; then
            echo -e "${GREEN}✓${NC} Docker Hub reachable"
        else
            echo -e "${YELLOW}⚠${NC} Docker Hub not reachable"
        fi
    fi
}

echo "🐳 Docker Environment:"
check_command "docker" "Docker" "https://docs.docker.com/get-docker/"
check_docker_compose

# Check if Docker daemon is running
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker daemon is running"
    
    # Check Docker version
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo "  Docker version: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker daemon is not running"
    echo -e "  Start Docker and try again"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "🐍 Python Environment:"
check_python_version
check_command "pip3" "pip3" "https://pip.pypa.io/en/stable/installation/"

echo ""
echo "🛠️ Optional Tools:"
check_command "git" "Git" "https://git-scm.com/downloads/" || true
check_command "make" "Make" "Install build-essential (Linux) or Xcode tools (macOS)" || true
check_command "curl" "curl" "Usually pre-installed" || true

check_resources
check_network

echo ""
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All prerequisites are satisfied!${NC}"
    echo ""
    echo "🎯 Next steps:"
    echo "  1. Install CLI: ${YELLOW}cd cli && pip install -e .${NC}"
    echo "  2. Initialize: ${YELLOW}labctl init${NC}"
    echo "  3. Build: ${YELLOW}labctl build${NC}"
    echo "  4. Deploy: ${YELLOW}labctl deploy${NC}"
    echo ""
    echo "📚 Documentation: README.md"
    echo "💬 Support: https://github.com/patel5d2/enterprise-homelab-boilerplate/issues"
else
    echo -e "${RED}❌ $FAILURES prerequisite(s) missing${NC}"
    echo ""
    echo "Please install the missing requirements and run this check again."
    exit 1
fi