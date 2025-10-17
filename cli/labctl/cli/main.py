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
) -> None:
    """
    🚀 Initialize new home lab configuration
    
    Creates a new configuration file with guided setup wizard.
    """
    try:
        init_cmd.run(
            config_file=config_file,
            interactive=interactive,
            force=force,
        )
    except HomeLabError as e:
        console.print(f"[red]Error:[/red] {e.message}", err=True)
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
        help="Enable strict validation",
    ),
) -> None:
    """
    ✅ Validate configuration and requirements
    
    Checks configuration syntax, schema compliance, and system requirements.
    """
    try:
        validate_cmd.run(config_file=config_file, strict=strict)
    except HomeLabError as e:
        console.print(f"[red]Validation failed:[/red] {e.message}", err=True)
        if hasattr(e, 'errors') and e.errors:
            for error in e.errors:
                console.print(f"  • [red]{error.get('path', 'unknown')}[/red]: {error.get('message', '')}")
        raise typer.Exit(1)


@app.command("build")
def build_command(
    config_file: str = config_file_option,
) -> None:
    """
    🔨 Build Docker Compose configurations
    
    Generate Docker Compose files from configuration.
    """
    console.print("[yellow]Build command not yet implemented[/yellow]")


@app.command("deploy") 
def deploy_command(
    config_file: str = config_file_option,
) -> None:
    """
    🚀 Deploy home lab services
    
    Deploy services using Docker Compose with health checking.
    """
    console.print("[yellow]Deploy command not yet implemented[/yellow]")


@app.command("status")
def status_command(
    config_file: str = config_file_option,
) -> None:
    """
    📊 Show service status and health
    
    Displays current status of all services.
    """
    console.print("[yellow]Status command not yet implemented[/yellow]")


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
        console.print(f"[red]Error [{exc_value.code}]:[/red] {exc_value.message}", err=True)
        
        if exc_value.details:
            console.print("[dim]Details:[/dim]", err=True)
            for key, value in exc_value.details.items():
                console.print(f"  {key}: {value}", err=True)
        return
    
    # For unexpected exceptions, show more detail in debug mode
    if os.getenv("LABCTL_DEBUG"):
        import traceback
        console.print("[red]Unexpected error occurred:[/red]", err=True)
        console.print(traceback.format_exception(exc_type, exc_value, exc_traceback), err=True)
    else:
        console.print(f"[red]Unexpected error:[/red] {exc_value}", err=True)
        console.print("[dim]Run with --debug for more details[/dim]", err=True)


# Set global exception handler
sys.excepthook = handle_exception


if __name__ == "__main__":
    app()