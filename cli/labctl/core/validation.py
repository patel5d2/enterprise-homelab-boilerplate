"""
Input validation and preflight checks for Home Lab configurations
"""

import re
import ipaddress
import socket
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .config import LabConfig, BaseServiceConfig

console = Console()


class ValidationError(Exception):
    """Configuration validation error"""
    def __init__(self, message: str, field: str = "", service: str = ""):
        self.message = message
        self.field = field
        self.service = service
        super().__init__(message)


class ValidationWarning:
    """Configuration validation warning"""
    def __init__(self, message: str, field: str = "", service: str = ""):
        self.message = message
        self.field = field
        self.service = service


class ConfigurationValidator:
    """Comprehensive configuration validator"""
    
    def __init__(self, config: LabConfig):
        self.config = config
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationWarning] = []
    
    def validate_all(self) -> Tuple[List[ValidationError], List[ValidationWarning]]:
        """Run all validation checks"""
        self.errors.clear()
        self.warnings.clear()
        
        try:
            # Core validation
            self._validate_core_config()
            
            # Service-specific validation
            self._validate_services()
            
            # Cross-service validation
            self._validate_service_interactions()
            
            # Infrastructure validation
            self._validate_infrastructure()
            
        except Exception as e:
            self.errors.append(ValidationError(f"Validation process failed: {e}"))
        
        return self.errors, self.warnings
    
    def _validate_core_config(self):
        """Validate core configuration settings"""
        core = self.config.core
        
        # Domain validation
        if not self._is_valid_domain(core.domain):
            self.errors.append(ValidationError(
                f"Invalid domain format: '{core.domain}'. Expected format: example.com or subdomain.example.com",
                field="domain"
            ))
        elif core.domain.endswith('.local') and self.config.profile == 'prod':
            self.warnings.append(ValidationWarning(
                "Using .local domain in production profile. Consider using a real domain for production deployment.",
                field="domain"
            ))
        
        # Email validation
        if not self._is_valid_email(core.email):
            self.errors.append(ValidationError(
                f"Invalid email format: '{core.email}'",
                field="email"
            ))
        
        # Timezone validation
        if hasattr(core, 'timezone') and core.timezone:
            if not self._is_valid_timezone(core.timezone):
                self.warnings.append(ValidationWarning(
                    f"Timezone '{core.timezone}' may not be valid. Use formats like 'UTC', 'America/New_York'",
                    field="timezone"
                ))
    
    def _validate_services(self):
        """Validate individual service configurations"""
        enabled_services = self.config.get_enabled_services()
        
        for service_id, service_config in enabled_services.items():
            try:
                self._validate_service(service_id, service_config)
            except Exception as e:
                self.errors.append(ValidationError(
                    f"Failed to validate {service_id}: {e}",
                    service=service_id
                ))
    
    def _validate_service(self, service_id: str, service_config: BaseServiceConfig):
        """Validate a single service configuration"""
        
        # Port validation
        if hasattr(service_config, 'port') and service_config.port:
            if not self._is_valid_port(service_config.port):
                self.errors.append(ValidationError(
                    f"Invalid port {service_config.port}. Must be between 1 and 65535",
                    field="port",
                    service=service_id
                ))
            elif service_config.port < 1024 and self.config.profile == 'dev':
                self.warnings.append(ValidationWarning(
                    f"Using privileged port {service_config.port} in development. Consider using port > 1024",
                    field="port",
                    service=service_id
                ))
        
        # Service-specific validation
        if service_id == 'traefik':
            self._validate_traefik(service_config)
        elif service_id == 'postgresql':
            self._validate_postgresql(service_config)
        elif service_id == 'redis':
            self._validate_redis(service_config)
        elif service_id == 'nextcloud':
            self._validate_nextcloud(service_config)
        elif service_id == 'pihole':
            self._validate_pihole(service_config)
        elif service_id == 'vaultwarden':
            self._validate_vaultwarden(service_config)
        elif service_id == 'gitlab':
            self._validate_gitlab(service_config)
    
    def _validate_traefik(self, config):
        """Validate Traefik configuration"""
        if hasattr(config, 'domain') and config.domain:
            if not self._is_valid_domain(config.domain):
                self.errors.append(ValidationError(
                    f"Invalid Traefik domain: '{config.domain}'",
                    field="domain",
                    service="traefik"
                ))
        
        if hasattr(config, 'email') and config.email:
            if not self._is_valid_email(config.email):
                self.errors.append(ValidationError(
                    f"Invalid Traefik email: '{config.email}'",
                    field="email",
                    service="traefik"
                ))
        
        if hasattr(config, 'acme_environment'):
            if config.acme_environment not in ['staging', 'production']:
                self.errors.append(ValidationError(
                    f"Invalid ACME environment: '{config.acme_environment}'. Must be 'staging' or 'production'",
                    field="acme_environment",
                    service="traefik"
                ))
            elif config.acme_environment == 'staging' and self.config.profile == 'prod':
                self.warnings.append(ValidationWarning(
                    "Using ACME staging environment in production profile",
                    field="acme_environment",
                    service="traefik"
                ))
    
    def _validate_postgresql(self, config):
        """Validate PostgreSQL configuration"""
        if hasattr(config, 'max_connections') and config.max_connections:
            if config.max_connections < 10 or config.max_connections > 1000:
                self.warnings.append(ValidationWarning(
                    f"PostgreSQL max_connections ({config.max_connections}) outside recommended range 10-1000",
                    field="max_connections",
                    service="postgresql"
                ))
        
        if hasattr(config, 'shared_buffers') and config.shared_buffers:
            if not re.match(r'^\d+(MB|GB)$', config.shared_buffers):
                self.errors.append(ValidationError(
                    f"Invalid shared_buffers format: '{config.shared_buffers}'. Use format like '128MB' or '1GB'",
                    field="shared_buffers",
                    service="postgresql"
                ))
    
    def _validate_redis(self, config):
        """Validate Redis configuration"""
        if hasattr(config, 'persistence'):
            if config.persistence not in ['rdb', 'aof', 'both', 'none']:
                self.errors.append(ValidationError(
                    f"Invalid Redis persistence mode: '{config.persistence}'. Must be 'rdb', 'aof', 'both', or 'none'",
                    field="persistence",
                    service="redis"
                ))
        
        if hasattr(config, 'maxmemory') and config.maxmemory:
            if not re.match(r'^\d+(mb|gb)$', config.maxmemory.lower()):
                self.errors.append(ValidationError(
                    f"Invalid Redis maxmemory format: '{config.maxmemory}'. Use format like '256mb' or '1gb'",
                    field="maxmemory",
                    service="redis"
                ))
    
    def _validate_nextcloud(self, config):
        """Validate Nextcloud configuration"""
        if hasattr(config, 'upload_max_filesize') and config.upload_max_filesize:
            if not re.match(r'^\d+(M|G)$', config.upload_max_filesize):
                self.errors.append(ValidationError(
                    f"Invalid upload_max_filesize format: '{config.upload_max_filesize}'. Use format like '2G' or '512M'",
                    field="upload_max_filesize",
                    service="nextcloud"
                ))
        
        if hasattr(config, 'memory_limit') and config.memory_limit:
            if not re.match(r'^\d+(M|G)$', config.memory_limit):
                self.errors.append(ValidationError(
                    f"Invalid memory_limit format: '{config.memory_limit}'. Use format like '512M' or '1G'",
                    field="memory_limit",
                    service="nextcloud"
                ))
    
    def _validate_pihole(self, config):
        """Validate Pi-hole configuration"""
        if hasattr(config, 'upstream_dns') and config.upstream_dns:
            for dns in config.upstream_dns:
                if not self._is_valid_ip_or_domain(dns):
                    self.errors.append(ValidationError(
                        f"Invalid upstream DNS server: '{dns}'. Must be IP address or domain",
                        field="upstream_dns",
                        service="pihole"
                    ))
        
        if hasattr(config, 'server_ip') and config.server_ip:
            if not self._is_valid_ip(config.server_ip):
                self.errors.append(ValidationError(
                    f"Invalid server IP address: '{config.server_ip}'",
                    field="server_ip",
                    service="pihole"
                ))
        
        if hasattr(config, 'dns_port') and config.dns_port and config.dns_port != 53:
            self.warnings.append(ValidationWarning(
                f"Using non-standard DNS port {config.dns_port}. Standard DNS port is 53",
                field="dns_port",
                service="pihole"
            ))
    
    def _validate_vaultwarden(self, config):
        """Validate Vaultwarden configuration"""
        if hasattr(config, 'smtp_host') and config.smtp_host:
            if not self._is_valid_domain(config.smtp_host) and not self._is_valid_ip(config.smtp_host):
                self.errors.append(ValidationError(
                    f"Invalid SMTP host: '{config.smtp_host}'. Must be domain or IP address",
                    field="smtp_host",
                    service="vaultwarden"
                ))
        
        if hasattr(config, 'smtp_port') and config.smtp_port:
            common_smtp_ports = [25, 465, 587, 2525]
            if config.smtp_port not in common_smtp_ports:
                self.warnings.append(ValidationWarning(
                    f"Unusual SMTP port {config.smtp_port}. Common ports: {common_smtp_ports}",
                    field="smtp_port",
                    service="vaultwarden"
                ))
    
    def _validate_gitlab(self, config):
        """Validate GitLab configuration"""
        if hasattr(config, 'external_url') and config.external_url:
            if not self._is_valid_url(config.external_url):
                self.errors.append(ValidationError(
                    f"Invalid GitLab external URL: '{config.external_url}'",
                    field="external_url",
                    service="gitlab"
                ))
        
        if hasattr(config, 'ldap_enabled') and config.ldap_enabled:
            if hasattr(config, 'ldap_host') and not config.ldap_host:
                self.errors.append(ValidationError(
                    "LDAP host is required when LDAP is enabled",
                    field="ldap_host",
                    service="gitlab"
                ))
            elif hasattr(config, 'ldap_host') and config.ldap_host:
                if not self._is_valid_ldap_url(config.ldap_host):
                    self.errors.append(ValidationError(
                        f"Invalid LDAP URL: '{config.ldap_host}'. Expected format: ldap://host:port or ldaps://host:port",
                        field="ldap_host",
                        service="gitlab"
                    ))
    
    def _validate_service_interactions(self):
        """Validate interactions between services"""
        enabled_services = self.config.get_enabled_services()
        
        # Port conflict detection
        self._check_port_conflicts(enabled_services)
        
        # Dependency validation
        self._check_dependencies(enabled_services)
        
        # Resource validation
        self._check_resource_requirements(enabled_services)
    
    def _check_port_conflicts(self, services: Dict[str, BaseServiceConfig]):
        """Check for port conflicts between services"""
        port_usage: Dict[int, List[str]] = {}
        
        for service_id, config in services.items():
            ports = []
            
            # Collect all ports used by this service
            if hasattr(config, 'port') and config.port:
                ports.append(config.port)
            if hasattr(config, 'web_port') and config.web_port:
                ports.append(config.web_port)
            if hasattr(config, 'http_port') and config.http_port:
                ports.append(config.http_port)
            if hasattr(config, 'external_port') and config.external_port:
                ports.append(config.external_port)
            if hasattr(config, 'dns_port') and config.dns_port:
                ports.append(config.dns_port)
            
            for port in ports:
                if port not in port_usage:
                    port_usage[port] = []
                port_usage[port].append(service_id)
        
        # Report conflicts
        for port, service_list in port_usage.items():
            if len(service_list) > 1:
                self.errors.append(ValidationError(
                    f"Port {port} conflict: used by services {', '.join(service_list)}"
                ))
    
    def _check_dependencies(self, services: Dict[str, BaseServiceConfig]):
        """Check service dependencies are satisfied"""
        service_ids = set(services.keys())
        
        # Common dependency mappings
        dependencies = {
            'nextcloud': ['postgresql', 'redis'],
            'gitlab': ['postgresql', 'redis'],
            'monitoring': [],  # Prometheus + Grafana stack is self-contained
            'vaultwarden': [],
            'pihole': []
        }
        
        for service_id, required_deps in dependencies.items():
            if service_id in service_ids:
                missing_deps = [dep for dep in required_deps if dep not in service_ids]
                if missing_deps:
                    self.errors.append(ValidationError(
                        f"Service '{service_id}' requires dependencies: {', '.join(missing_deps)}",
                        service=service_id
                    ))
    
    def _check_resource_requirements(self, services: Dict[str, BaseServiceConfig]):
        """Check resource requirements and warnings"""
        heavy_services = ['gitlab', 'nextcloud', 'monitoring']
        enabled_heavy = [s for s in heavy_services if s in services]
        
        if len(enabled_heavy) > 2:
            self.warnings.append(ValidationWarning(
                f"Multiple resource-intensive services enabled: {', '.join(enabled_heavy)}. "
                "Ensure adequate RAM (8GB+ recommended) and CPU resources."
            ))
    
    def _validate_infrastructure(self):
        """Validate infrastructure and system requirements"""
        # Check if Docker is available (basic check)
        try:
            import subprocess
            result = subprocess.run(['which', 'docker'], capture_output=True, text=True)
            if result.returncode != 0:
                self.warnings.append(ValidationWarning(
                    "Docker not found in PATH. Ensure Docker is installed and running."
                ))
        except Exception:
            pass  # Skip if subprocess not available
        
        # Storage path validation
        self._validate_storage_paths()
    
    def _validate_storage_paths(self):
        """Validate storage paths exist or can be created"""
        common_paths = [
            Path('./data'),
            Path('./ssl'),
            Path('./backups'),
            Path('./logs')
        ]
        
        for path in common_paths:
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    path.rmdir()  # Clean up test directory
                except PermissionError:
                    self.warnings.append(ValidationWarning(
                        f"Cannot create directory {path}. Check permissions."
                    ))
                except Exception as e:
                    self.warnings.append(ValidationWarning(
                        f"Storage path issue for {path}: {e}"
                    ))
    
    # Utility validation methods
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain name format"""
        if not domain or len(domain) > 253:
            return False
        
        # Basic domain regex
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        return bool(re.match(pattern, domain))
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _is_valid_port(self, port: int) -> bool:
        """Validate port number"""
        return isinstance(port, int) and 1 <= port <= 65535
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _is_valid_ip_or_domain(self, value: str) -> bool:
        """Validate IP address or domain name"""
        return self._is_valid_ip(value) or self._is_valid_domain(value)
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    def _is_valid_ldap_url(self, url: str) -> bool:
        """Validate LDAP URL format"""
        try:
            result = urlparse(url)
            return result.scheme in ['ldap', 'ldaps'] and result.netloc
        except Exception:
            return False
    
    def _is_valid_timezone(self, tz: str) -> bool:
        """Validate timezone string"""
        try:
            import zoneinfo
            zoneinfo.ZoneInfo(tz)
            return True
        except Exception:
            # Fallback check for common formats
            common_timezones = ['UTC', 'GMT', 'EST', 'PST', 'CET']
            return tz in common_timezones or '/' in tz


def validate_configuration(config: LabConfig, show_results: bool = True) -> Tuple[List[ValidationError], List[ValidationWarning]]:
    """
    Validate a configuration and optionally display results
    
    Args:
        config: Configuration to validate
        show_results: Whether to display validation results
        
    Returns:
        Tuple of (errors, warnings)
    """
    validator = ConfigurationValidator(config)
    errors, warnings = validator.validate_all()
    
    if show_results:
        display_validation_results(errors, warnings)
    
    return errors, warnings


def display_validation_results(errors: List[ValidationError], warnings: List[ValidationWarning]):
    """Display validation results in a formatted table"""
    
    if not errors and not warnings:
        console.print(Panel.fit(
            "[green]✅ Configuration validation passed![/green]\n"
            "No errors or warnings found.",
            border_style="green",
            title="Validation Results"
        ))
        return
    
    # Display summary
    error_count = len(errors)
    warning_count = len(warnings)
    
    if error_count > 0:
        console.print(f"\n[red]❌ Found {error_count} error(s)[/red]")
    if warning_count > 0:
        console.print(f"[yellow]⚠️  Found {warning_count} warning(s)[/yellow]")
    
    # Display errors
    if errors:
        console.print("\n[bold red]Errors:[/bold red]")
        error_table = Table(show_header=True, header_style="bold red")
        error_table.add_column("Service", style="cyan", width=15)
        error_table.add_column("Field", style="magenta", width=15) 
        error_table.add_column("Message", style="white")
        
        for error in errors:
            error_table.add_row(
                error.service or "-",
                error.field or "-", 
                error.message
            )
        console.print(error_table)
    
    # Display warnings
    if warnings:
        console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
        warning_table = Table(show_header=True, header_style="bold yellow")
        warning_table.add_column("Service", style="cyan", width=15)
        warning_table.add_column("Field", style="magenta", width=15)
        warning_table.add_column("Message", style="white")
        
        for warning in warnings:
            warning_table.add_row(
                warning.service or "-",
                warning.field or "-",
                warning.message
            )
        console.print(warning_table)
    
    # Display recommendation
    if errors:
        console.print(f"\n[red]❌ Configuration has {error_count} error(s) that must be fixed before deployment.[/red]")
    elif warnings:
        console.print(f"\n[yellow]⚠️  Configuration has {warning_count} warning(s). Review before production use.[/yellow]")


def run_preflight_checks(config: LabConfig) -> bool:
    """
    Run preflight checks before deployment
    
    Args:
        config: Configuration to check
        
    Returns:
        True if all checks pass, False otherwise
    """
    console.print(Panel.fit(
        "🔍 [bold blue]Running Preflight Checks[/bold blue] 🔍\n"
        "Validating configuration before deployment...",
        border_style="blue"
    ))
    
    errors, warnings = validate_configuration(config, show_results=False)
    
    # Check system requirements
    console.print("\n[cyan]Checking system requirements...[/cyan]")
    
    # Additional system checks can be added here
    system_checks_passed = True
    
    # Display results
    display_validation_results(errors, warnings)
    
    if errors:
        console.print(f"\n[red]❌ Preflight checks failed with {len(errors)} error(s)[/red]")
        return False
    elif warnings:
        console.print(f"\n[yellow]⚠️  Preflight checks completed with {len(warnings)} warning(s)[/yellow]")
        console.print("[yellow]Review warnings before proceeding to production deployment.[/yellow]")
    else:
        console.print("\n[green]✅ All preflight checks passed![/green]")
    
    return system_checks_passed


if __name__ == "__main__":
    # Example usage for testing
    from .config import LabConfig, CoreConfig
    
    # Create a test configuration
    test_config = LabConfig(
        core=CoreConfig(domain="example.com", email="admin@example.com"),
        services={}
    )
    
    validate_configuration(test_config)