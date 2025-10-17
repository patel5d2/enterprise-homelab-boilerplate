"""
Status command - shows service status and health information
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...core.config import Config
from ...core.exceptions import HomeLabError
from ...core.health import HealthChecker

console = Console()


def run(
    config_file: str,
    services: Optional[List[str]] = None,
    compose_dir: Optional[str] = None,
    watch: bool = False
) -> None:
    """Show service status and health information"""
    
    console.print("📊 [bold]Home Lab Service Status[/bold]")
    
    if watch:
        console.print("[yellow]Watch mode not implemented yet[/yellow]")
        return
    
    try:
        # Get Docker status
        docker_status = _get_docker_status(None, services)
        
        # Display status information
        _display_service_status(docker_status, {})
        
        # Show basic system info
        _display_basic_info(config_file)
        
    except Exception as e:
        raise HomeLabError(f"Status check failed: {str(e)}")


def _get_docker_status(compose_path: Path, services: Optional[List[str]]) -> Dict:
    """Get Docker container status"""
    
    status = {}
    
    try:
        # Get all running containers with their status
        cmd = ["docker", "ps", "-a", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            import json
            # Parse JSON output (one JSON object per line)
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        container_info = json.loads(line)
                        name = container_info.get('Names', '')
                        
                        # Filter services if specified
                        if services and not any(service in name for service in services):
                            continue
                        
                        status[name] = {
                            'state': container_info.get('State', 'unknown'),
                            'status': container_info.get('Status', 'unknown'),
                            'image': container_info.get('Image', 'unknown'),
                            'ports': container_info.get('Ports', '')
                        }
                    except json.JSONDecodeError:
                        continue
    
    except subprocess.CalledProcessError:
        # If docker ps fails, try to show a helpful message
        console.print("[yellow]Could not get container status. Is Docker running?[/yellow]")
    
    return status


def _display_service_status(docker_status: Dict, health_status: Dict) -> None:
    """Display service status in a table"""
    
    if not docker_status:
        console.print("[yellow]No containers found. Have you deployed the services yet?[/yellow]")
        console.print("Run: [cyan]labctl deploy[/cyan] to deploy services")
        return
    
    table = Table(title="🐳 Container Status")
    table.add_column("Container", style="cyan")
    table.add_column("State", style="white")
    table.add_column("Status", style="white")
    table.add_column("Health", style="white")
    table.add_column("Image", style="dim")
    
    for container_name, info in docker_status.items():
        # Format state
        state = info.get('state', 'unknown')
        state_style = _get_state_style(state)
        
        # Format status
        status = info.get('status', 'unknown')
        
        # Format health (if available)
        health = 'unknown'
        health_style = 'dim'
        
        # Try to match container name to service name for health check
        service_name = container_name.lower()
        for key in ['traefik', 'gitlab', 'prometheus', 'grafana', 'vault']:
            if key in service_name:
                health_info = health_status.get(key, {})
                if health_info.get('healthy') is True:
                    health = '✅ healthy'
                    health_style = 'green'
                elif health_info.get('healthy') is False:
                    health = '❌ unhealthy'
                    health_style = 'red'
                break
        
        # Get image name (short version)
        image = info.get('image', 'unknown')
        if ':' in image:
            image = image.split(':')[0]  # Remove tag for brevity
        
        table.add_row(
            container_name,
            f"[{state_style}]{state}[/{state_style}]",
            status,
            f"[{health_style}]{health}[/{health_style}]",
            image
        )
    
    console.print(table)


def _display_basic_info(config_file: str) -> None:
    """Display basic system information"""
    
    info_items = []
    
    # Configuration file
    info_items.append(f"📄 Config File: {config_file}")
    
    # Docker info
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, check=True
        )
        docker_version = result.stdout.strip()
        info_items.append(f"🐳 Docker Version: {docker_version}")
    except Exception:
        info_items.append("🐳 Docker: Not available")
    
    # Docker Compose info
    try:
        result = subprocess.run(
            ["docker", "compose", "version", "--short"],
            capture_output=True, text=True, check=True
        )
        compose_version = result.stdout.strip()
        info_items.append(f"📦 Docker Compose: {compose_version}")
    except Exception:
        info_items.append("📦 Docker Compose: Not available")
    
    # Quick tips
    info_items.append("")
    info_items.append("💡 Quick Commands:")
    info_items.append("  • View logs: labctl logs")
    info_items.append("  • Stop services: labctl stop")
    info_items.append("  • Redeploy: labctl deploy")
    
    info_panel = Panel(
        "\n".join(info_items),
        title="⚙️ System Information",
        border_style="blue"
    )
    
    console.print(info_panel)


def _get_state_style(state: str) -> str:
    """Get Rich style for Docker container state"""
    
    state_styles = {
        'running': 'green',
        'exited': 'red',
        'paused': 'yellow',
        'restarting': 'yellow',
        'created': 'blue',
        'dead': 'red',
        'removing': 'yellow'
    }
    
    return state_styles.get(state.lower(), 'dim')