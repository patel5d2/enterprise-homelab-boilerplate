"""
Init command - interactive setup wizard
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

from ...core.config import Config
from ...core.exceptions import HomeLabError
import yaml
from typing import Dict

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
        if isinstance(config, dict):
            # Save as YAML if it's a dict
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2, sort_keys=False)
        else:
            config.save_to_file(config_path)
        console.print(f"\n[green]✅ Configuration saved to {config_file}[/green]")
        
        # Create directory structure
        _create_directories(config_path.parent)
        
        # Show next steps
        _show_next_steps(config)
        
    except Exception as e:
        raise HomeLabError(f"Failed to save configuration: {str(e)}")


def _interactive_setup():
    """Interactive configuration setup with service selection"""
    
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
    
    # Interactive service selection
    console.print("\n[bold]📦 Service Selection[/bold]")
    console.print("Select which services you want to include in your home lab:")
    
    selected_services = _interactive_service_selection()
    
    # Collect custom environment variables for selected services
    custom_env_vars = _collect_custom_environment_variables(selected_services)
    
    # Build configuration dict
    config_data = {
        "core": {
            "domain": domain,
            "email": email,
            "timezone": timezone
        },
        "reverse_proxy": {
            "provider": "traefik",
            "ssl_provider": "letsencrypt",
            "staging": False
        },
        "monitoring": {
            "enabled": selected_services.get("monitoring", True),
            "retention": "30d",
            "prometheus_port": 9090,
            "grafana_port": 3000
        },
        "gitlab": {
            "enabled": selected_services.get("gitlab", False),
            "runners": 3,
            "registry": True,
            "pages": True
        },
        "security": {
            "enabled": True,
            "vulnerability_scanning": True,
            "compliance_reporting": True
        },
        "vault": {
            "enabled": selected_services.get("vault", False),
            "auto_unseal": True,
            "ui_enabled": True
        },
        # Infrastructure services
        "networking": {
            "cloudflared": selected_services.get("cloudflared", False),
            "headscale": selected_services.get("headscale", False),
            "pihole": selected_services.get("pihole", False)
        },
        "databases": {
            "postgresql": selected_services.get("postgresql", True),
            "mongodb": selected_services.get("mongodb", False),
            "redis": selected_services.get("redis", True)
        },
        "backups": {
            "enabled": selected_services.get("backups", False),
            "backrest": selected_services.get("backrest", False),
            "restic": False,
            "s3_endpoint": ""
        },
        "passwords": {
            "vaultwarden": selected_services.get("vaultwarden", False)
        },
        "dashboards": {
            "glance": selected_services.get("glance", False),
            "uptime_kuma": selected_services.get("uptime_kuma", False)
        },
        "documentation": {
            "fumadocs": selected_services.get("fumadocs", False)
        },
        "automation": {
            "n8n": selected_services.get("n8n", False)
        },
        "ci_cd": {
            "gitlab": selected_services.get("gitlab", False),
            "jenkins": selected_services.get("jenkins", False)
        },
        "proxy": {
            "traefik": True,  # Always enabled as default
            "nginx_proxy_manager": selected_services.get("nginx_proxy_manager", False),
            "caddy": selected_services.get("caddy", False)
        },
        "custom_env": {
            "variables": custom_env_vars
        }
    }
    
    return config_data


def _interactive_service_selection() -> dict:
    """Interactive service selection with categories"""
    
    services = {
        # Core services (always recommended)
        "Core Services": {
            "postgresql": {"name": "PostgreSQL", "desc": "Relational database", "default": True},
            "redis": {"name": "Redis", "desc": "In-memory cache & message broker", "default": True},
            "monitoring": {"name": "Monitoring Stack", "desc": "Prometheus + Grafana", "default": True}
        },
        
        # Networking & DNS
        "Networking & DNS": {
            "pihole": {"name": "Pi-hole", "desc": "DNS ad-blocking and local DNS", "default": False},
            "headscale": {"name": "Headscale", "desc": "Self-hosted Tailscale coordinator", "default": False},
            "cloudflared": {"name": "Cloudflared", "desc": "Zero Trust tunnel", "default": False}
        },
        
        # Security & Secrets
        "Security & Secrets": {
            "vaultwarden": {"name": "Vaultwarden", "desc": "Password manager (Bitwarden)", "default": False},
            "vault": {"name": "HashiCorp Vault", "desc": "Enterprise secrets management", "default": False}
        },
        
        # Dashboards & Monitoring  
        "Dashboards & Monitoring": {
            "glance": {"name": "Glance", "desc": "Home lab dashboard", "default": False},
            "uptime_kuma": {"name": "Uptime Kuma", "desc": "Uptime monitoring", "default": False}
        },
        
        # Development & CI/CD
        "Development & CI/CD": {
            "gitlab": {"name": "GitLab CE", "desc": "Git repository & CI/CD", "default": False},
            "jenkins": {"name": "Jenkins", "desc": "CI/CD automation server", "default": False}
        },
        
        # Databases & Storage
        "Databases & Storage": {
            "mongodb": {"name": "MongoDB", "desc": "Document database", "default": False},
            "backups": {"name": "Backup Services", "desc": "Automated backups", "default": False},
            "backrest": {"name": "pgBackRest", "desc": "PostgreSQL backup tool", "default": False}
        },
        
        # Automation & Workflows
        "Automation & Workflows": {
            "n8n": {"name": "n8n", "desc": "Workflow automation", "default": False},
            "fumadocs": {"name": "Fumadocs", "desc": "Documentation platform", "default": False}
        },
        
        # Alternative Proxy Options
        "Alternative Proxies": {
            "nginx_proxy_manager": {"name": "Nginx Proxy Manager", "desc": "Web-based proxy manager", "default": False},
            "caddy": {"name": "Caddy", "desc": "Modern web server with automatic HTTPS", "default": False}
        }
    }
    
    selected = {}
    
    for category, category_services in services.items():
        console.print(f"\n[bold cyan]{category}:[/bold cyan]")
        
        for service_id, service_info in category_services.items():
            default_choice = service_info["default"]
            choice = Confirm.ask(
                f"  {service_info['name']} - {service_info['desc']}",
                default=default_choice
            )
            selected[service_id] = choice
    
    # Show summary
    console.print("\n[bold green]Selected Services Summary:[/bold green]")
    enabled_services = [k for k, v in selected.items() if v]
    
    if enabled_services:
        for service in enabled_services:
            console.print(f"  ✓ {service}")
    else:
        console.print("  Only core infrastructure (Traefik) will be installed")
        
    console.print(f"\nTotal services selected: [bold]{len(enabled_services)}[/bold]")
    
    return selected


def _collect_custom_environment_variables(selected_services: Dict[str, bool]) -> Dict[str, Dict[str, str]]:
    """Collect custom environment variables for selected services"""
    
    custom_env_vars = {}
    
    # Get list of enabled services
    enabled_services = [service for service, enabled in selected_services.items() if enabled]
    
    if not enabled_services:
        return custom_env_vars
    
    console.print("\n[bold]⚙️ Custom Environment Variables[/bold]")
    console.print("You can add custom environment variables for each service.")
    console.print("Press [cyan]Enter[/cyan] to skip if you don't need custom variables for a service.")
    
    # Map of service IDs to user-friendly names
    service_names = {
        "postgresql": "PostgreSQL",
        "redis": "Redis", 
        "mongodb": "MongoDB",
        "pihole": "Pi-hole",
        "headscale": "Headscale",
        "cloudflared": "Cloudflared",
        "vaultwarden": "Vaultwarden",
        "vault": "HashiCorp Vault",
        "glance": "Glance Dashboard",
        "uptime_kuma": "Uptime Kuma",
        "gitlab": "GitLab CE",
        "jenkins": "Jenkins",
        "n8n": "n8n",
        "fumadocs": "Fumadocs",
        "nginx_proxy_manager": "Nginx Proxy Manager",
        "caddy": "Caddy"
    }
    
    for service in enabled_services:
        service_display_name = service_names.get(service, service.title())
        
        console.print(f"\n[cyan]• {service_display_name}[/cyan]")
        
        if Confirm.ask(f"Add custom environment variables for {service_display_name}?", default=False):
            service_env_vars = {}
            
            console.print(f"[dim]Enter environment variables for {service_display_name} (format: KEY=value)[/dim]")
            console.print("[dim]Press Enter with empty input to finish adding variables[/dim]")
            
            while True:
                env_input = Prompt.ask(
                    "Environment variable (KEY=value)",
                    default=""
                )
                
                if not env_input.strip():
                    break
                    
                # Parse KEY=value format
                if "=" in env_input:
                    key, value = env_input.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key and value:
                        service_env_vars[key] = value
                        console.print(f"[green]Added: {key}={value}[/green]")
                    else:
                        console.print("[red]Invalid format. Use KEY=value[/red]")
                else:
                    console.print("[red]Invalid format. Use KEY=value (e.g., DEBUG=true)[/red]")
            
            if service_env_vars:
                custom_env_vars[service] = service_env_vars
                console.print(f"[green]✓ Added {len(service_env_vars)} custom variables for {service_display_name}[/green]")
    
    if custom_env_vars:
        console.print(f"\n[bold green]Custom Environment Variables Summary:[/bold green]")
        for service, vars_dict in custom_env_vars.items():
            service_name = service_names.get(service, service.title())
            console.print(f"  • {service_name}: {len(vars_dict)} variables")
    
    return custom_env_vars


def _default_setup():
    """Default configuration setup"""
    
    console.print("[yellow]Using default configuration...[/yellow]")
    
    return {
        "core": {
            "domain": "homelab.local",
            "email": "admin@homelab.local",
            "timezone": "UTC"
        },
        "reverse_proxy": {
            "provider": "traefik",
            "ssl_provider": "letsencrypt",
            "staging": False
        },
        "monitoring": {
            "enabled": True,
            "retention": "30d",
            "prometheus_port": 9090,
            "grafana_port": 3000
        },
        "gitlab": {
            "enabled": False,
            "runners": 3,
            "registry": True,
            "pages": True
        },
        "security": {
            "enabled": True,
            "vulnerability_scanning": True,
            "compliance_reporting": True
        },
        "vault": {
            "enabled": False,
            "auto_unseal": True,
            "ui_enabled": True
        },
        "networking": {
            "cloudflared": False,
            "headscale": False,
            "pihole": True
        },
        "databases": {
            "postgresql": True,
            "mongodb": False,
            "redis": True
        },
        "backups": {
            "enabled": False,
            "backrest": False,
            "restic": False,
            "s3_endpoint": ""
        },
        "passwords": {
            "vaultwarden": True
        },
        "dashboards": {
            "glance": True,
            "uptime_kuma": True
        },
        "documentation": {
            "fumadocs": False
        },
        "automation": {
            "n8n": False
        },
        "ci_cd": {
            "gitlab": False,
            "jenkins": False
        },
        "proxy": {
            "traefik": True,
            "nginx_proxy_manager": False,
            "caddy": False
        }
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


def _show_next_steps(config) -> None:
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
    
    # Service URLs (simplified for dict config)
    console.print(f"\n[bold]🌐 Service URLs (after deployment):[/bold]")
    domain = config.get('core', {}).get('domain', 'homelab.local')
    base_urls = {
        'traefik': f'https://traefik.{domain}',
        'grafana': f'https://grafana.{domain}',
        'prometheus': f'https://prometheus.{domain}'
    }
    
    # Add conditional URLs based on enabled services
    if config.get('passwords', {}).get('vaultwarden'):
        base_urls['vaultwarden'] = f'https://vault.{domain}'
    if config.get('dashboards', {}).get('glance'):
        base_urls['glance'] = f'https://dashboard.{domain}'
    if config.get('dashboards', {}).get('uptime_kuma'):
        base_urls['uptime-kuma'] = f'https://uptime.{domain}'
    if config.get('networking', {}).get('pihole'):
        base_urls['pihole'] = f'https://pihole.{domain}'
    
    for service, url in base_urls.items():
        console.print(f"  • {service.title()}: {url}")
    
    console.print(f"\n[dim]💡 Edit configuration anytime with: labctl config --edit[/dim]")
