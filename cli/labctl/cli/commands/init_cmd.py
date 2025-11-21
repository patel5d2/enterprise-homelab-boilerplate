"""
Init command - interactive setup wizard
"""

from pathlib import Path
from typing import Dict, Optional

import yaml
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ...core.config import Config
from ...core.config_writer import save_config_to_yaml
from ...core.exceptions import HomeLabError
from ...core.secrets import load_or_create_env
from ...core.services.deps import resolve_with_dependencies
from ...core.services.schema import load_service_schemas
from ..wizard.orchestrator import WizardOrchestrator

console = Console()


def run(
    config_file: str,
    interactive: bool = True,
    force: bool = False,
    profile: Optional[str] = None,
    non_interactive: bool = False,
) -> None:
    """Initialize new home lab configuration"""

    config_path = Path(config_file)

    # Check if config already exists
    if config_path.exists() and not force:
        if not Confirm.ask(
            f"Configuration file {config_file} already exists. Overwrite?"
        ):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return

    # Check for legacy config and offer migration
    if config_path.exists() and not non_interactive:
        try:
            with open(config_path, "r") as f:
                existing_config = yaml.safe_load(f)
            if existing_config and not existing_config.get("version"):
                console.print("[yellow]⚠️  Legacy configuration detected[/yellow]")
                if Confirm.ask(
                    "Would you like to migrate to the new configuration format?"
                ):
                    console.print(
                        "[blue]Migration feature will be available soon. Please backup your config and create a new one.[/blue]"
                    )
                    return
        except Exception:
            pass  # Ignore errors reading existing config

    console.print(
        Panel.fit(
            "🏠 [bold blue]Home Lab Setup Wizard v2.0[/bold blue] 🏠\n\n"
            "Welcome to the new Enterprise Home Lab setup wizard!\n"
            "This will guide you through configuring your infrastructure\n"
            "with service-specific settings and dependency management.",
            border_style="blue",
        )
    )

    try:
        # Load service schemas
        schemas_path = config_path.parent.parent / "config" / "services-v2"
        service_schemas = load_service_schemas(str(schemas_path))

        if interactive and not non_interactive:
            # Run the new wizard
            orchestrator = WizardOrchestrator(service_schemas)
            config_data = orchestrator.run_wizard(profile=profile)
        else:
            config_data = _default_setup_v2(profile or "prod")

        # Save configuration and environment variables
        save_config_to_yaml(config_data, config_path)

        # Create .env file with secrets
        env_path = config_path.parent / ".env"
        env_vars = config_data.get("env_vars", {})
        if env_vars:
            load_or_create_env(str(env_path), env_vars)

        console.print(f"\n[green]✅ Configuration saved to {config_file}[/green]")
        if env_vars:
            console.print(
                f"[green]✅ Environment variables saved to {env_path}[/green]"
            )

        # Create directory structure
        _create_directories(config_path.parent)

        # Show next steps
        _show_next_steps_v2(config_data)

    except Exception as e:
        raise HomeLabError(f"Failed to save configuration: {str(e)}")


def _default_setup_v2(profile: str = "prod") -> dict:
    """Default configuration setup using new schema format"""

    console.print(f"[yellow]Creating default {profile} configuration...[/yellow]")

    return {
        "version": 2,
        "profile": profile,
        "core": {"domain": "homelab.local", "email": "admin@homelab.local"},
        "services": {
            "traefik": {
                "enabled": True,
                "domain": "homelab.local",
                "email": "admin@homelab.local",
                "acme_environment": "staging" if profile == "dev" else "production",
            },
            "postgresql": {"enabled": True, "port": 5432, "superuser": "postgres"},
            "redis": {"enabled": True, "port": 6379, "persistence": "rdb"},
            "monitoring": {
                "enabled": True,
                "prometheus_retention": "15d" if profile == "dev" else "30d",
                "external_port": 9090,
            },
        },
        "custom_env": {},
        "env_vars": {
            "POSTGRES_PASSWORD": "$(generate_password)",
            "REDIS_PASSWORD": "$(generate_password)",
            "GRAFANA_ADMIN_PASSWORD": "$(generate_password)",
        },
    }


def _create_directories(base_path: Path) -> None:
    """Create necessary directory structure"""

    directories = [
        "compose",
        "data",
        "logs",
        "backups",
        "config/secrets",
        "ssl",
    ]

    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]📁 Created directory structure in {base_path}[/green]")


def _show_next_steps_v2(config: dict) -> None:
    """Show next steps after initialization using new config format"""

    console.print("\n[bold]🎯 Next Steps:[/bold]")

    table = Table(show_header=False, show_lines=True)
    table.add_column("Step", style="cyan", width=4)
    table.add_column("Action", style="white")

    table.add_row("1", "Validate configuration: [cyan]labctl validate[/cyan]")
    table.add_row("2", "Build compose files: [cyan]labctl build[/cyan]")
    table.add_row("3", "Deploy infrastructure: [cyan]labctl deploy[/cyan]")
    table.add_row("4", "Check status: [cyan]labctl status[/cyan]")

    console.print(table)

    # Service URLs based on new config format
    console.print(f"\n[bold]🌐 Service URLs (after deployment):[/bold]")
    domain = config.get("core", {}).get("domain", "homelab.local")
    services = config.get("services", {})

    base_urls = {}

    # Always show Traefik if enabled
    if services.get("traefik", {}).get("enabled"):
        base_urls["traefik"] = f"https://traefik.{domain}"

    # Add URLs for enabled services
    if services.get("monitoring", {}).get("enabled"):
        base_urls["grafana"] = f"https://grafana.{domain}"
        base_urls["prometheus"] = f"https://prometheus.{domain}"

    if services.get("vaultwarden", {}).get("enabled"):
        base_urls["vaultwarden"] = f"https://vault.{domain}"

    if services.get("nextcloud", {}).get("enabled"):
        base_urls["nextcloud"] = f"https://nextcloud.{domain}"

    if services.get("pihole", {}).get("enabled"):
        base_urls["pihole"] = f"https://pihole.{domain}"

    if services.get("gitlab", {}).get("enabled"):
        base_urls["gitlab"] = f"https://gitlab.{domain}"

    for service, url in base_urls.items():
        console.print(f"  • {service.title()}: {url}")

    # Show profile info
    profile = config.get("profile", "prod")
    console.print(f"\n[dim]📋 Configuration profile: {profile}[/dim]")
    console.print(
        f"[dim]💡 Edit configuration anytime with: labctl config --edit[/dim]"
    )
