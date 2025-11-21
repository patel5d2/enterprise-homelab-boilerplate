"""
Logs command - view and manage service logs
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from ...core.config import Config
from ...core.exceptions import HomeLabError

console = Console()


def run(
    config_file: str,
    services: Optional[List[str]] = None,
    compose_dir: Optional[str] = None,
    follow: bool = False,
    tail: int = 100,
) -> None:
    """View service logs"""

    console.print("📋 [bold]Service Logs[/bold]")

    # Look for docker-compose.yml in current directory first
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        if compose_dir:
            compose_file = Path(compose_dir) / "docker-compose.yml"
        else:
            # Try compose subdirectory
            compose_file = Path("compose/docker-compose.yml")

    if not compose_file.exists():
        console.print("[yellow]Docker Compose file not found[/yellow]")
        console.print("Run: [cyan]labctl build[/cyan] to generate compose files")
        return

    try:
        # Build docker compose logs command
        cmd = ["docker", "compose", "-f", str(compose_file), "logs"]

        if follow:
            cmd.append("-f")

        if tail > 0:
            cmd.extend(["--tail", str(tail)])

        # Add specific services if requested
        if services:
            cmd.extend(services)

        service_list = ", ".join(services) if services else "all services"
        console.print(f"[dim]Viewing logs for {service_list}[/dim]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        # Run the command directly (not capturing output)
        subprocess.run(
            cmd,
            cwd=compose_file.parent if compose_file.parent.name != "." else Path.cwd(),
        )

    except subprocess.CalledProcessError as e:
        raise HomeLabError(f"Failed to view logs: {e}")
    except KeyboardInterrupt:
        console.print("\n[yellow]Log viewing interrupted[/yellow]")
