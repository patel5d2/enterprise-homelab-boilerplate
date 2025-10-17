"""
Config command - configuration management and viewing
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel

from ...core.config import Config
from ...core.exceptions import HomeLabError

console = Console()


def run(
    config_file: str,
    show: bool = False,
    edit: bool = False,
    key: Optional[str] = None,
    format: str = "yaml"
) -> None:
    """Manage configuration files"""
    
    config_path = Path(config_file)
    if not config_path.exists():
        raise HomeLabError(f"Configuration file not found: {config_file}")
    
    # Load configuration
    config = Config.load_from_file(config_path)
    
    if show:
        _show_config(config_path, config, key, format)
    elif edit:
        _edit_config(config_path)
    else:
        _display_config_info(config, config_path)


def _show_config(
    config_path: Path,
    config: Config,
    key: Optional[str],
    format: str
) -> None:
    """Show configuration content"""
    
    if key:
        # Show specific key
        value = _get_config_value(config, key)
        console.print(f"[cyan]{key}[/cyan]: {value}")
        return
    
    # Show full configuration
    with open(config_path, 'r') as f:
        content = f.read()
    
    if format.lower() == 'yaml':
        syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    elif format.lower() == 'json':
        # Convert to JSON if requested
        import json
        import yaml
        try:
            data = yaml.safe_load(content)
            json_content = json.dumps(data, indent=2)
            syntax = Syntax(json_content, "json", theme="monokai", line_numbers=True)
        except Exception:
            syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
    else:
        syntax = Syntax(content, "text", line_numbers=True)
    
    panel = Panel(
        syntax,
        title=f"📋 Configuration: {config_path.name}",
        border_style="blue"
    )
    
    console.print(panel)


def _edit_config(config_path: Path) -> None:
    """Edit configuration file with default editor"""
    
    import os
    import subprocess
    
    # Try to find a suitable editor
    editors = [
        os.environ.get('EDITOR'),
        'code',  # VS Code
        'nano',
        'vim',
        'vi',
    ]
    
    editor = None
    for e in editors:
        if e and _command_exists(e):
            editor = e
            break
    
    if not editor:
        console.print("[yellow]No suitable editor found.[/yellow]")
        console.print("Set the EDITOR environment variable or install: code, nano, vim")
        console.print(f"Edit manually: [cyan]{config_path}[/cyan]")
        return
    
    try:
        subprocess.run([editor, str(config_path)], check=True)
        console.print(f"[green]✅ Configuration edited with {editor}[/green]")
        console.print("Run [cyan]labctl validate[/cyan] to check your changes")
    except subprocess.CalledProcessError:
        raise HomeLabError(f"Failed to edit configuration with {editor}")
    except KeyboardInterrupt:
        console.print("\n[yellow]Edit cancelled[/yellow]")


def _display_config_info(config: Config, config_path: Path) -> None:
    """Display configuration summary"""
    
    table = Table(title="⚙️ Configuration Summary")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    # Core settings
    table.add_row("📁 Config File", str(config_path))
    table.add_row("🌐 Domain", config.core.domain)
    table.add_row("📧 Email", config.core.email or "Not set")
    table.add_row("🕒 Timezone", config.core.timezone or "UTC")
    
    # Reverse proxy
    table.add_row("🔀 Reverse Proxy", config.reverse_proxy.provider)
    table.add_row("🔒 SSL Provider", config.reverse_proxy.ssl_provider)
    table.add_row("🧪 SSL Staging", "Yes" if config.reverse_proxy.staging else "No")
    
    # Features
    features = []
    if config.monitoring.enabled:
        features.append("📊 Monitoring")
    if config.gitlab.enabled:
        features.append("🦊 GitLab")
    if config.security.enabled:
        features.append("🔒 Security")
    if config.vault.enabled:
        features.append("🔐 Vault")
    
    if features:
        table.add_row("⚡ Features", "\n".join(features))
    else:
        table.add_row("⚡ Features", "Core only")
    
    console.print(table)
    
    # Show service URLs
    console.print(f"\n[bold]🌐 Service URLs:[/bold]")
    urls = config.get_service_urls()
    for service, url in urls.items():
        if (service == "gitlab" and config.gitlab.enabled) or \
           (service == "vault" and config.vault.enabled) or \
           (service in ["prometheus", "grafana"] and config.monitoring.enabled) or \
           service == "traefik":
            console.print(f"  • {service.title()}: {url}")
    
    console.print(f"\n[bold]🔧 Actions:[/bold]")
    console.print(f"  • View content: [cyan]labctl config --show[/cyan]")
    console.print(f"  • Edit config: [cyan]labctl config --edit[/cyan]")
    console.print(f"  • Validate: [cyan]labctl validate[/cyan]")


def _get_config_value(config: Config, key: str):
    """Get a configuration value by dot-notation key"""
    
    parts = key.split('.')
    value = config
    
    for part in parts:
        if hasattr(value, part):
            value = getattr(value, part)
        else:
            raise HomeLabError(f"Configuration key not found: {key}")
    
    return value


def _command_exists(command: str) -> bool:
    """Check if a command exists in PATH"""
    
    import shutil
    return shutil.which(command) is not None