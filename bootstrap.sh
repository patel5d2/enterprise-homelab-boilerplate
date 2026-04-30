#!/usr/bin/env bash
# =============================================================================
# Enterprise Home Lab Boilerplate — Bootstrap Script
# =============================================================================
# One-command setup for a fresh machine. Idempotent: safe to re-run.
#
# Usage:
#   ./bootstrap.sh                # interactive (default)
#   ./bootstrap.sh --non-interactive  # CI mode — fail on missing prereqs
#   ./bootstrap.sh --dry-run      # print what would happen, do nothing
#
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants & state
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIRED_PYTHON_MINOR=11   # 3.x where x >= this
REQUIRED_PYTHON="3.${REQUIRED_PYTHON_MINOR}"

NON_INTERACTIVE=false
DRY_RUN=false

# ---------------------------------------------------------------------------
# Parse CLI flags
# ---------------------------------------------------------------------------
for arg in "$@"; do
  case "$arg" in
    --non-interactive) NON_INTERACTIVE=true ;;
    --dry-run)         DRY_RUN=true ;;
    --help|-h)
      echo "Usage: $0 [--non-interactive] [--dry-run]"
      echo "  --non-interactive  CI mode: use defaults, fail on missing prereqs"
      echo "  --dry-run          Print what would happen without doing anything"
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $arg" >&2
      echo "Run '$0 --help' for usage." >&2
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
BLU='\033[0;34m'
CYN='\033[0;36m'
BLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${BLU}[INFO]${NC}    $*"; }
success() { echo -e "${GRN}[OK]${NC}      $*"; }
warn()    { echo -e "${YLW}[WARN]${NC}    $*"; }
error()   { echo -e "${RED}[ERROR]${NC}   $*" >&2; }
step()    { echo -e "\n${BLD}${CYN}▶ $*${NC}"; }
dryrun()  { echo -e "${YLW}[DRY-RUN]${NC} Would: $*"; }

run() {
  # Execute a command, or just print it in dry-run mode
  if $DRY_RUN; then
    dryrun "$*"
  else
    "$@"
  fi
}

# Prompt helper: returns 0 (yes) or 1 (no). In non-interactive mode uses default.
# Usage: prompt_yes_no "Question?" [default_yes=true|false]
prompt_yes_no() {
  local question="$1"
  local default="${2:-true}"
  if $NON_INTERACTIVE; then
    if $default; then return 0; else return 1; fi
  fi
  local hint
  if $default; then hint="[Y/n]"; else hint="[y/N]"; fi
  while true; do
    read -r -p "$(echo -e "${YLW}?${NC} $question $hint: ")" answer
    case "${answer:-}" in
      [Yy]*|"") if $default; then return 0; else
                   case "${answer:-}" in [Yy]*) return 0;; *) return 1;; esac
                 fi ;;
      [Nn]*)    return 1 ;;
      *)        echo "  Please answer y or n." ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# Step 1 — OS Detection
# ---------------------------------------------------------------------------
step "Detecting operating system"

OS=""
PKG_MGR=""
case "$(uname -s)" in
  Darwin)
    OS="macos"
    PKG_MGR="brew"
    success "macOS (Darwin) detected"
    ;;
  Linux)
    if [ -f /etc/os-release ]; then
      # shellcheck source=/dev/null
      . /etc/os-release
      case "${ID:-}" in
        ubuntu|debian|linuxmint)
          OS="debian"
          PKG_MGR="apt"
          success "Debian/Ubuntu Linux detected (${PRETTY_NAME:-Linux})"
          ;;
        rhel|fedora|centos|rocky|almalinux)
          OS="rhel"
          PKG_MGR="dnf"
          success "RHEL/Fedora Linux detected (${PRETTY_NAME:-Linux})"
          ;;
        arch|manjaro|endeavouros)
          OS="arch"
          PKG_MGR="pacman"
          success "Arch Linux detected (${PRETTY_NAME:-Linux})"
          ;;
        *)
          error "Unsupported Linux distribution: ${ID:-unknown}"
          error "Supported: Debian/Ubuntu (apt), RHEL/Fedora (dnf), Arch (pacman)"
          exit 1
          ;;
      esac
    else
      error "Cannot determine Linux distribution (no /etc/os-release)"
      exit 1
    fi
    ;;
  *)
    error "Unsupported OS: $(uname -s)"
    error "Supported: macOS, Debian/Ubuntu, RHEL/Fedora, Arch Linux"
    exit 1
    ;;
esac

# ---------------------------------------------------------------------------
# Step 2 — Run check_prereqs.sh (wired in, read-only)
# ---------------------------------------------------------------------------
step "Running prerequisite check"

PREREQ_SCRIPT="$SCRIPT_DIR/scripts/bootstrap/check_prereqs.sh"
if [ -f "$PREREQ_SCRIPT" ]; then
  if $DRY_RUN; then
    dryrun "bash $PREREQ_SCRIPT (check only — not failing on missing prereqs)"
  else
    # Run prereq check but don't exit on failure — we'll install what's missing
    bash "$PREREQ_SCRIPT" || true
  fi
else
  warn "check_prereqs.sh not found at $PREREQ_SCRIPT — skipping"
fi

# ---------------------------------------------------------------------------
# Helper: install a package via the detected package manager
# ---------------------------------------------------------------------------
install_package() {
  local pkg_name="$1"
  local display_name="${2:-$pkg_name}"
  info "Installing $display_name..."
  case "$PKG_MGR" in
    brew)    run brew install "$pkg_name" ;;
    apt)     run sudo apt-get install -y "$pkg_name" ;;
    dnf)     run sudo dnf install -y "$pkg_name" ;;
    pacman)  run sudo pacman -S --noconfirm "$pkg_name" ;;
  esac
}

# ---------------------------------------------------------------------------
# Step 3a — Homebrew (macOS only)
# ---------------------------------------------------------------------------
if [ "$OS" = "macos" ]; then
  step "Checking Homebrew"
  if ! command -v brew &>/dev/null; then
    if $NON_INTERACTIVE; then
      error "Homebrew is required on macOS but is not installed."
      error "Install it from https://brew.sh then re-run this script."
      $DRY_RUN || exit 1
    fi
    warn "Homebrew is not installed."
    if prompt_yes_no "Install Homebrew now?"; then
      if $DRY_RUN; then
        dryrun '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
      else
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Apple Silicon: add brew to PATH for the rest of this session
        if [ -f /opt/homebrew/bin/brew ]; then
          eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
      fi
    else
      error "Homebrew is required to install other dependencies on macOS. Aborting."
      $DRY_RUN || exit 1
    fi
  else
    success "Homebrew is installed ($(brew --version | head -1))"
  fi
fi

# ---------------------------------------------------------------------------
# Step 3b — Python 3.11+
# ---------------------------------------------------------------------------
step "Checking Python ${REQUIRED_PYTHON}+"

PYTHON_BIN=""
# Try venv Python first (idempotent re-run), then system
for candidate in \
    "$VENV_DIR/bin/python3" \
    python3.14 python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" &>/dev/null 2>&1; then
    ver=$("$candidate" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
    maj=$("$candidate" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "0")
    if [ "$maj" -eq 3 ] && [ "$ver" -ge "$REQUIRED_PYTHON_MINOR" ]; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done

if [ -n "$PYTHON_BIN" ]; then
  PY_VER=$("$PYTHON_BIN" --version 2>&1)
  success "Found compatible Python: $PY_VER ($PYTHON_BIN)"
else
  # Check if an older Python3 exists
  if command -v python3 &>/dev/null; then
    OLD_VER=$(python3 --version 2>&1)
    warn "Found $OLD_VER but Python ${REQUIRED_PYTHON}+ is required."
    warn "We will NOT replace your system Python."
    warn "Recommended: install pyenv and run: pyenv install 3.11 && pyenv global 3.11"

    if $NON_INTERACTIVE; then
      error "Python ${REQUIRED_PYTHON}+ not found. Aborting (--non-interactive)."
      $DRY_RUN || exit 1
    fi

    if prompt_yes_no "Install Python ${REQUIRED_PYTHON} via package manager now?" false; then
      case "$OS" in
        macos)   install_package "python@${REQUIRED_PYTHON}" "Python ${REQUIRED_PYTHON}" ;;
        debian)  run sudo apt-get update && install_package "python${REQUIRED_PYTHON}" "Python ${REQUIRED_PYTHON}" ;;
        rhel)    install_package "python${REQUIRED_PYTHON/./}" "Python ${REQUIRED_PYTHON}" ;;
        arch)    install_package python "Python" ;;
      esac
      # Re-scan
      for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
        if command -v "$candidate" &>/dev/null 2>&1; then
          ver=$("$candidate" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
          maj=$("$candidate" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "0")
          if [ "$maj" -eq 3 ] && [ "$ver" -ge "$REQUIRED_PYTHON_MINOR" ]; then
            PYTHON_BIN="$candidate"
            break
          fi
        fi
      done
    fi
    if [ -z "$PYTHON_BIN" ]; then
      error "Python ${REQUIRED_PYTHON}+ still not found. Please install it manually."
      error "  macOS: brew install python@3.11"
      error "  Ubuntu: sudo apt install python3.11"
      error "  pyenv: https://github.com/pyenv/pyenv"
      $DRY_RUN || exit 1
    fi
  else
    # No Python3 at all
    if $NON_INTERACTIVE; then
      error "Python 3 not found. Aborting (--non-interactive)."
      $DRY_RUN || exit 1
    fi
    if prompt_yes_no "Python 3 not found. Install Python ${REQUIRED_PYTHON} now?"; then
      case "$OS" in
        macos)   install_package "python@${REQUIRED_PYTHON}" "Python ${REQUIRED_PYTHON}" ;;
        debian)  run sudo apt-get update && install_package "python${REQUIRED_PYTHON}" "Python ${REQUIRED_PYTHON}" ;;
        rhel)    install_package "python${REQUIRED_PYTHON/./}" "Python ${REQUIRED_PYTHON}" ;;
        arch)    install_package python "Python" ;;
      esac
      PYTHON_BIN="python3"
    else
      error "Python 3 is required. Aborting."
      $DRY_RUN || exit 1
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Step 3c — Docker + Compose plugin
# ---------------------------------------------------------------------------
step "Checking Docker"

DOCKER_MISSING=false
COMPOSE_MISSING=false

if ! command -v docker &>/dev/null; then
  DOCKER_MISSING=true
fi

if ! docker compose version &>/dev/null 2>&1; then
  COMPOSE_MISSING=true
fi

if $DOCKER_MISSING; then
  warn "Docker is not installed."
  if [ "$OS" = "macos" ]; then
    info "On macOS, Docker Desktop must be installed manually (license click-through required)."
    info "Download from: https://www.docker.com/products/docker-desktop/"
    if $NON_INTERACTIVE; then
      error "Docker not found. Aborting (--non-interactive). Install Docker Desktop and retry."
      $DRY_RUN || exit 1
    fi
    warn "Please install Docker Desktop, then re-run this script."
    echo ""
    read -r -p "Press [Enter] once Docker Desktop is installed, or Ctrl-C to abort..."
    if ! command -v docker &>/dev/null; then
      error "Docker still not found. Aborting."
      $DRY_RUN || exit 1
    fi
  else
    # Linux — can install via get.docker.com
    if $NON_INTERACTIVE; then
      error "Docker not found. Aborting (--non-interactive)."
      $DRY_RUN || exit 1
    fi
    if prompt_yes_no "Install Docker Engine via get.docker.com (requires sudo)?"; then
      if $DRY_RUN; then
        dryrun "curl -fsSL https://get.docker.com | sudo sh"
        dryrun "sudo usermod -aG docker ${USER:-root}"
      else
        curl -fsSL https://get.docker.com | sudo sh
        sudo usermod -aG docker "${USER:-root}"
        warn "Docker installed. You may need to log out and back in for group membership."
        warn "Or run: newgrp docker"
      fi
    else
      error "Docker is required. Aborting."
      $DRY_RUN || exit 1
    fi
  fi
elif $COMPOSE_MISSING; then
  warn "Docker Compose plugin (V2) is not available."
  info "Ensure Docker Desktop is up to date, or install the compose plugin:"
  info "  https://docs.docker.com/compose/install/"
  if $NON_INTERACTIVE; then
    error "Docker Compose not found. Aborting (--non-interactive)."
    $DRY_RUN || exit 1
  fi
else
  DOCKER_VER=$(docker --version 2>&1 | cut -d' ' -f3 | tr -d ',')
  COMPOSE_VER=$(docker compose version 2>&1 | awk '{print $NF}')
  success "Docker ${DOCKER_VER} with Compose ${COMPOSE_VER} found"
fi

# ---------------------------------------------------------------------------
# Step 3d — make, git, curl
# ---------------------------------------------------------------------------
step "Checking essential tools (make, git, curl)"

for tool in make git curl; do
  if command -v "$tool" &>/dev/null; then
    success "$tool is installed"
  else
    warn "$tool is not installed."
    if $NON_INTERACTIVE; then
      info "Installing $tool automatically (non-interactive mode)..."
      case "$OS" in
        macos)   run brew install "$tool" ;;
        debian)  run sudo apt-get install -y "$tool" ;;
        rhel)    run sudo dnf install -y "$tool" ;;
        arch)    run sudo pacman -S --noconfirm "$tool" ;;
      esac
    else
      if prompt_yes_no "Install $tool via $PKG_MGR?"; then
        install_package "$tool"
      else
        warn "Skipping $tool installation. Some features may not work."
      fi
    fi
  fi
done

# ---------------------------------------------------------------------------
# Step 4 — Create venv
# ---------------------------------------------------------------------------
step "Setting up Python virtual environment"

VENV_OK=false
if [ -d "$VENV_DIR" ]; then
  # Check if the existing venv has a compatible Python
  VENV_PY="$VENV_DIR/bin/python3"
  if [ -x "$VENV_PY" ]; then
    venv_ver=$("$VENV_PY" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
    venv_maj=$("$VENV_PY" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "0")
    if [ "$venv_maj" -eq 3 ] && [ "$venv_ver" -ge "$REQUIRED_PYTHON_MINOR" ]; then
      success "Existing venv at $VENV_DIR has Python 3.${venv_ver} — reusing"
      VENV_OK=true
    else
      warn "Existing venv has Python 3.${venv_ver} which is too old — recreating"
      run rm -rf "$VENV_DIR"
    fi
  fi
fi

if ! $VENV_OK; then
  info "Creating venv with $PYTHON_BIN at $VENV_DIR ..."
  run "$PYTHON_BIN" -m venv "$VENV_DIR"
  success "Virtual environment created"
fi

VENV_PIP="$VENV_DIR/bin/pip"
VENV_PYTHON="$VENV_DIR/bin/python3"

# ---------------------------------------------------------------------------
# Step 5 — Install package (pip install -e .[dev])
# ---------------------------------------------------------------------------
step "Installing labctl package (pip install -e .[dev])"

info "Upgrading pip inside venv..."
run "$VENV_PIP" install --quiet --upgrade pip

info "Installing package and dev dependencies..."
run "$VENV_PIP" install --quiet -e "$SCRIPT_DIR/.[dev]"
success "labctl package installed"

# ---------------------------------------------------------------------------
# Step 6 — Symlink labctl to PATH
# ---------------------------------------------------------------------------
step "Adding labctl to PATH"

LABCTL_SCRIPT="$SCRIPT_DIR/labctl"

# Ensure the launcher script is up-to-date
if $DRY_RUN; then
  dryrun "Write/verify $LABCTL_SCRIPT launcher"
else
  cat > "$LABCTL_SCRIPT" <<'LAUNCHER'
#!/usr/bin/env bash
# Auto-generated by bootstrap.sh — do not edit manually
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$SCRIPT_DIR/venv" ]; then
  echo "[ERROR] Virtual environment not found at $SCRIPT_DIR/venv"
  echo "        Run ./bootstrap.sh to set it up."
  exit 1
fi

source "$SCRIPT_DIR/venv/bin/activate"
export PYTHONPATH="$SCRIPT_DIR/cli:${PYTHONPATH:-}"
exec python3 -m labctl.cli.main "$@"
LAUNCHER
  chmod +x "$LABCTL_SCRIPT"
fi

if $NON_INTERACTIVE; then
  LINK_DEST="$HOME/.local/bin"
  DO_LINK=true
else
  echo ""
  echo "  Where should labctl be symlinked for system-wide access?"
  echo "  1) ~/.local/bin  (no sudo required, recommended)"
  echo "  2) /usr/local/bin  (requires sudo)"
  echo "  3) Skip (use ./labctl directly)"
  read -r -p "$(echo -e "${YLW}?${NC} Choice [1/2/3, default=1]: ")" link_choice
  case "${link_choice:-1}" in
    2) LINK_DEST="/usr/local/bin"; DO_LINK=true ;;
    3) LINK_DEST=""; DO_LINK=false; info "Skipping PATH symlink. Use ./labctl from the project root." ;;
    *) LINK_DEST="$HOME/.local/bin"; DO_LINK=true ;;
  esac
fi

if $DO_LINK && [ -n "$LINK_DEST" ]; then
  if $DRY_RUN; then
    dryrun "mkdir -p $LINK_DEST && ln -sf $LABCTL_SCRIPT $LINK_DEST/labctl"
  else
    mkdir -p "$LINK_DEST"
    if [ "$LINK_DEST" = "/usr/local/bin" ]; then
      sudo ln -sf "$LABCTL_SCRIPT" "$LINK_DEST/labctl"
    else
      ln -sf "$LABCTL_SCRIPT" "$LINK_DEST/labctl"
    fi
    success "labctl symlinked to $LINK_DEST/labctl"
  fi

  # Ensure ~/.local/bin is in PATH via shell rc
  if [ "$LINK_DEST" = "$HOME/.local/bin" ]; then
    PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
    for rcfile in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
      if [ -f "$rcfile" ] && ! grep -qF '.local/bin' "$rcfile"; then
        if $DRY_RUN; then
          dryrun "Append PATH export to $rcfile"
        else
          echo "" >> "$rcfile"
          echo "# Added by labctl bootstrap" >> "$rcfile"
          echo "$PATH_LINE" >> "$rcfile"
          info "Added ~/.local/bin to PATH in $rcfile"
        fi
      fi
    done
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

# ---------------------------------------------------------------------------
# Step 7 — Generate .env from .env.template
# ---------------------------------------------------------------------------
step "Setting up .env file"

ENV_FILE="$SCRIPT_DIR/.env"
ENV_TEMPLATE="$SCRIPT_DIR/.env.template"

if [ -f "$ENV_FILE" ]; then
  success ".env already exists — skipping generation"
else
  if [ ! -f "$ENV_TEMPLATE" ]; then
    warn ".env.template not found — skipping .env generation"
  else
    info "Generating .env from .env.template ..."
    if $DRY_RUN; then
      dryrun "Generate $ENV_FILE from $ENV_TEMPLATE with auto-filled secrets"
    else
      # Process each line of the template
      while IFS= read -r line || [ -n "$line" ]; do
        # Pass comments and blank lines through unchanged
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
          echo "$line"
          continue
        fi

        # Extract key and value
        key="${line%%=*}"
        value="${line#*=}"

        # Auto-generate for token/secret/password/key fields (if placeholder)
        if [[ "$value" =~ ^your- ]] || [[ "$value" =~ placeholder ]] || [[ "$value" =~ CHANGE_ME ]]; then
          lower_key="${key,,}"
          if [[ "$lower_key" =~ (token|secret|password|key|pass) ]] && \
             [[ ! "$lower_key" =~ (cloudflare|s3_key|s3_secret|s3_bucket) ]]; then
            generated=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
            echo "${key}=${generated}"
            info "  Auto-generated secret for ${key}"
            continue
          else
            # Provider-specific tokens — leave with # TODO comment
            echo "# TODO: Set ${key} — ${value}"
            warn "  Left blank (needs manual config): ${key}"
            continue
          fi
        fi

        # Pass through any already-set values
        echo "$line"
      done < "$ENV_TEMPLATE" > "$ENV_FILE"

      success ".env generated at $ENV_FILE"
      warn "Review .env and fill in any # TODO entries before deploying."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Step 8 — Run labctl doctor (Phase 3 — invoked if available)
# ---------------------------------------------------------------------------
step "Running post-install health check"

LABCTL_BIN="$VENV_DIR/bin/labctl"

if $DRY_RUN; then
  dryrun "labctl doctor (post-install verification)"
elif "$LABCTL_BIN" doctor &>/dev/null 2>&1; then
  "$LABCTL_BIN" doctor
elif command -v labctl &>/dev/null; then
  labctl doctor 2>/dev/null || true
else
  # doctor command not yet available — do a basic check
  if "$LABCTL_BIN" --help &>/dev/null 2>&1; then
    success "labctl is working correctly"
  else
    warn "Could not verify labctl. Try running: ./labctl --help"
  fi
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${GRN}${BLD}╔════════════════════════════════════════════╗${NC}"
echo -e "${GRN}${BLD}║  🎉  Bootstrap complete!                   ║${NC}"
echo -e "${GRN}${BLD}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLD}Next steps:${NC}"
echo -e "  1. Review your ${CYN}.env${NC} file and fill in any ${YLW}# TODO${NC} provider tokens"
echo -e "  2. ${CYN}labctl init${NC}    — run the interactive setup wizard"
echo -e "  3. ${CYN}labctl build${NC}   — generate Docker Compose files"
echo -e "  4. ${CYN}labctl deploy${NC}  — start your services"
echo ""
echo -e "  Run ${CYN}labctl --help${NC} to see all available commands."
echo ""
