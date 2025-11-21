"""
Build command - generates Docker Compose configurations
"""

import time
from pathlib import Path
from typing import List, Optional

import yaml
from rich.console import Console
from rich.progress import Progress

from ...core.compose import ComposeGenerator
from ...core.config import Config, LabConfig
from ...core.exceptions import HomeLabError

console = Console()


def run(
    config_file: str,
    services: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    force: bool = False,
) -> None:
    """Build Docker Compose files from configuration"""

    console.print("🔨 Building Docker Compose configurations...")

    config_path = Path(config_file)
    if not config_path.exists():
        raise HomeLabError(f"Configuration file not found: {config_file}")

    # Load configuration (detect version and use appropriate loader)
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    config_version = config_data.get("version", 1)

    if config_version == 2:
        config = LabConfig.load_from_file(config_path)
        console.print(f"[dim]✓ Loaded v{config_version} configuration[/dim]")
    else:
        config = Config.load_from_file(config_path)
        console.print(f"[dim]✓ Loaded v{config_version} (legacy) configuration[/dim]")

    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = config_path.parent / "compose"

    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize generator
    generator = ComposeGenerator(config)

    try:
        with Progress() as progress:
            task = progress.add_task("Generating compose files...", total=100)

            # Generate Docker Compose configuration
            progress.update(
                task, description="Generating Docker Compose configuration..."
            )
            compose_file = output_path / "docker-compose.yml"
            env_file = output_path / ".env.template"

            # Check if files exist and handle gracefully
            if compose_file.exists() and not force:
                backup = compose_file.with_name(
                    f"{compose_file.stem}.bak.{int(time.time())}{compose_file.suffix}"
                )
                compose_file.rename(backup)
                console.print(
                    f"[yellow]✓ Existing Compose file backed up to {backup.name}[/yellow]"
                )

            # Generate and save compose file
            generator.save_compose_file(compose_file)
            progress.update(task, advance=80)

            # Generate and save environment template
            generator.save_env_template(env_file)
            progress.update(task, advance=20)

        console.print(
            f"\n[green]✅ Docker Compose configuration built successfully![/green]"
        )
        console.print(f"[dim]✓ Created {compose_file.name}[/dim]")
        console.print(f"[dim]✓ Created {env_file.name}[/dim]")
        _show_next_steps(config, output_path)

    except Exception as e:
        raise HomeLabError(f"Build failed: {str(e)}")


def _show_next_steps(config, output_path: Path) -> None:
    """Show next steps after build"""

    console.print("\n[bold]🎯 Next Steps:[/bold]")
    console.print(f"  1. Review generated files in [cyan]{output_path}[/cyan]")
    console.print(f"  2. Update environment variables in [cyan].env.template[/cyan]")
    console.print(f"  3. Deploy with: [cyan]labctl deploy[/cyan]")
    console.print(f"  4. Check status: [cyan]labctl status[/cyan]")

    # Show service URLs that will be available
    console.print(f"\n[bold]🌐 Services (after deployment):[/bold]")

    # Handle both v1 and v2 configs
    try:
        if hasattr(config, "get_service_urls"):
            urls = config.get_service_urls()
            for service, url in urls.items():
                console.print(f"  • {service.title()}: {url}")
        else:
            # Fallback for configs without get_service_urls method
            domain = getattr(config.core, "domain", "homelab.local")
            if isinstance(config, LabConfig):
                enabled_services = config.get_enabled_services()
                for service_id in enabled_services.keys():
                    console.print(
                        f"  • {service_id.title()}: https://{service_id}.{domain}"
                    )
    except Exception as e:
        console.print(f"  [dim]Service URLs will be available after deployment[/dim]")

    console.print(
        f"\n[dim]💡 Deploy all services: docker compose -f {output_path}/docker-compose.yml up -d[/dim]"
    )
