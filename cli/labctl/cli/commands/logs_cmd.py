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
    tail: int = 100
) -> None:
    """View service logs"""
    
    config_path = Path(config_file)
    if not config_path.exists():
        raise HomeLabError(f"Configuration file not found: {config_file}")
    
    # Load configuration
    config = Config.load_from_file(config_path)
    
    # Set compose directory
    if compose_dir:
        compose_path = Path(compose_dir)
    else:
        compose_path = config_path.parent / "compose"
    
    if not compose_path.exists():
        console.print("[yellow]Compose directory not found. Have you built the project yet?[/yellow]")
        console.print("Run: [cyan]labctl build[/cyan] first")
        return
    
    # Find compose files to use
    compose_files = [
        "docker-compose.yml",
        "docker-compose.optional.yml",
        "docker-compose.monitoring.yml", 
        "docker-compose.security.yml"
    ]
    
    existing_files = [
        f for f in compose_files 
        if (compose_path / f).exists()
    ]
    
    if not existing_files:
        console.print("[yellow]No compose files found[/yellow]")
        console.print("Run: [cyan]labctl build[/cyan] to generate compose files")
        return
    
    try:
        # Build docker compose logs command
        cmd = ["docker", "compose"]
        
        # Add compose files
        for f in existing_files:
            cmd.extend(["-f", str(compose_path / f)])
        
        cmd.append("logs")
        
        if follow:
            cmd.append("-f")
        
        if tail > 0:
            cmd.extend(["--tail", str(tail)])
        
        # Add specific services if requested
        if services:
            cmd.extend(services)
        
        service_list = services if services else "all services"
        console.print(f"[dim]Viewing logs for {service_list}[/dim]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")
        
        # Run the command directly (not capturing output)
        subprocess.run(cmd, cwd=compose_path)
        
    except subprocess.CalledProcessError as e:
        raise HomeLabError(f"Failed to view logs: {e}")
    except KeyboardInterrupt:
        console.print("\n[yellow]Log viewing interrupted[/yellow]")