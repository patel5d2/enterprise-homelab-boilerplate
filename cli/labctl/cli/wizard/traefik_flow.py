"""
Traefik Specialized Configuration Flow

This module provides specialized configuration prompts for Traefik,
including Cloudflare DNS challenge setup, wildcard certificates,
and dashboard authentication.
"""

import re
from typing import Dict, Any, Optional, Tuple
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from ...core.secrets import generate_password, generate_htpasswd_hash

console = Console()


def validate_domain(domain: str) -> bool:
    """
    Validate domain format
    
    Args:
        domain: Domain string to validate
        
    Returns:
        True if valid domain format
    """
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
    return bool(re.match(pattern, domain)) and len(domain) <= 253


def validate_cloudflare_token(token: str) -> bool:
    """
    Validate Cloudflare API token format
    
    Args:
        token: Token string to validate
        
    Returns:
        True if valid token format
    """
    # Cloudflare API tokens are typically 40 character alphanumeric strings
    return bool(re.match(r'^[A-Za-z0-9_-]{40}$', token))


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def configure_traefik_domain() -> str:
    """
    Configure the primary domain for Traefik
    
    Returns:
        Validated domain string
    """
    console.print("\n[bold blue]🌐 Domain Configuration[/bold blue]")
    console.print("Configure your primary domain for SSL certificates and routing.")
    
    while True:
        domain = Prompt.ask(
            "Primary domain (e.g., example.com)",
            default="homelab.local",
            console=console
        )
        
        if validate_domain(domain):
            return domain
        else:
            console.print("[red]Invalid domain format. Please enter a valid domain.[/red]")


def configure_cloudflare_credentials() -> Tuple[str, Dict[str, str]]:
    """
    Configure Cloudflare DNS challenge credentials
    
    Returns:
        Tuple of (provider_type, credentials_dict)
    """
    console.print("\n[bold blue]☁️ Cloudflare DNS Challenge[/bold blue]")
    console.print("Configure Cloudflare for automatic DNS challenge and wildcard certificates.")
    
    console.print("\n[bold]Authentication Methods:[/bold]")
    console.print("1. [cyan]API Token[/cyan] (Recommended) - Scoped permissions, more secure")
    console.print("2. [cyan]Global API Key[/cyan] - Full account access, less secure")
    
    choice = Prompt.ask(
        "Authentication method",
        choices=["1", "2", "token", "key"],
        default="1",
        console=console
    )
    
    if choice in ["1", "token"]:
        return configure_api_token()
    else:
        return configure_global_key()


def configure_api_token() -> Tuple[str, Dict[str, str]]:
    """
    Configure Cloudflare API token authentication
    
    Returns:
        Tuple of (provider_type, credentials_dict)
    """
    console.print("\n[bold]API Token Configuration[/bold]")
    console.print("[dim]Create a token at: https://dash.cloudflare.com/profile/api-tokens[/dim]")
    console.print("[dim]Required permissions: Zone:Zone:Read, Zone:DNS:Edit[/dim]")
    
    while True:
        token = Prompt.ask(
            "Cloudflare API Token",
            password=True,
            console=console
        )
        
        if validate_cloudflare_token(token):
            console.print("[green]✓ Token format looks valid[/green]")
            break
        else:
            console.print("[red]Invalid token format. Tokens should be 40 characters.[/red]")
            if not Confirm.ask("Try again?", default=True, console=console):
                break
    
    return "token", {
        "CLOUDFLARE_DNS_API_TOKEN": token
    }


def configure_global_key() -> Tuple[str, Dict[str, str]]:
    """
    Configure Cloudflare Global API Key authentication
    
    Returns:
        Tuple of (provider_type, credentials_dict)
    """
    console.print("\n[bold]Global API Key Configuration[/bold]")
    console.print("[yellow]Warning: Global API Key provides full account access[/yellow]")
    console.print("[dim]Find your key at: https://dash.cloudflare.com/profile/api-tokens[/dim]")
    
    while True:
        email = Prompt.ask("Cloudflare account email", console=console)
        if validate_email(email):
            break
        else:
            console.print("[red]Invalid email format[/red]")
    
    api_key = Prompt.ask(
        "Global API Key",
        password=True,
        console=console
    )
    
    return "global_key", {
        "CLOUDFLARE_EMAIL": email,
        "CLOUDFLARE_API_KEY": api_key
    }


def configure_acme_environment() -> str:
    """
    Configure ACME environment (staging vs production)
    
    Returns:
        ACME environment string
    """
    console.print("\n[bold blue]🔒 SSL Certificate Environment[/bold blue]")
    console.print("[bold]Environment Options:[/bold]")
    console.print("• [green]Production[/green] - Real certificates, rate limited")
    console.print("• [yellow]Staging[/yellow] - Test certificates, higher rate limits")
    
    choice = Prompt.ask(
        "ACME environment",
        choices=["production", "staging"],
        default="production",
        console=console
    )
    
    return choice


def configure_wildcard_certificates() -> bool:
    """
    Configure wildcard certificate option
    
    Returns:
        True if wildcard certificates should be enabled
    """
    console.print("\n[bold blue]🌟 Wildcard Certificates[/bold blue]")
    console.print("Wildcard certificates secure *.yourdomain.com automatically.")
    console.print("[dim]Requires DNS challenge (already configured with Cloudflare)[/dim]")
    
    return Confirm.ask(
        "Enable wildcard certificates?",
        default=True,
        console=console
    )


def configure_dashboard() -> Tuple[bool, Optional[Dict[str, str]]]:
    """
    Configure Traefik dashboard access
    
    Returns:
        Tuple of (enabled, auth_config_dict)
    """
    console.print("\n[bold blue]📊 Traefik Dashboard[/bold blue]")
    console.print("The dashboard provides monitoring and configuration visibility.")
    
    enabled = Confirm.ask(
        "Enable Traefik dashboard?",
        default=True,
        console=console
    )
    
    if not enabled:
        return False, None
    
    console.print("\n[bold]Dashboard Security[/bold]")
    console.print("Secure the dashboard with HTTP basic authentication.")
    
    username = Prompt.ask(
        "Dashboard admin username",
        default="admin",
        console=console
    )
    
    # Generate a secure password
    password = generate_password(16, charset="alphanumeric_symbols")
    console.print(f"[green]Generated secure password for dashboard access[/green]")
    
    # Create htpasswd hash for Traefik
    htpasswd_hash = generate_htpasswd_hash(username, password)
    
    auth_config = {
        "dashboard_enabled": True,
        "dashboard_username": username,
        "dashboard_auth_hash": htpasswd_hash
    }
    
    # Store password in environment variables
    env_vars = {
        "TRAEFIK_DASHBOARD_PASSWORD": password
    }
    
    return True, {"config": auth_config, "env_vars": env_vars}


def configure_advanced_options() -> Dict[str, Any]:
    """
    Configure advanced Traefik options
    
    Returns:
        Dictionary of advanced configuration options
    """
    console.print("\n[bold blue]⚙️ Advanced Options[/bold blue]")
    
    config = {}
    
    if Confirm.ask("Enable HSTS (HTTP Strict Transport Security)?", default=True, console=console):
        config["hsts_enabled"] = True
    
    if Confirm.ask("Force HTTPS redirects?", default=True, console=console):
        config["https_redirect"] = True
    
    if Confirm.ask("Enable IPv6 support?", default=False, console=console):
        config["ipv6_enabled"] = True
    
    return config


def run_traefik_configuration() -> Dict[str, Any]:
    """
    Run the complete Traefik configuration flow
    
    Returns:
        Complete Traefik configuration dictionary
    """
    console.print(Panel.fit(
        "🚀 [bold blue]Traefik Configuration Wizard[/bold blue] 🚀\n\n"
        "Configure your reverse proxy with SSL, DNS challenge,\n"
        "and automatic certificate management.\n\n"
        "[dim]This will set up Cloudflare integration for DNS challenges[/dim]",
        border_style="blue"
    ))
    
    try:
        # Step 1: Domain configuration
        domain = configure_traefik_domain()
        
        # Step 2: Cloudflare credentials
        provider_type, cloudflare_creds = configure_cloudflare_credentials()
        
        # Step 3: ACME environment
        acme_env = configure_acme_environment()
        
        # Step 4: Wildcard certificates
        wildcard_enabled = configure_wildcard_certificates()
        
        # Step 5: Dashboard configuration
        dashboard_enabled, dashboard_config = configure_dashboard()
        
        # Step 6: Advanced options
        advanced_config = configure_advanced_options()
        
        # Build complete configuration
        traefik_config = {
            "enabled": True,
            "domain": domain,
            "acme_environment": acme_env,
            "dns_provider": "cloudflare",
            "dns_provider_type": provider_type,
            "wildcard_enabled": wildcard_enabled,
            **advanced_config
        }
        
        # Add dashboard configuration
        if dashboard_enabled and dashboard_config:
            traefik_config.update(dashboard_config["config"])
        
        # Collect all environment variables
        env_vars = cloudflare_creds.copy()
        if dashboard_enabled and dashboard_config and "env_vars" in dashboard_config:
            env_vars.update(dashboard_config["env_vars"])
        
        # Show configuration summary
        show_traefik_summary(traefik_config, env_vars)
        
        # Show DNS setup instructions
        show_dns_setup_instructions(domain)
        
        return {
            "config": traefik_config,
            "env_vars": env_vars
        }
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Traefik configuration cancelled[/yellow]")
        return {}
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        return {}


def show_traefik_summary(config: Dict[str, Any], env_vars: Dict[str, str]) -> None:
    """
    Display Traefik configuration summary
    
    Args:
        config: Traefik configuration dictionary
        env_vars: Environment variables dictionary
    """
    console.print("\n" + "="*60)
    console.print("[bold green]🎯 Traefik Configuration Summary[/bold green]")
    console.print("="*60)
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="white", width=25)
    table.add_column("Value", style="green")
    
    table.add_row("Domain", config.get("domain", ""))
    table.add_row("ACME Environment", config.get("acme_environment", ""))
    table.add_row("DNS Provider", f"Cloudflare ({config.get('dns_provider_type', '')})")
    table.add_row("Wildcard Certificates", "✓" if config.get("wildcard_enabled") else "✗")
    table.add_row("Dashboard", "✓" if config.get("dashboard_enabled") else "✗")
    table.add_row("HSTS", "✓" if config.get("hsts_enabled") else "✗")
    table.add_row("HTTPS Redirect", "✓" if config.get("https_redirect") else "✗")
    table.add_row("IPv6", "✓" if config.get("ipv6_enabled") else "✗")
    
    console.print(table)
    
    # Show environment variables (redacted)
    if env_vars:
        console.print(f"\n[bold]Environment Variables ({len(env_vars)} secrets):[/bold]")
        for key in env_vars.keys():
            console.print(f"  • {key}: [dim]●●●●●●●●[/dim]")


def show_dns_setup_instructions(domain: str) -> None:
    """
    Display DNS setup instructions
    
    Args:
        domain: Primary domain name
    """
    console.print("\n" + "="*60)
    console.print("[bold yellow]📋 Next Steps: DNS Configuration[/bold yellow]")
    console.print("="*60)
    
    console.print(f"\n[bold]Required DNS Records for {domain}:[/bold]")
    console.print(f"  • A record: {domain} → [your-server-ip]")
    console.print(f"  • A record: *.{domain} → [your-server-ip] (for wildcard)")
    
    console.print("\n[bold]Cloudflare Setup:[/bold]")
    console.print("1. 🌐 Add your domain to Cloudflare")
    console.print("2. 📝 Create DNS records pointing to your server")
    console.print("3. 🔒 Ensure SSL/TLS is set to 'Full (strict)' mode")
    console.print("4. ⚡ Consider enabling proxy (orange cloud) for security")
    
    console.print("\n[bold]Verification:[/bold]")
    console.print("After deployment, check:")
    console.print(f"  • https://traefik.{domain} - Traefik dashboard")
    console.print(f"  • https://{domain} - Your main site")
    console.print("  • Certificate validity and wildcard support")
    
    console.print("\n[dim]💡 Tip: Use 'dig' or 'nslookup' to verify DNS propagation[/dim]")


if __name__ == "__main__":
    # Test the configuration flow
    result = run_traefik_configuration()
    print("\nConfiguration result:")
    print(result)