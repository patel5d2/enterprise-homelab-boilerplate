"""
Migration command - convert legacy configurations to v2 format
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.table import Table
import yaml

from ...core.config import migrate_from_legacy, LabConfig
from ...core.config_writer import save_labconfig_to_yaml
from ...core.exceptions import HomeLabError

console = Console()


def run(
    input_file: str,
    output_file: Optional[str] = None,
    backup: bool = True,
    preview: bool = True,
    force: bool = False
) -> None:
    """
    Migrate legacy configuration to v2 format
    
    Args:
        input_file: Path to legacy configuration file
        output_file: Path for migrated configuration (default: input_file with .v2 suffix)
        backup: Create backup of original file
        preview: Show preview of migration before applying
        force: Skip confirmation prompts
    """
    
    input_path = Path(input_file)
    if not input_path.exists():
        raise HomeLabError(f"Input configuration file not found: {input_file}")
    
    # Determine output path
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = input_path.with_suffix(f'.v2{input_path.suffix}')
    
    console.print(Panel.fit(
        "📋 [bold blue]Configuration Migration Tool[/bold blue] 📋\n\n"
        "Convert legacy configuration to the new v2 format with\n"
        "service-specific settings and enhanced structure.",
        border_style="blue"
    ))
    
    try:
        # Load legacy configuration
        console.print(f"[dim]Loading configuration from {input_path}[/dim]")
        with open(input_path, 'r') as f:
            legacy_data = yaml.safe_load(f)
        
        if not legacy_data:
            raise HomeLabError("Configuration file is empty or invalid")
        
        # Check if it's already v2 format
        if legacy_data.get('version') == 2:
            console.print("[yellow]⚠️  Configuration is already in v2 format[/yellow]")
            if not force and not Confirm.ask("Continue anyway?"):
                console.print("Migration cancelled")
                return
        
        # Perform migration
        console.print("[cyan]🔄 Migrating configuration...[/cyan]")
        migrated_config = migrate_from_legacy(legacy_data)
        
        # Show preview if requested
        if preview and not force:
            show_migration_preview(legacy_data, migrated_config)
            
            if not Confirm.ask("Apply this migration?", default=True):
                console.print("Migration cancelled")
                return
        
        # Create backup if requested
        if backup and input_path.exists():
            backup_path = create_backup(input_path)
            if backup_path:
                console.print(f"[green]✓ Backup created: {backup_path}[/green]")
        
        # Save migrated configuration
        save_labconfig_to_yaml(migrated_config, output_path)
        
        console.print(f"\n[bold green]✅ Migration completed successfully![/bold green]")
        console.print(f"[green]✓ Migrated configuration saved to: {output_path}[/green]")
        
        # Show next steps
        show_next_steps(output_path, migrated_config)
        
    except yaml.YAMLError as e:
        raise HomeLabError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise HomeLabError(f"Migration failed: {e}")


def show_migration_preview(legacy_data: dict, migrated_config: LabConfig) -> None:
    """
    Show preview of migration changes
    
    Args:
        legacy_data: Original legacy configuration
        migrated_config: Migrated v2 configuration
    """
    console.print("\n" + "="*60)
    console.print("[bold yellow]📊 Migration Preview[/bold yellow]")
    console.print("="*60)
    
    # Show version change
    old_version = legacy_data.get('version', 1)
    new_version = migrated_config.version
    console.print(f"Version: {old_version} → {new_version}")
    console.print(f"Profile: → {migrated_config.profile}")
    
    # Show core configuration
    legacy_core = legacy_data.get('core', {})
    console.print(f"\n[bold]Core Configuration:[/bold]")
    console.print(f"  Domain: {legacy_core.get('domain', 'N/A')} → {migrated_config.core.domain}")
    console.print(f"  Email: {legacy_core.get('email', 'N/A')} → {migrated_config.core.email}")
    
    # Show service migration
    enabled_services = migrated_config.get_enabled_services()
    console.print(f"\n[bold]Services ({len(enabled_services)} enabled):[/bold]")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Service", style="white", width=20)
    table.add_column("Status", width=10)
    table.add_column("Migration Notes", style="dim")
    
    for service_id, config in enabled_services.items():
        status = "[green]✓ Enabled[/green]"
        notes = "Migrated from legacy format"
        
        # Add specific migration notes
        if service_id == 'traefik':
            notes = f"Domain: {config.domain}, ACME: {config.acme_environment}"
        elif service_id == 'postgresql':
            notes = f"Port: {config.port}, User: {config.superuser}"
        elif service_id == 'monitoring':
            notes = f"Retention: {config.prometheus_retention}"
        
        table.add_row(service_id.title(), status, notes)
    
    console.print(table)
    
    # Show custom environment variables
    if migrated_config.custom_env:
        console.print(f"\n[bold]Custom Environment Variables:[/bold]")
        for service_id, env_vars in migrated_config.custom_env.items():
            if env_vars:
                console.print(f"  • {service_id}: {len(env_vars)} variables")


def create_backup(file_path: Path) -> Optional[Path]:
    """
    Create backup of configuration file
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file if created, None otherwise
    """
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f'.backup.{timestamp}{file_path.suffix}')
        
        with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        
        return backup_path
    except Exception as e:
        console.print(f"[yellow]Warning: Could not create backup: {e}[/yellow]")
        return None


def show_next_steps(config_path: Path, migrated_config: LabConfig) -> None:
    """
    Show next steps after migration
    
    Args:
        config_path: Path to migrated configuration
        migrated_config: Migrated configuration
    """
    console.print("\n" + "="*60)
    console.print("[bold blue]📋 Next Steps[/bold blue]")
    console.print("="*60)
    
    table = Table(show_header=False, show_lines=True)
    table.add_column("Step", style="cyan", width=4)
    table.add_column("Action", style="white")
    
    table.add_row("1", f"Review migrated configuration: [cyan]{config_path}[/cyan]")
    table.add_row("2", "Validate configuration: [cyan]labctl validate[/cyan]")
    table.add_row("3", "Build compose files: [cyan]labctl build[/cyan]")
    table.add_row("4", "Deploy infrastructure: [cyan]labctl deploy[/cyan]")
    
    console.print(table)
    
    # Show service URLs
    console.print(f"\n[bold]🌐 Service URLs (after deployment):[/bold]")
    urls = migrated_config.get_service_urls()
    for service_id, url in urls.items():
        console.print(f"  • {service_id.title()}: {url}")
    
    console.print(f"\n[dim]💡 The migrated configuration uses the new v2 format[/dim]")
    console.print(f"[dim]💡 You can now use service-specific configuration options[/dim]")


def validate_migration(legacy_data: dict, migrated_config: LabConfig) -> list:
    """
    Validate migration results
    
    Args:
        legacy_data: Original configuration
        migrated_config: Migrated configuration
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Check core fields were preserved
    legacy_core = legacy_data.get('core', {})
    if legacy_core.get('domain') and legacy_core['domain'] != migrated_config.core.domain:
        issues.append("Core domain was not preserved during migration")
    
    if legacy_core.get('email') and legacy_core['email'] != migrated_config.core.email:
        issues.append("Core email was not preserved during migration")
    
    # Check service count
    enabled_services = migrated_config.get_enabled_services()
    if not enabled_services:
        issues.append("No services were enabled after migration")
    
    # Run standard validation
    config_issues = migrated_config.validate_configuration()
    issues.extend(config_issues)
    
    return issues


if __name__ == "__main__":
    # Test migration
    import sys
    if len(sys.argv) > 1:
        run(sys.argv[1], preview=True, force=False)
    else:
        print("Usage: python migrate_cmd.py <config_file>")