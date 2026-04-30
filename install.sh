#!/usr/bin/env bash
# install.sh — Compatibility shim
#
# This script is kept for backwards compatibility only.
# New installations should use bootstrap.sh directly.
#
# Usage (legacy):  ./install.sh [install|init]
# Recommended:     ./bootstrap.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[INFO] install.sh is a compatibility shim — forwarding to bootstrap.sh"
echo "[INFO] For full control, run: ./bootstrap.sh --help"
echo ""

# Pass through --non-interactive if provided
EXTRA_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --non-interactive|--dry-run) EXTRA_ARGS+=("$arg") ;;
    install|init) ;;  # Legacy positional args — silently ignore
    *) echo "[WARN] Unknown argument '$arg' — ignored" ;;
  esac
done

exec bash "$SCRIPT_DIR/bootstrap.sh" "${EXTRA_ARGS[@]}"