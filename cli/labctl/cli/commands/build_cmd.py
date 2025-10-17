"""
Build command - generates Docker Compose configurations
"""

import yaml
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress

from ...core.config import Config
from ...core.exceptions import HomeLabError
from ...compose.composer import ComposeComposer

console = Console()


def run(
    config_file: str,
    services: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    force: bool = False
) -> None:
    """Build Docker Compose files from configuration"""
    
    console.print("🔨 Building Docker Compose configurations...")
    
    config_path = Path(config_file)
    if not config_path.exists():
        raise HomeLabError(f"Configuration file not found: {config_file}")
    
    # Load configuration
    config = Config.load_from_file(config_path)
    
    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = config_path.parent / "compose"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize composer
    composer = ComposeComposer(config)
    
    try:
        with Progress() as progress:
            task = progress.add_task("Generating compose files...", total=100)
            
            # Build core services
            progress.update(task, description="Building core services...")
            core_compose = composer.build_core_services()
            progress.update(task, advance=25)
            
            # Build optional services
            progress.update(task, description="Building optional services...")
            optional_services = composer.build_optional_services(services)
            progress.update(task, advance=25)
            
            # Build monitoring if enabled
            if config.monitoring.enabled:
                progress.update(task, description="Building monitoring stack...")
                monitoring_compose = composer.build_monitoring()
            else:
                monitoring_compose = None
            progress.update(task, advance=25)
            
            # Build security services if enabled
            if config.security.enabled:
                progress.update(task, description="Building security services...")
                security_compose = composer.build_security()
            else:
                security_compose = None
            progress.update(task, advance=15)
            
            # Write compose files
            progress.update(task, description="Writing compose files...")
            _write_compose_files(
                output_path,
                core_compose,
                optional_services,
                monitoring_compose,
                security_compose,
                force
            )
            progress.update(task, advance=10)
            
        console.print(f"\n[green]✅ Compose files built successfully in {output_path}[/green]")
        _show_next_steps(config, output_path)
        
    except Exception as e:
        raise HomeLabError(f"Build failed: {str(e)}")


def _write_compose_files(
    output_path: Path,
    core_compose: dict,
    optional_services: dict,
    monitoring_compose: Optional[dict],
    security_compose: Optional[dict],
    force: bool
) -> None:
    """Write compose files to output directory"""
    
    # Main docker-compose.yml (core services)
    main_file = output_path / "docker-compose.yml"
    if main_file.exists() and not force:
        raise HomeLabError(f"File exists: {main_file}. Use --force to overwrite")
    
    with open(main_file, 'w') as f:
        yaml.dump(core_compose, f, default_flow_style=False, indent=2, sort_keys=False)
    
    console.print(f"[dim]✓ Created {main_file.name}[/dim]")
    
    # Optional services
    if optional_services and optional_services.get("services"):
        optional_file = output_path / "docker-compose.optional.yml"
        with open(optional_file, 'w') as f:
            yaml.dump(optional_services, f, default_flow_style=False, indent=2, sort_keys=False)
        console.print(f"[dim]✓ Created {optional_file.name}[/dim]")
    
    # Monitoring
    if monitoring_compose and monitoring_compose.get("services"):
        monitoring_file = output_path / "docker-compose.monitoring.yml"
        with open(monitoring_file, 'w') as f:
            yaml.dump(monitoring_compose, f, default_flow_style=False, indent=2, sort_keys=False)
        console.print(f"[dim]✓ Created {monitoring_file.name}[/dim]")
    
    # Security
    if security_compose and security_compose.get("services"):
        security_file = output_path / "docker-compose.security.yml"
        with open(security_file, 'w') as f:
            yaml.dump(security_compose, f, default_flow_style=False, indent=2, sort_keys=False)
        console.print(f"[dim]✓ Created {security_file.name}[/dim]")


def _show_next_steps(config: Config, output_path: Path) -> None:
    """Show next steps after build"""
    
    console.print("\n[bold]🎯 Next Steps:[/bold]")
    console.print(f"  1. Review generated files in [cyan]{output_path}[/cyan]")
    console.print(f"  2. Deploy with: [cyan]labctl deploy[/cyan]")
    console.print(f"  3. Check status: [cyan]labctl status[/cyan]")
    
    # Show service URLs that will be available
    console.print(f"\n[bold]🌐 Services (after deployment):[/bold]")
    urls = config.get_service_urls()
    for service, url in urls.items():
        if (service == "gitlab" and config.gitlab.enabled) or \
           (service == "vault" and config.vault.enabled) or \
           (service in ["prometheus", "grafana"] and config.monitoring.enabled) or \
           service == "traefik":
            console.print(f"  • {service.title()}: {url}")
    
    console.print(f"\n[dim]💡 Deploy all services: docker compose -f {output_path}/docker-compose.yml up -d[/dim]")