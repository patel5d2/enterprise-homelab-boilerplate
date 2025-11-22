"""
Deploy command - orchestrates service deployment
"""

import subprocess
import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress

from ...core.config import Config
from ...core.exceptions import DeploymentError, HomeLabError
from ...core.health import HealthChecker

console = Console()


def run(
    config_file: str,
    services: Optional[List[str]] = None,
    compose_dir: Optional[str] = None,
    detach: bool = True,
    build: bool = False,
    wait: bool = True,
    timeout: int = 300,
) -> None:
    """Deploy services using Docker Compose"""

    console.print("🚀 Deploying home lab services...")

    config_path = Path(config_file)
    if not config_path.exists():
        raise HomeLabError(f"Configuration file not found: {config_file}")

    # Load configuration
    # Load configuration
    import yaml
    from ...core.config import LabConfig
    
    # Check version
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    if config_data.get("version") == 2:
        config = LabConfig.load_from_file(config_path)
    else:
        config = Config.load_from_file(config_path)

    # Set compose directory
    if compose_dir:
        compose_path = Path(compose_dir)
    else:
        compose_path = config_path.parent / "compose"

    compose_file = compose_path / "docker-compose.yml"
    if not compose_file.exists():
        raise HomeLabError(
            f"Docker Compose file not found: {compose_file}. Run 'labctl build' first."
        )

    try:
        with Progress() as progress:
            deploy_task = progress.add_task("Deploying services...", total=100)

            # Build compose file if requested
            if build:
                progress.update(deploy_task, description="Building compose file...")
                _build_compose_files(config_file, compose_path)
                progress.update(deploy_task, advance=20)

            # Create networks first
            progress.update(deploy_task, description="Creating networks...")
            _create_networks()
            progress.update(deploy_task, advance=10)

            # Check for environment file
            env_file = compose_path / ".env"
            if not env_file.exists():
                console.print("[yellow]⚠️  .env file not found. Attempting to generate...[/yellow]")
                
                # Try to generate from config
                env_vars = {}
                if isinstance(config, LabConfig) and hasattr(config, "env_vars"):
                     # LabConfig doesn't have env_vars field in definition but init creates it in dict
                     # We might need to access the raw dict or add it to LabConfig
                     pass 
                
                # Fallback: Try to load from config file directly if model doesn't have it
                try:
                    import yaml
                    with open(config_file, "r") as f:
                        raw_config = yaml.safe_load(f)
                    env_vars = raw_config.get("env_vars", {})
                except Exception:
                    env_vars = {}

                if env_vars:
                    from ...core.secrets import load_or_create_env
                    load_or_create_env(str(env_file), env_vars)
                    console.print("[green]✓ Generated .env file from configuration[/green]")
                else:
                    # Fallback to template copy
                    env_template = compose_path / ".env.template"
                    if env_template.exists():
                        import shutil
                        shutil.copy(env_template, env_file)
                        console.print("[yellow]✓ Copied .env.template to .env (please configure secrets)[/yellow]")
                
                progress.update(deploy_task, advance=5)

            # Deploy all services
            progress.update(deploy_task, description="Deploying services...")
            _deploy_compose_stack(compose_path, "docker-compose.yml", services, detach)
            progress.update(deploy_task, advance=60)

            # Wait for services to be healthy
            if wait:
                progress.update(deploy_task, description="Waiting for services...")
                _wait_for_services(config, timeout)
                progress.update(deploy_task, advance=5)

        console.print(f"\n[green]✅ Deployment completed successfully![/green]")
        _show_deployment_info(config, compose_path)

    except Exception as e:
        raise DeploymentError(f"Deployment failed: {str(e)}")


def _build_compose_files(config_file: str, compose_path: Path) -> None:
    """Build compose files before deployment"""
    from .build_cmd import run as build_run

    build_run(config_file, output_dir=str(compose_path), force=True)


def _create_networks() -> None:
    """Create Docker networks if they don't exist"""
    networks = ["traefik"]

    for network in networks:
        try:
            # Check if network exists
            result = subprocess.run(
                ["docker", "network", "inspect", network],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Create network
                subprocess.run(
                    ["docker", "network", "create", network],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                console.print(f"[dim]✓ Created network: {network}[/dim]")
            else:
                console.print(f"[dim]✓ Network already exists: {network}[/dim]")

        except subprocess.CalledProcessError as e:
            console.print(
                f"[yellow]Warning: Failed to create network {network}: {e}[/yellow]"
            )


def _deploy_compose_stack(
    compose_path: Path, compose_file: str, services: Optional[List[str]], detach: bool
) -> None:
    """Deploy a specific compose stack"""

    # Use absolute path for compose file to avoid cwd issues
    compose_file_path = (compose_path / compose_file).resolve()
    if not compose_file_path.exists():
        return

    cmd = ["docker", "compose", "-f", str(compose_file_path), "up"]

    if detach:
        cmd.append("-d")

    if services:
        cmd.extend(services)

    try:
        result = subprocess.run(
            cmd, cwd=compose_path, capture_output=True, text=True, check=True
        )
        console.print(f"[dim]✓ Deployed {compose_file}[/dim]")

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or "Unknown error"
        console.print(
            f"[yellow]Warning: Failed to deploy {compose_file}: {error_msg[:100]}...[/yellow]"
        )


def _wait_for_services(config: Config, timeout: int) -> None:
    """Wait for services to become healthy"""

    console.print("[dim]Waiting for services to become ready...[/dim]")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check Docker containers are running
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\\t{{.Status}}"],
                capture_output=True,
                text=True,
                check=True,
            )

            running_containers = []
            for line in result.stdout.strip().split("\n"):
                if line and "Up" in line:
                    name = line.split("\t")[0]
                    running_containers.append(name)

            # Check if key services are running
            required_services = ["traefik"]
            
            if isinstance(config, LabConfig):
                # V2 Config
                enabled_services = config.get_enabled_services()
                if "gitlab" in enabled_services:
                    required_services.append("gitlab")
                if "monitoring" in enabled_services:
                    required_services.extend(["prometheus", "grafana"])
                if "postgresql" in enabled_services:
                    required_services.append("postgres") # Container name is usually postgres or postgresql
                if "vaultwarden" in enabled_services:
                    required_services.append("vaultwarden")
            else:
                # Legacy Config
                if config.gitlab.enabled or config.ci_cd.gitlab:
                    required_services.append("gitlab")
                if config.monitoring.enabled:
                    required_services.extend(["prometheus", "grafana"])
                if config.databases.postgresql:
                    required_services.append("postgres")
                if config.passwords.vaultwarden:
                    required_services.append("vaultwarden")

            all_running = True
            for service in required_services:
                # Check partial match because container names might have prefixes/suffixes
                if not any(service in container for container in running_containers):
                    all_running = False
                    break

            if all_running:
                console.print("[green]✓ All core services are running![/green]")
                return

            time.sleep(10)

        except Exception:
            time.sleep(10)

    console.print(
        f"[yellow]⚠️ Some services may still be starting after {timeout}s[/yellow]"
    )


def _show_deployment_info(config: Config, compose_path: Path) -> None:
    """Show deployment information and next steps"""

    console.print("\n[bold]🌐 Service Access URLs:[/bold]")

    urls = config.get_service_urls()
    for service, url in urls.items():
        console.print(f"  • {service.title()}: {url}")

    console.print(f"\n[bold]📁 Management:[/bold]")
    console.print(f"  • Check status: [cyan]labctl status[/cyan]")
    console.print(f"  • View logs: [cyan]labctl logs[/cyan]")
    console.print(f"  • Stop services: [cyan]labctl stop[/cyan]")

    console.print(f"\n[bold]📋 Docker Commands:[/bold]")
    console.print(f"  • View containers: [cyan]docker ps[/cyan]")
    console.print(
        f"  • Follow logs: [cyan]docker compose -f {compose_path}/docker-compose.yml logs -f[/cyan]"
    )

    console.print(
        f"\n[dim]💡 Services may take a few minutes to fully initialize[/dim]"
    )
