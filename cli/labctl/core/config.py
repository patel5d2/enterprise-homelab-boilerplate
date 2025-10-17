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


class Config(BaseModel):
    """Main configuration class"""
    core: CoreConfig
    reverse_proxy: ReverseProxyConfig = ReverseProxyConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    gitlab: GitLabConfig = GitLabConfig()
    security: SecurityConfig = SecurityConfig()
    vault: VaultConfig = VaultConfig()

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
        return {
            "traefik": f"https://traefik.{base_domain}",
            "gitlab": f"https://gitlab.{base_domain}",
            "grafana": f"https://grafana.{base_domain}",
            "prometheus": f"https://prometheus.{base_domain}",
            "vault": f"https://vault.{base_domain}",
        }