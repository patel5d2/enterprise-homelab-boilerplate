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
        console.print("[yellow]Compose directory not found[/yellow]")
        return
    
    # Find compose files
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
        return
    
    console.print("🛑 Stopping home lab services...")
    
    try:
        with Progress() as progress:
            task = progress.add_task("Stopping services...", total=len(existing_files))
            
            # Stop services in reverse order (security, monitoring, optional, core)
            for compose_file in reversed(existing_files):
                progress.update(task, description=f"Stopping {compose_file}...")
                _stop_compose_stack(compose_path, compose_file, services, remove_volumes)
                progress.update(task, advance=1)
            
            if remove_images:
                progress.update(task, description="Removing unused images...")
                _cleanup_images()
                
        console.print("\n[green]✅ Services stopped successfully![/green]")
        
        if remove_volumes:
            console.print("[yellow]⚠️ Volumes were removed - data may be lost[/yellow]")
        
        console.print("\n[dim]💡 Start services again with: labctl deploy[/dim]")
        
    except Exception as e:
        raise HomeLabError(f"Stop failed: {str(e)}")


def _stop_compose_stack(
    compose_path: Path,
    compose_file: str,
    services: Optional[List[str]],
    remove_volumes: bool
) -> None:
    """Stop a specific compose stack"""
    
    compose_file_path = compose_path / compose_file
    
    cmd = [
        "docker", "compose",
        "-f", str(compose_file_path),
        "down"
    ]
    
    if remove_volumes:
        cmd.append("--volumes")
    
    if services:
        # For specific services, use stop instead of down
        cmd = [
            "docker", "compose",
            "-f", str(compose_file_path),
            "stop"
        ]
        cmd.extend(services)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=compose_path,
            capture_output=True,
            text=True,
            check=True
        )
        console.print(f"[dim]✓ Stopped {compose_file}[/dim]")
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or "Unknown error"
        console.print(f"[yellow]Warning: Failed to stop {compose_file}: {error_msg[:50]}...[/yellow]")


def _cleanup_images() -> None:
    """Remove unused Docker images"""
    
    try:
        subprocess.run(
            ["docker", "image", "prune", "-f"],
            capture_output=True,
            text=True,
            check=True
        )
        console.print("[dim]✓ Cleaned up unused images[/dim]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[yellow]Warning: Failed to cleanup images: {e}[/yellow]")