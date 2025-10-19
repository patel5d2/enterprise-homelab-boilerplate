"""
Configuration management for Home Lab CLI
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import json
from pydantic import BaseModel, Field, validator


class CoreConfig(BaseModel):
    """Core system configuration"""
    domain: str = Field(..., description="Primary domain for the home lab")
    email: str = Field(..., description="Admin email address")
    timezone: str = Field(default="UTC", description="System timezone")


class ReverseProxyConfig(BaseModel):
    """Reverse proxy configuration"""
    provider: str = Field(default="traefik", description="Reverse proxy provider")
    ssl_provider: str = Field(default="letsencrypt", description="SSL certificate provider")
    staging: bool = Field(default=False, description="Use Let's Encrypt staging")


class MonitoringConfig(BaseModel):
    """Monitoring stack configuration"""
    enabled: bool = Field(default=True, description="Enable monitoring stack")
    retention: str = Field(default="30d", description="Metrics retention period")
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    grafana_port: int = Field(default=3000, description="Grafana port")


class GitLabConfig(BaseModel):
    """GitLab Enterprise configuration"""
    enabled: bool = Field(default=False, description="Enable GitLab Enterprise")
    runners: int = Field(default=3, description="Number of GitLab runners")
    registry: bool = Field(default=True, description="Enable container registry")
    pages: bool = Field(default=True, description="Enable GitLab Pages")


class SecurityConfig(BaseModel):
    """Security configuration"""
    enabled: bool = Field(default=True, description="Enable security features")
    vulnerability_scanning: bool = Field(default=True, description="Enable vulnerability scanning")
    compliance_reporting: bool = Field(default=True, description="Enable compliance reporting")


class VaultConfig(BaseModel):
    """HashiCorp Vault configuration"""
    enabled: bool = Field(default=False, description="Enable Vault")
    auto_unseal: bool = Field(default=True, description="Enable auto-unseal")
    ui_enabled: bool = Field(default=True, description="Enable Vault UI")


class NetworkingConfig(BaseModel):
    """Networking services configuration"""
    cloudflared: bool = Field(default=False, description="Enable Cloudflared tunnel")
    headscale: bool = Field(default=False, description="Enable Headscale (Tailscale controller)")
    pihole: bool = Field(default=False, description="Enable Pi-hole DNS")
    

class DatabaseConfig(BaseModel):
    """Database services configuration"""
    postgresql: bool = Field(default=True, description="Enable PostgreSQL")
    mongodb: bool = Field(default=False, description="Enable MongoDB")
    redis: bool = Field(default=True, description="Enable Redis")


class BackupConfig(BaseModel):
    """Backup services configuration"""
    enabled: bool = Field(default=False, description="Enable backup services")
    backrest: bool = Field(default=False, description="Enable Backrest for PostgreSQL")
    restic: bool = Field(default=False, description="Enable Restic for file backups")
    s3_endpoint: str = Field(default="", description="S3-compatible storage endpoint")
    

class PasswordManagerConfig(BaseModel):
    """Password manager configuration"""
    vaultwarden: bool = Field(default=False, description="Enable Vaultwarden (Bitwarden)")
    

class DashboardConfig(BaseModel):
    """Dashboard and monitoring services"""
    glance: bool = Field(default=False, description="Enable Glance dashboard")
    uptime_kuma: bool = Field(default=False, description="Enable Uptime Kuma monitoring")
    

class DocumentationConfig(BaseModel):
    """Documentation services"""
    fumadocs: bool = Field(default=False, description="Enable Fumadocs documentation")
    

class AutomationConfig(BaseModel):
    """Automation and workflow services"""
    n8n: bool = Field(default=False, description="Enable n8n workflow automation")
    

class CIConfig(BaseModel):
    """CI/CD services configuration"""
    gitlab: bool = Field(default=False, description="Enable GitLab")
    jenkins: bool = Field(default=False, description="Enable Jenkins")
    

class ProxyConfig(BaseModel):
    """Proxy services configuration"""
    traefik: bool = Field(default=True, description="Enable Traefik")
    nginx_proxy_manager: bool = Field(default=False, description="Enable Nginx Proxy Manager")
    caddy: bool = Field(default=False, description="Enable Caddy")


class CustomEnvironmentConfig(BaseModel):
    """Custom environment variables configuration for services"""
    # Dictionary mapping service names to their custom environment variables
    # Format: {"service_name": {"ENV_VAR_NAME": "value"}}
    variables: Dict[str, Dict[str, str]] = Field(default_factory=dict, description="Custom environment variables per service")
    
    def get_service_vars(self, service_name: str) -> Dict[str, str]:
        """Get custom environment variables for a specific service"""
        return self.variables.get(service_name, {})
    
    def set_service_vars(self, service_name: str, env_vars: Dict[str, str]) -> None:
        """Set custom environment variables for a specific service"""
        if env_vars:  # Only set if there are actual variables
            self.variables[service_name] = env_vars
    
    def has_custom_vars(self, service_name: str) -> bool:
        """Check if a service has custom environment variables"""
        return service_name in self.variables and bool(self.variables[service_name])


class Config(BaseModel):
    """Main configuration class"""
    core: CoreConfig
    reverse_proxy: ReverseProxyConfig = ReverseProxyConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    gitlab: GitLabConfig = GitLabConfig()
    security: SecurityConfig = SecurityConfig()
    vault: VaultConfig = VaultConfig()
    
    # Infrastructure services
    networking: NetworkingConfig = NetworkingConfig()
    databases: DatabaseConfig = DatabaseConfig()
    backups: BackupConfig = BackupConfig()
    passwords: PasswordManagerConfig = PasswordManagerConfig()
    dashboards: DashboardConfig = DashboardConfig()
    documentation: DocumentationConfig = DocumentationConfig()
    automation: AutomationConfig = AutomationConfig()
    ci_cd: CIConfig = CIConfig()
    proxy: ProxyConfig = ProxyConfig()
    
    # Custom environment variables
    custom_env: CustomEnvironmentConfig = CustomEnvironmentConfig()

    @classmethod
    def load_from_file(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(
                self.dict(), 
                f, 
                default_flow_style=False, 
                indent=2,
                sort_keys=False
            )

    def validate_requirements(self) -> List[str]:
        """Validate configuration and return warnings"""
        warnings = []
        
        # Check domain format
        if not self.core.domain or '.' not in self.core.domain:
            warnings.append("Domain should be a valid FQDN (e.g., homelab.example.com)")
        
        # Check email format
        if not self.core.email or '@' not in self.core.email:
            warnings.append("Email should be a valid email address")
        
        # GitLab runner count
        if self.gitlab.enabled and self.gitlab.runners < 1:
            warnings.append("GitLab runners should be at least 1")
        
        return warnings

    def get_service_urls(self) -> Dict[str, str]:
        """Get service URLs based on domain"""
        base_domain = self.core.domain
        urls = {
            "traefik": f"https://traefik.{base_domain}",
            "gitlab": f"https://gitlab.{base_domain}",
            "grafana": f"https://grafana.{base_domain}",
            "prometheus": f"https://prometheus.{base_domain}",
            "vault": f"https://vault.{base_domain}",
        }
        
        # Add URLs for enabled services
        if self.networking.pihole:
            urls["pihole"] = f"https://pihole.{base_domain}"
        if self.networking.headscale:
            urls["headscale"] = f"https://headscale.{base_domain}"
        if self.passwords.vaultwarden:
            urls["vaultwarden"] = f"https://vault.{base_domain}"
        if self.dashboards.glance:
            urls["glance"] = f"https://dashboard.{base_domain}"
        if self.dashboards.uptime_kuma:
            urls["uptime"] = f"https://uptime.{base_domain}"
        if self.documentation.fumadocs:
            urls["docs"] = f"https://docs.{base_domain}"
        if self.automation.n8n:
            urls["n8n"] = f"https://automation.{base_domain}"
        if self.ci_cd.jenkins:
            urls["jenkins"] = f"https://jenkins.{base_domain}"
        if self.proxy.nginx_proxy_manager:
            urls["npm"] = f"https://proxy.{base_domain}"
            
        return urls
