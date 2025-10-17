"""
Validate command - configuration and system validation
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table

from ...core.config import Config
from ...core.exceptions import HomeLabError, ValidationError

console = Console()


def run(config_file: str, strict: bool = False) -> None:
    """Validate configuration and system requirements"""
    
    console.print("🔍 Validating configuration...")
    
    config_path = Path(config_file)
    if not config_path.exists():
        raise HomeLabError(f"Configuration file not found: {config_file}")
    
    try:
        # Load and validate configuration
        config = Config.load_from_file(config_path)
        
        # Check for warnings
        warnings = config.validate_requirements()
        
        # Display results
        table = Table(title="Validation Results")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message", style="white")
        
        table.add_row("Schema", "✅ Valid", "Configuration schema is valid")
        table.add_row("Core Settings", "✅ Valid", f"Domain: {config.core.domain}")
        table.add_row("Reverse Proxy", "✅ Valid", f"Provider: {config.reverse_proxy.provider}")
        
        if warnings:
            for warning in warnings:
                table.add_row("Warning", "⚠️ Warning", warning)
        
        console.print(table)
        
        if warnings and not strict:
            console.print("\n[yellow]Warnings found but validation passed[/yellow]")
        elif warnings and strict:
            raise ValidationError("Strict validation failed due to warnings", warnings)
        else:
            console.print("\n[green]✅ Configuration validation passed![/green]")
            
    except ValidationError as e:
        console.print(f"\n[red]❌ Validation failed: {e.message}[/red]")
        if hasattr(e, 'errors') and e.errors:
            for error in e.errors:
                console.print(f"  • {error.get('path', 'unknown')}: {error.get('message', '')}")
        raise e