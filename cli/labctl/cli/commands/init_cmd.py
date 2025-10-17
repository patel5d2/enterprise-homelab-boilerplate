"""
Init command - interactive setup wizard
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from ...core.config import Config, CoreConfig, ReverseProxyConfig, MonitoringConfig, GitLabConfig, SecurityConfig, VaultConfig
from ...core.exceptions import HomeLabError

console = Console()


def run(
    config_file: str,
    interactive: bool = True,
    force: bool = False
) -> None:
    """Initialize new home lab configuration"""
    
    config_path = Path(config_file)
    
    # Check if config already exists
    if config_path.exists() and not force:
        if not Confirm.ask(f"Configuration file {config_file} already exists. Overwrite?"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return
    
    console.print(Panel.fit(
        "🏠 [bold blue]Home Lab Setup Wizard[/bold blue] 🏠\n\n"
        "Welcome to the Enterprise Home Lab setup wizard!\n"
        "This will guide you through configuring your infrastructure.",
        border_style="blue"
    ))
    
    if interactive:
        config = _interactive_setup()
    else:
        config = _default_setup()
    
    # Save configuration
    try:
        config.save_to_file(config_path)
        console.print(f"\n[green]✅ Configuration saved to {config_file}[/green]")
        
        # Create directory structure
        _create_directories(config_path.parent)
        
        # Show next steps
        _show_next_steps(config)
        
    except Exception as e:
        raise HomeLabError(f"Failed to save configuration: {str(e)}")


def _interactive_setup() -> Config:
    """Interactive configuration setup"""
    
    console.print("\n[bold]📝 Core Configuration[/bold]")
    
    # Core settings
    domain = Prompt.ask(
        "🌐 Primary domain (e.g., homelab.example.com)",
        default="homelab.local"
    )
    
    email = Prompt.ask(
        "📧 Admin email address",
        default="admin@example.com"
    )
    
    timezone = Prompt.ask(
        "🕒 Timezone",
        default="UTC"
    )
    
    core_config = CoreConfig(domain=domain, email=email, timezone=timezone)
    
    console.print("\n[bold]🔀 Reverse Proxy Configuration[/bold]")
    
    # Reverse proxy settings
    reverse_proxy_provider = Prompt.ask(
        "Reverse proxy provider",
        choices=["traefik", "caddy", "nginx"],
        default="traefik"
    )
    
    ssl_staging = Confirm.ask(
        "Use Let's Encrypt staging (for testing)?",
        default=False
    )
    
    reverse_proxy_config = ReverseProxyConfig(
        provider=reverse_proxy_provider,
        staging=ssl_staging
    )
    
    console.print("\n[bold]🚀 Feature Selection[/bold]")
    
    # GitLab Enterprise
    gitlab_enabled = Confirm.ask(
        "🦊 Enable GitLab Enterprise Edition?",
        default=True
    )
    
    gitlab_config = GitLabConfig(enabled=gitlab_enabled)
    if gitlab_enabled:
        gitlab_config.runners = int(Prompt.ask(
            "Number of GitLab runners",
            default="3"
        ))
    
    # Monitoring
    monitoring_enabled = Confirm.ask(
        "📊 Enable monitoring stack (Prometheus, Grafana)?",
        default=True
    )
    
    monitoring_config = MonitoringConfig(enabled=monitoring_enabled)
    
    # Security
    security_enabled = Confirm.ask(
        "🔒 Enable security features (Vault, scanning)?",
        default=True
    )
    
    security_config = SecurityConfig(enabled=security_enabled)
    
    # Vault
    vault_enabled = Confirm.ask(
        "🔐 Enable HashiCorp Vault?",
        default=False
    )
    
    vault_config = VaultConfig(enabled=vault_enabled)
    
    return Config(
        core=core_config,
        reverse_proxy=reverse_proxy_config,
        monitoring=monitoring_config,
        gitlab=gitlab_config,
        security=security_config,
        vault=vault_config
    )


def _default_setup() -> Config:
    """Default configuration setup"""
    
    console.print("[yellow]Using default configuration...[/yellow]")
    
    return Config(
        core=CoreConfig(
            domain="homelab.local",
            email="admin@example.com",
            timezone="UTC"
        ),
        reverse_proxy=ReverseProxyConfig(),
        monitoring=MonitoringConfig(enabled=True),
        gitlab=GitLabConfig(enabled=True),
        security=SecurityConfig(enabled=True),
        vault=VaultConfig(enabled=False)
    )


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


def _show_next_steps(config: Config) -> None:
    """Show next steps after initialization"""
    
    console.print("\n[bold]🎯 Next Steps:[/bold]")
    
    table = Table(show_header=False, show_lines=True)
    table.add_column("Step", style="cyan", width=4)
    table.add_column("Action", style="white")
    
    table.add_row("1", "Validate configuration: [cyan]labctl validate[/cyan]")
    table.add_row("2", "Build compose files: [cyan]labctl build[/cyan]")
    table.add_row("3", "Deploy infrastructure: [cyan]labctl deploy[/cyan]")
    table.add_row("4", "Check status: [cyan]labctl status[/cyan]")
    
    console.print(table)
    
    # Service URLs
    console.print(f"\n[bold]🌐 Service URLs (after deployment):[/bold]")
    urls = config.get_service_urls()
    for service, url in urls.items():
        console.print(f"  • {service.title()}: {url}")
    
    console.print(f"\n[dim]💡 Edit configuration anytime with: labctl config --edit[/dim]")