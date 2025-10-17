"""
Stop command - stop services and cleanup resources
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress

from ...core.config import Config
from ...core.exceptions import HomeLabError

console = Console()


def run(
    config_file: str,
    services: Optional[List[str]] = None,
    compose_dir: Optional[str] = None,
    remove_volumes: bool = False,
    remove_images: bool = False
) -> None:
    """Stop services and optionally cleanup resources"""
    
    console.print("🛑 [bold]Stopping Home Lab Services[/bold]")
    
    # Look for docker-compose.yml
    compose_file = Path("docker-compose.yml")
    if not compose_file.exists():
        if compose_dir:
            compose_file = Path(compose_dir) / "docker-compose.yml"
        else:
            compose_file = Path("compose/docker-compose.yml")
    
    if not compose_file.exists():
        console.print("[yellow]Docker Compose file not found[/yellow]")
        return
    
    try:
        with Progress() as progress:
            stop_task = progress.add_task("Stopping services...", total=100)
            
            # Stop services
            progress.update(stop_task, description="Stopping containers...")
            _stop_services(compose_file, services)
            progress.update(stop_task, advance=50)
            
            # Remove volumes if requested
            if remove_volumes:
                progress.update(stop_task, description="Removing volumes...")
                _remove_volumes(compose_file)
                progress.update(stop_task, advance=30)
            
            # Remove images if requested
            if remove_images:
                progress.update(stop_task, description="Removing unused images...")
                _cleanup_images()
                progress.update(stop_task, advance=20)
            
        console.print(f"\n[green]✅ Services stopped successfully[/green]")
        
        if remove_volumes:
            console.print("[yellow]⚠️  Volumes have been removed - data may be lost[/yellow]")
        
    except Exception as e:
        raise HomeLabError(f"Failed to stop services: {str(e)}")


def _stop_services(compose_file: Path, services: Optional[List[str]]) -> None:
    """Stop Docker Compose services"""
    
    cmd = ["docker", "compose", "-f", str(compose_file), "down"]
    
    # Add specific services if provided
    if services:
        cmd.extend(services)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=compose_file.parent if compose_file.parent.name != '.' else Path.cwd(),
            capture_output=True,
            text=True,
            check=True
        )
        
        if services:
            console.print(f"[green]✓ Stopped services: {', '.join(services)}[/green]")
        else:
            console.print("[green]✓ Stopped all services[/green]")
            
    except subprocess.CalledProcessError as e:
        error_output = e.stderr or e.stdout or "Unknown error"
        console.print(f"[red]Failed to stop services: {error_output}[/red]")
        raise


def _remove_volumes(compose_file: Path) -> None:
    """Remove volumes associated with the compose file"""
    
    cmd = ["docker", "compose", "-f", str(compose_file), "down", "-v"]
    
    try:
        subprocess.run(
            cmd,
            cwd=compose_file.parent if compose_file.parent.name != '.' else Path.cwd(),
            capture_output=True,
            text=True,
            check=True
        )
        console.print("[green]✓ Removed volumes[/green]")
        
    except subprocess.CalledProcessError as e:
        error_output = e.stderr or e.stdout or "Unknown error"
        console.print(f"[yellow]Warning: Failed to remove volumes: {error_output}[/yellow]")


def _cleanup_images() -> None:
    """Remove unused Docker images"""
    
    try:
        subprocess.run(
            ["docker", "image", "prune", "-f"],
            capture_output=True,
            text=True,
            check=True
        )
        console.print("[green]✓ Cleaned up unused images[/green]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[yellow]Warning: Failed to cleanup images: {e}[/yellow]")
