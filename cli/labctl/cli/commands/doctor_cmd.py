"""
doctor_cmd — Post-install health verification for Enterprise Home Lab CLI.

Checks:
  1. Python version and package importability
  2. Docker daemon reachable + Compose plugin present
  3. .env exists and required vars are set
  4. config.yaml parses and references only known services
  5. All enabled services have their required env vars populated

Prints ✓/✗ per check with remediation hints.
Exit code 0 = all healthy, 1 = at least one failure.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ── Helpers ──────────────────────────────────────────────────────────────────


class CheckResult(NamedTuple):
    name: str
    passed: bool
    detail: str
    hint: Optional[str] = None


def _check(name: str, fn: Callable[[], tuple[bool, str, Optional[str]]]) -> CheckResult:
    try:
        passed, detail, hint = fn()
        return CheckResult(name, passed, detail, hint)
    except Exception as exc:  # never crash the whole doctor run
        return CheckResult(name, False, f"Unexpected error: {exc}", "Run with --debug for a traceback.")


# ── Individual checks ─────────────────────────────────────────────────────────


def check_python() -> tuple[bool, str, Optional[str]]:
    """Python 3.11+ and package importability."""
    vi = sys.version_info
    version_str = f"{vi.major}.{vi.minor}.{vi.micro}"
    if vi < (3, 11):
        return (
            False,
            f"Python {version_str} found (need ≥ 3.11)",
            "Run: ./bootstrap.sh  — or install pyenv and: pyenv install 3.11",
        )

    try:
        import labctl  # noqa: F401

        pkg_ok = True
    except ImportError:
        pkg_ok = False

    if not pkg_ok:
        return (
            False,
            f"Python {version_str} OK, but 'labctl' package not importable",
            "Run: pip install -e .[dev]  inside the venv, or re-run ./bootstrap.sh",
        )

    return True, f"Python {version_str} ✓, package importable ✓", None


def check_venv(project_root: Path) -> tuple[bool, str, Optional[str]]:
    """Virtual environment exists and is the active interpreter."""
    venv_python = project_root / "venv" / "bin" / "python3"
    if not venv_python.exists():
        return (
            False,
            "venv not found at ./venv/",
            "Run: ./bootstrap.sh  to create and populate the virtualenv.",
        )

    # Check if we're running inside it
    running_inside = str(sys.executable).startswith(str(project_root / "venv"))
    status = "active ✓" if running_inside else "exists (not active)"
    return True, f"venv at ./venv/ {status}", None


def check_docker() -> tuple[bool, str, Optional[str]]:
    """Docker daemon reachable and Compose plugin present."""
    if not shutil.which("docker"):
        return (
            False,
            "docker binary not found in PATH",
            "macOS: install Docker Desktop — https://www.docker.com/products/docker-desktop/\n"
            "Linux: curl -fsSL https://get.docker.com | sudo sh",
        )

    # Daemon running?
    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return (
            False,
            "Docker daemon not running (docker info failed)",
            "Start Docker Desktop, or run: sudo systemctl start docker",
        )

    # Compose plugin?
    compose_result = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if compose_result.returncode != 0:
        return (
            False,
            "Docker is running but 'docker compose' plugin not found",
            "Update Docker Desktop, or: sudo apt install docker-compose-plugin",
        )

    compose_ver = compose_result.stdout.strip().split()[-1] if compose_result.stdout else "?"
    docker_ver_result = subprocess.run(
        ["docker", "--version"], capture_output=True, text=True
    )
    docker_ver = docker_ver_result.stdout.strip() if docker_ver_result.returncode == 0 else "?"
    return True, f"{docker_ver}, Compose {compose_ver}", None


def check_env_file(project_root: Path) -> tuple[bool, str, Optional[str]]:
    """.env exists."""
    env_path = project_root / ".env"
    if not env_path.exists():
        template = project_root / ".env.template"
        hint = (
            "Run: ./bootstrap.sh  — it will generate .env from .env.template"
            if template.exists()
            else "Create a .env file (see .env.template for the required variables)."
        )
        return False, ".env file not found", hint

    # Count non-comment, non-empty lines
    lines = [
        line
        for line in env_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return True, f".env found ({len(lines)} variable(s) set)", None


def check_env_required_vars(project_root: Path) -> tuple[bool, str, Optional[str]]:
    """Required env vars present in .env (no TODO placeholders)."""
    env_path = project_root / ".env"
    if not env_path.exists():
        return False, ".env missing — skipping var check", "Run ./bootstrap.sh"

    todo_vars: List[str] = []
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("# TODO"):
            # Extract the var name from "# TODO: Set VAR_NAME — ..."
            parts = stripped.split("Set ", 1)
            if len(parts) == 2:
                var_name = parts[1].split(" — ")[0].strip()
                todo_vars.append(var_name)

    if todo_vars:
        return (
            False,
            f"{len(todo_vars)} variable(s) still need manual values: {', '.join(todo_vars)}",
            "Edit .env and fill in the # TODO entries, then re-run: labctl doctor",
        )
    return True, "All .env variables have values set", None


def check_config_yaml(project_root: Path) -> tuple[bool, str, Optional[str]]:
    """config.yaml parses and references only known services."""
    config_path = project_root / "config" / "config.yaml"
    if not config_path.exists():
        return (
            False,
            "config/config.yaml not found",
            "Run: labctl init  to create your configuration.",
        )

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, f"config.yaml has YAML syntax errors: {e}", "Fix the YAML and re-run."

    if not isinstance(data, dict):
        return False, "config.yaml is empty or not a mapping", "Run: labctl init"

    # Load known service IDs from schemas directory
    schemas_dir = project_root / "config" / "services-v2"
    known_services: set[str] = set()
    if schemas_dir.exists():
        for f in schemas_dir.glob("*.yaml"):
            if f.stem != "SCHEMA":
                known_services.add(f.stem)

    services = data.get("services", {})
    unknown = [s for s in services if s not in known_services] if known_services else []
    enabled = [s for s, cfg in services.items() if isinstance(cfg, dict) and cfg.get("enabled")]

    issues = []
    if unknown:
        issues.append(f"unknown service IDs: {', '.join(unknown)}")
    detail = (
        f"config.yaml OK — {len(enabled)} service(s) enabled"
        + (f" (⚠ {'; '.join(issues)})" if issues else "")
    )
    passed = not issues
    hint = (
        f"Unknown services: {', '.join(unknown)}. Valid IDs come from config/services-v2/*.yaml"
        if unknown
        else None
    )
    return passed, detail, hint


def check_service_env_vars(project_root: Path) -> tuple[bool, str, Optional[str]]:
    """Enabled services' required env vars appear in .env."""
    config_path = project_root / "config" / "config.yaml"
    env_path = project_root / ".env"

    if not config_path.exists() or not env_path.exists():
        return True, "Skipped (config.yaml or .env missing)", None

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        with open(env_path) as f:
            env_content = f.read()
    except Exception as e:
        return False, f"Could not read files: {e}", None

    # Build set of defined env keys
    defined_keys: set[str] = set()
    for line in env_content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            defined_keys.add(stripped.split("=", 1)[0].strip())

    # Common per-service required vars (conservative list)
    SERVICE_REQUIRED_VARS: dict[str, list[str]] = {
        "postgresql": ["POSTGRES_PASSWORD"],
        "redis": ["REDIS_PASSWORD"],
        "monitoring": ["GRAFANA_ADMIN_PASSWORD"],
        "vaultwarden": ["VAULTWARDEN_ADMIN_TOKEN"],
        "traefik": ["CLOUDFLARE_TUNNEL_TOKEN"],
    }

    services = data.get("services", {})
    missing: list[str] = []
    for svc_id, cfg in services.items():
        if not (isinstance(cfg, dict) and cfg.get("enabled")):
            continue
        for var in SERVICE_REQUIRED_VARS.get(svc_id, []):
            if var not in defined_keys:
                missing.append(f"{var} (for {svc_id})")

    if missing:
        return (
            False,
            f"Missing env vars for enabled services: {', '.join(missing)}",
            "Add these to .env:\n  " + "\n  ".join(f"{m.split(' (')[0]}=<value>" for m in missing),
        )
    return True, "All required service env vars are set", None


# ── Renderer ──────────────────────────────────────────────────────────────────


def _render_results(results: List[CheckResult]) -> bool:
    """Render a Rich table of check results. Returns True if all passed."""
    table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
    table.add_column("", width=2)
    table.add_column("Check", style="bold white", min_width=30)
    table.add_column("Detail", style="dim")

    all_passed = True
    failed_hints: list[tuple[str, str]] = []

    for r in results:
        icon = "[green]✓[/green]" if r.passed else "[red]✗[/red]"
        name_style = r.name if r.passed else f"[red]{r.name}[/red]"
        table.add_row(icon, name_style, r.detail)
        if not r.passed:
            all_passed = False
            if r.hint:
                failed_hints.append((r.name, r.hint))

    console.print()
    console.print(table)
    console.print()

    if failed_hints:
        console.print("[bold red]Remediation hints:[/bold red]")
        for name, hint in failed_hints:
            console.print(f"\n  [red]▶ {name}[/red]")
            for line in hint.splitlines():
                console.print(f"    {line}")
        console.print()

    return all_passed


# ── Public entry point ────────────────────────────────────────────────────────


def run(project_root: Optional[str] = None) -> None:
    """
    Run all health checks and print results.

    Args:
        project_root: Path to the repository root. Defaults to CWD.

    Raises:
        SystemExit(1) if any check fails.
    """
    root = Path(project_root) if project_root else Path.cwd()

    console.print(
        Panel.fit(
            "🩺 [bold blue]labctl doctor[/bold blue] — Post-install health check",
            border_style="blue",
        )
    )

    results: List[CheckResult] = [
        _check("Python 3.11+", check_python),
        _check("Virtual environment", lambda: check_venv(root)),
        _check("Docker + Compose", check_docker),
        _check(".env file", lambda: check_env_file(root)),
        _check(".env required vars", lambda: check_env_required_vars(root)),
        _check("config.yaml", lambda: check_config_yaml(root)),
        _check("Service env vars", lambda: check_service_env_vars(root)),
    ]

    all_passed = _render_results(results)

    passed_count = sum(1 for r in results if r.passed)
    total = len(results)
    colour = "green" if all_passed else "red"
    console.print(
        f"[{colour}]{passed_count}/{total} checks passed[/{colour}]"
        + ("  🎉" if all_passed else "  — fix the issues above and re-run: labctl doctor")
    )
    console.print()

    if not all_passed:
        raise SystemExit(1)
