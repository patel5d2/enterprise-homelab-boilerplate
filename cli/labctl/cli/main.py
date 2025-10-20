"""
Home Lab CLI - Main application entry point
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from ..core.config import Config
from ..core.exceptions import HomeLabError
from .commands import (
    init_cmd,
    validate_cmd,
    build_cmd,
    deploy_cmd,
    status_cmd,
    logs_cmd,
    stop_cmd,
    config_cmd,
    migrate_cmd,
)

# Initialize Typer app
app = typer.Typer(
    name="labctl",
    help="🏠 Enterprise Home Lab Infrastructure Management CLI",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Initialize Rich console
console = Console()

# Global options
config_file_option = typer.Option(
    "config/config.yaml",
    "--config",
    "-c",
    help="Path to configuration file",
    show_default=True,
)

verbose_option = typer.Option(
    False,
    "--verbose",
    "-v", 
    help="Enable verbose output",
)

debug_option = typer.Option(
    False,
    "--debug",
    help="Enable debug output",
)


def version_callback(value: bool) -> None:
    """Show version information"""
    if value:
        from .. import __version__, __description__
        rprint(f"[bold blue]labctl[/bold blue] v{__version__}")
        rprint(f"[dim]{__description__}[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = verbose_option,
    debug: bool = debug_option,
) -> None:
    """
    🏠 Enterprise Home Lab Infrastructure Management CLI
    
    A comprehensive tool for managing your self-hosted infrastructure with
    Docker Compose, featuring GitLab, monitoring, security, and more.
    """
    if verbose:
        os.environ["LABCTL_VERBOSE"] = "1"
    if debug:
        os.environ["LABCTL_DEBUG"] = "1"


@app.command("init")
def init_command(
    config_file: str = config_file_option,
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Run interactive setup wizard",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing configuration",
    ),
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        help="Configuration profile (dev or prod)",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Skip all prompts and use defaults",
    ),
) -> None:
    """
    🚀 Initialize new home lab configuration
    
    Creates a new configuration file with guided setup wizard.
    Uses the new service-specific configuration system with dependency management.
    """
    try:
        init_cmd.run(
            config_file=config_file,
            interactive=interactive,
            force=force,
            profile=profile,
            non_interactive=non_interactive,
        )
    except HomeLabError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        raise typer.Exit(130)


@app.command("validate")
def validate_command(
    config_file: str = config_file_option,
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Enable strict validation (warnings become errors)",
    ),
    preflight: bool = typer.Option(
        False,
        "--preflight",
        help="Run preflight system checks (Docker, networking, etc.)",
    ),
) -> None:
    """
    ✅ Validate configuration and requirements
    
    Checks configuration syntax, schema compliance, service dependencies, and optionally
    runs preflight system checks to ensure Docker and networking requirements are met.
    """
    try:
        validate_cmd.run(config_file=config_file, strict=strict, preflight=preflight)
    except HomeLabError as e:
        console.print(f"[red]Validation failed:[/red] {e.message}")
        if hasattr(e, 'errors') and e.errors:
            for error in e.errors:
                console.print(f"  • [red]{error.get('path', 'unknown')}[/red]: {error.get('message', '')}")
        raise typer.Exit(1)


@app.command("build")
def build_command(
    config_file: str = config_file_option,
    services: Optional[str] = typer.Option(
        None,
        "--services",
        help="Comma-separated list of services to build",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for compose files",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files",
    ),
) -> None:
    """
    🔨 Build Docker Compose configurations
    
    Generate Docker Compose files from configuration.
    """
    try:
        service_list = services.split(',') if services else None
        build_cmd.run(
            config_file=config_file,
            services=service_list,
            output_dir=output,
            force=force,
        )
    except HomeLabError as e:
        console.print(f"[red]Build failed:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("deploy") 
def deploy_command(
    config_file: str = config_file_option,
    services: Optional[str] = typer.Option(
        None,
        "--services",
        help="Comma-separated list of services to deploy",
    ),
    compose_dir: Optional[str] = typer.Option(
        None,
        "--compose-dir",
        help="Directory containing compose files",
    ),
    build: bool = typer.Option(
        False,
        "--build",
        help="Build compose files before deployment",
    ),
    wait: bool = typer.Option(
        True,
        "--wait/--no-wait",
        help="Wait for services to be healthy",
    ),
    timeout: int = typer.Option(
        300,
        "--timeout",
        help="Timeout for waiting (seconds)",
    ),
) -> None:
    """
    🚀 Deploy home lab services
    
    Deploy services using Docker Compose with health checking.
    """
    try:
        service_list = services.split(',') if services else None
        deploy_cmd.run(
            config_file=config_file,
            services=service_list,
            compose_dir=compose_dir,
            build=build,
            wait=wait,
            timeout=timeout,
        )
    except HomeLabError as e:
        console.print(f"[red]Deployment failed:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("status")
def status_command(
    config_file: str = config_file_option,
    services: Optional[str] = typer.Option(
        None,
        "--services",
        help="Comma-separated list of services to check",
    ),
    compose_dir: Optional[str] = typer.Option(
        None,
        "--compose-dir",
        help="Directory containing compose files",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch status continuously (not yet implemented)",
    ),
) -> None:
    """
    📊 Show service status and health
    
    Displays current status of all services or specific services.
    """
    try:
        service_list = services.split(',') if services else None
        status_cmd.run(
            config_file=config_file,
            services=service_list,
            compose_dir=compose_dir,
            watch=watch,
        )
    except HomeLabError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("logs")
def logs_command(
    config_file: str = config_file_option,
    services: Optional[str] = typer.Option(
        None,
        "--services",
        help="Comma-separated list of services to show logs for",
    ),
    compose_dir: Optional[str] = typer.Option(
        None,
        "--compose-dir",
        help="Directory containing compose files",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Follow log output",
    ),
    tail: int = typer.Option(
        100,
        "--tail",
        help="Number of lines to show",
    ),
) -> None:
    """
    📋 Show service logs
    
    Display logs from services with filtering and follow options.
    """
    try:
        service_list = services.split(',') if services else None
        logs_cmd.run(
            config_file=config_file,
            services=service_list,
            compose_dir=compose_dir,
            follow=follow,
            tail=tail,
        )
    except HomeLabError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("stop")
def stop_command(
    config_file: str = config_file_option,
    services: Optional[str] = typer.Option(
        None,
        "--services",
        help="Comma-separated list of services to stop",
    ),
    compose_dir: Optional[str] = typer.Option(
        None,
        "--compose-dir",
        help="Directory containing compose files",
    ),
    volumes: bool = typer.Option(
        False,
        "--volumes",
        help="Remove volumes as well",
    ),
    images: bool = typer.Option(
        False,
        "--images",
        help="Remove unused images after stopping",
    ),
) -> None:
    """
    🛑 Stop services and cleanup resources
    
    Stop running services and optionally cleanup volumes and images.
    """
    try:
        service_list = services.split(',') if services else None
        stop_cmd.run(
            config_file=config_file,
            services=service_list,
            compose_dir=compose_dir,
            remove_volumes=volumes,
            remove_images=images,
        )
    except HomeLabError as e:
        console.print(f"[red]Stop failed:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("config")
def config_command(
    config_file: str = config_file_option,
    show: bool = typer.Option(
        False,
        "--show",
        help="Show configuration content",
    ),
    edit: bool = typer.Option(
        False,
        "--edit",
        help="Open configuration in editor",
    ),
    key: Optional[str] = typer.Option(
        None,
        "--key",
        help="Show specific configuration key",
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        help="Output format (yaml, json)",
    ),
) -> None:
    """
    ⚙️ Manage configuration files
    
    View, edit, and manage configuration files.
    """
    try:
        config_cmd.run(
            config_file=config_file,
            show=show,
            edit=edit,
            key=key,
            format=format,
        )
    except HomeLabError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("migrate")
def migrate_command(
    input_file: str = typer.Argument(..., help="Input configuration file to migrate"),
    output_file: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for migrated configuration"
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create backup of original file"
    ),
    preview: bool = typer.Option(
        True,
        "--preview/--no-preview",
        help="Show migration preview before applying"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompts"
    ),
) -> None:
    """
    📋 Migrate legacy configuration to v2 format
    
    Convert existing configuration files to the new v2 format with 
    service-specific settings and enhanced structure.
    """
    try:
        migrate_cmd.run(
            input_file=input_file,
            output_file=output_file,
            backup=backup,
            preview=preview,
            force=force
        )
    except HomeLabError as e:
        console.print(f"[red]Migration failed:[/red] {e.message}")
        raise typer.Exit(1)


@app.command("version")
def version_command() -> None:
    """
    📋 Show detailed version information
    
    Displays version, build info, and system details.
    """
    from .. import __version__, __description__
    
    panel = Panel(
        f"[bold blue]labctl[/bold blue] v{__version__}\n"
        f"[dim]{__description__}[/dim]\n\n"
        f"Python: {sys.version.split()[0]}\n"
        f"Platform: {sys.platform}",
        title="Version Information",
        border_style="blue",
    )
    
    console.print(panel)


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler for better error reporting"""
    if issubclass(exc_type, KeyboardInterrupt):
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return
    
    if isinstance(exc_value, HomeLabError):
        console.print(f"[red]Error [{exc_value.code}]:[/red] {exc_value.message}")
        
        if exc_value.details:
            console.print("[dim]Details:[/dim]")
            for key, value in exc_value.details.items():
                console.print(f"  {key}: {value}")
        return
    
    # For unexpected exceptions, show more detail in debug mode
    if os.getenv("LABCTL_DEBUG"):
        import traceback
        console.print("[red]Unexpected error occurred:[/red]")
        console.print(traceback.format_exception(exc_type, exc_value, exc_traceback))
    else:
        console.print(f"[red]Unexpected error:[/red] {exc_value}")
        console.print("[dim]Run with --debug for more details[/dim]")


# Set global exception handler
sys.excepthook = handle_exception


if __name__ == "__main__":
    app()