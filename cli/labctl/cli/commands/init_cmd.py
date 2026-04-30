"""
Init command — interactive home lab setup wizard (Phase 2).

Changes vs legacy:
  • Category-by-category service selection (not raw ID list)
  • Dual-write: secrets → .env,  non-secrets → config.yaml
  • --service <id>  to reconfigure just one service
  • --non-interactive / --profile for CI/scripted use
  • Idempotent: existing values loaded as defaults, Enter keeps them
"""

from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ...core.config_writer import save_config_to_yaml
from ...core.exceptions import HomeLabError
from ...core.services.schema import load_service_schemas
from ..wizard.orchestrator import WizardOrchestrator

console = Console()

# ── Public entry point ────────────────────────────────────────────────────────


def run(
    config_file: str,
    interactive: bool = True,
    force: bool = False,
    profile: Optional[str] = None,
    non_interactive: bool = False,
    service: Optional[str] = None,         # --service <id> — reconfigure one service
) -> None:
    """Initialize or reconfigure the home lab configuration."""

    config_path = Path(config_file)
    # .env sits next to config.yaml
    env_path = config_path.parent.parent / ".env"

    # ── Load existing config (used as defaults on re-run) ──────────────────
    existing_config: dict = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                existing_config = yaml.safe_load(f) or {}
        except Exception:
            pass

    # ── Handle already-existing config ────────────────────────────────────
    if config_path.exists() and not force and not service:
        console.print(f"[green]✓ Configuration already exists at {config_file}[/green]")

        if non_interactive or not interactive:
            console.print(
                "[dim]Skipping init (use --force to overwrite,"
                " --service to reconfigure one service)[/dim]"
            )
            _show_next_steps(existing_config)
            return

        action = Prompt.ask(
            "Config exists — what would you like to do?",
            choices=["skip", "reconfigure", "overwrite"],
            default="skip",
        )
        if action == "skip":
            _show_next_steps(existing_config)
            return
        elif action == "reconfigure":
            console.print("[blue]Starting reconfiguration with existing values as defaults…[/blue]")
            # fall through to wizard with existing_config
        else:  # overwrite
            if not Confirm.ask("⚠  Overwrite existing configuration?"):
                console.print("[yellow]Cancelled[/yellow]")
                return
            existing_config = {}

    # ── Load service schemas ───────────────────────────────────────────────
    # Schema dir is always relative to this file's project root
    project_root = config_path.parent.parent
    schemas_dir = project_root / "config" / "services-v2"
    try:
        service_schemas = load_service_schemas(str(schemas_dir))
    except Exception as exc:
        raise HomeLabError(f"Cannot load service schemas from {schemas_dir}: {exc}")

    orchestrator = WizardOrchestrator(service_schemas)

    # ── Run wizard ─────────────────────────────────────────────────────────
    try:
        if service:
            # Single-service reconfigure
            if service not in service_schemas:
                known = ", ".join(sorted(service_schemas.keys()))
                raise HomeLabError(f"Unknown service '{service}'. Known services: {known}")
            console.print(f"\n[bold blue]⚙  Reconfiguring {service_schemas[service].name} only[/bold blue]")
            svc_cfg, svc_env = orchestrator.run_single_service(
                service_id=service,
                existing_config=existing_config,
                profile=profile or existing_config.get("profile", "prod"),
            )
            existing_config.setdefault("services", {})[service] = svc_cfg
            existing_config.setdefault("env_vars", {}).update(svc_env)
            config_data = existing_config
        else:
            config_data = orchestrator.run_wizard(
                profile=profile,
                existing_config=existing_config,
                non_interactive=non_interactive,
            )
    except KeyboardInterrupt:
        console.print("\n[yellow]Wizard cancelled[/yellow]")
        return
    except ValueError as exc:
        # Wizard-internal cancellations (not confirmed, no services selected, etc.)
        console.print(f"[yellow]{exc}[/yellow]")
        return

    # ── Write outputs ──────────────────────────────────────────────────────
    try:
        # Strip env_vars from config before writing config.yaml
        env_vars = config_data.pop("env_vars", {})

        save_config_to_yaml(config_data, config_path)
        console.print(f"\n[green]✅ Configuration saved → {config_file}[/green]")

        if env_vars:
            _merge_env_file(env_path, env_vars)
            console.print(f"[green]✅ Secrets merged   → {env_path}[/green]")
        elif not env_path.exists():
            console.print(f"[dim]ℹ  No secrets to write — .env unchanged[/dim]")

    except Exception as exc:
        raise HomeLabError(f"Failed to save configuration: {exc}")

    # ── Create directory structure ─────────────────────────────────────────
    _create_directories(config_path.parent)

    # ── Next steps ─────────────────────────────────────────────────────────
    _show_next_steps(config_data)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _merge_env_file(env_path: Path, new_vars: dict) -> None:
    """
    Merge new_vars into .env.
    - Existing keys are NOT overwritten (preserves hand-edited values).
    - New keys are appended.
    """
    existing_keys: dict = {}
    lines: list[str] = []

    if env_path.exists():
        for line in env_path.read_text().splitlines():
            lines.append(line)
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                existing_keys[k] = True

    added = 0
    for key, value in new_vars.items():
        if key not in existing_keys:
            if added == 0:
                lines.append("\n# Added by labctl init")
            lines.append(f"{key}={value}")
            added += 1

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines) + "\n")


def _create_directories(base_path: Path) -> None:
    for d in ["compose", "data", "logs", "backups", "config/secrets", "ssl"]:
        (base_path / d).mkdir(parents=True, exist_ok=True)
    console.print(f"[green]📁 Directory structure ready in {base_path}[/green]")


def _show_next_steps(config: dict) -> None:
    domain = config.get("core", {}).get("domain", "homelab.local")
    services = config.get("services", {})
    enabled = [s for s, c in services.items() if isinstance(c, dict) and c.get("enabled")]
    disabled_count = len(services) - len(enabled)

    console.print("\n[bold]🎯 Next Steps[/bold]")
    table = Table(show_header=False, show_lines=False, box=None)
    table.add_column("", style="cyan", width=3)
    table.add_column("", style="white")
    table.add_row("1.", "Validate:   [cyan]labctl validate[/cyan]")
    table.add_row("2.", "Build:      [cyan]labctl build[/cyan]")
    table.add_row("3.", "Deploy:     [cyan]labctl deploy[/cyan]")
    table.add_row("4.", "Health:     [cyan]labctl doctor[/cyan]")
    console.print(table)

    if enabled:
        console.print(f"\n[bold]Enabled ({len(enabled)}):[/bold] {', '.join(enabled)}")
    if disabled_count:
        console.print(f"[dim]Disabled: {disabled_count} other service(s)[/dim]")

    # Service URLs
    urls = {
        s: f"https://{s}.{domain}"
        for s in enabled
        if s not in ("postgresql", "redis", "mongodb")
    }
    if urls:
        console.print("\n[bold]🌐 Service URLs (after deploy):[/bold]")
        for svc, url in list(urls.items())[:6]:
            console.print(f"  • {svc}: {url}")

    console.print(f"\n[dim]Profile: {config.get('profile', 'prod')} | Re-run: labctl init --service <id>[/dim]")
