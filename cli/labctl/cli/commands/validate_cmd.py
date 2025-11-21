"""
Validate command - configuration and system validation
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...core.config import Config, LabConfig
from ...core.config_writer import load_config_from_yaml
from ...core.exceptions import HomeLabError
from ...core.validation import run_preflight_checks, validate_configuration

console = Console()


def run(config_file: str, strict: bool = False, preflight: bool = False) -> None:
    """Validate configuration and system requirements"""

    console.print(
        Panel.fit(
            "🔍 [bold blue]Configuration Validation[/bold blue] 🔍\n"
            "Checking configuration syntax, values, and system requirements...",
            border_style="blue",
        )
    )

    config_path = Path(config_file)
    if not config_path.exists():
        raise HomeLabError(f"Configuration file not found: {config_file}")

    try:
        # Load configuration
        config_dict = load_config_from_yaml(config_path)

        # Determine configuration type and load appropriately
        if config_dict.get("version") == 2:
            # New v2 configuration
            config = LabConfig(**config_dict)
            console.print("[green]✓ Loaded v2 configuration[/green]")
        else:
            # Legacy configuration - try to load as old Config
            try:
                config = Config.load_from_file(config_path)
                console.print(
                    "[yellow]⚠️  Loaded legacy configuration (consider migrating to v2)[/yellow]"
                )

                # Run legacy validation
                warnings = config.validate_requirements()

                if warnings:
                    console.print(
                        "\n[bold yellow]Legacy Configuration Warnings:[/bold yellow]"
                    )
                    for warning in warnings:
                        console.print(f"  • {warning}")

                if warnings and strict:
                    raise HomeLabError("Strict validation failed due to warnings")

                console.print(
                    "\n[green]✅ Legacy configuration validation passed![/green]"
                )
                console.print(
                    "[dim]💡 Use 'labctl migrate' to upgrade to v2 format[/dim]"
                )
                return

            except Exception as e:
                raise HomeLabError(f"Failed to load configuration: {e}")

        # Run comprehensive validation for v2 configs
        if isinstance(config, LabConfig):
            errors, warnings = validate_configuration(config, show_results=True)

            # Check validation results
            if errors:
                error_count = len(errors)
                console.print(
                    f"\n[red]❌ Validation failed with {error_count} error(s)[/red]"
                )
                if strict:
                    raise HomeLabError("Configuration validation failed")
            elif warnings and strict:
                console.print(
                    f"\n[red]❌ Strict validation failed with {len(warnings)} warning(s)[/red]"
                )
                raise HomeLabError("Strict validation failed due to warnings")
            elif warnings:
                console.print(
                    f"\n[yellow]⚠️  Validation completed with {len(warnings)} warning(s)[/yellow]"
                )
            else:
                console.print(
                    "\n[green]✅ Configuration validation passed perfectly![/green]"
                )

            # Run preflight checks if requested
            if preflight:
                console.print("\n" + "=" * 60)
                success = run_preflight_checks(config)
                if not success:
                    raise HomeLabError("Preflight checks failed")

            # Show configuration summary
            _show_config_summary(config)

    except Exception as e:
        if isinstance(e, HomeLabError):
            raise
        raise HomeLabError(f"Validation failed: {e}")


def _show_config_summary(config: LabConfig) -> None:
    """Show a summary of the configuration"""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]📊 Configuration Summary[/bold cyan]")
    console.print("=" * 60)

    # Basic info
    console.print(f"[bold]Version:[/bold] {config.version}")
    console.print(f"[bold]Profile:[/bold] {config.profile}")
    console.print(f"[bold]Domain:[/bold] {config.core.domain}")
    console.print(f"[bold]Email:[/bold] {config.core.email}")

    # Services summary
    enabled_services = config.get_enabled_services()
    console.print(f"\n[bold]Enabled Services ({len(enabled_services)}):[/bold]")

    if enabled_services:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Service", style="white", width=20)
        table.add_column("Status", width=10)
        table.add_column("Key Settings", style="dim")

        for service_id, service_config in enabled_services.items():
            status = "[green]✓ Enabled[/green]"

            # Get key settings for display
            key_settings = []
            if hasattr(service_config, "port") and service_config.port:
                key_settings.append(f"Port: {service_config.port}")
            if hasattr(service_config, "domain") and service_config.domain:
                key_settings.append(f"Domain: {service_config.domain}")
            if hasattr(service_config, "persistence") and service_config.persistence:
                key_settings.append(f"Persistence: {service_config.persistence}")

            settings_text = "; ".join(key_settings[:3])
            if len(key_settings) > 3:
                settings_text += f" (+{len(key_settings) - 3} more)"

            table.add_row(service_id.title(), status, settings_text)

        console.print(table)
    else:
        console.print("  [dim]No services enabled[/dim]")

    # URLs preview
    urls = config.get_service_urls()
    if urls:
        console.print(f"\n[bold]🌐 Service URLs (after deployment):[/bold]")
        for service, url in list(urls.items())[:5]:  # Show first 5
            console.print(f"  • [cyan]{url}[/cyan]")
        if len(urls) > 5:
            console.print(f"  [dim]... and {len(urls) - 5} more[/dim]")
