"""
Configuration management for Home Lab CLI
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, model_validator, validator


class CoreConfig(BaseModel):
    """Core system configuration"""

    domain: str = Field(..., description="Primary domain for the home lab")
    email: str = Field(..., description="Admin email address")
    timezone: str = Field(default="UTC", description="System timezone")


class ReverseProxyConfig(BaseModel):
    """Reverse proxy configuration"""

    provider: str = Field(default="traefik", description="Reverse proxy provider")
    ssl_provider: str = Field(
        default="letsencrypt", description="SSL certificate provider"
    )
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
    vulnerability_scanning: bool = Field(
        default=True, description="Enable vulnerability scanning"
    )
    compliance_reporting: bool = Field(
        default=True, description="Enable compliance reporting"
    )


class VaultConfig(BaseModel):
    """HashiCorp Vault configuration"""

    enabled: bool = Field(default=False, description="Enable Vault")
    auto_unseal: bool = Field(default=True, description="Enable auto-unseal")
    ui_enabled: bool = Field(default=True, description="Enable Vault UI")


class NetworkingConfig(BaseModel):
    """Networking services configuration"""

    cloudflared: bool = Field(default=False, description="Enable Cloudflared tunnel")
    headscale: bool = Field(
        default=False, description="Enable Headscale (Tailscale controller)"
    )
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

    vaultwarden: bool = Field(
        default=False, description="Enable Vaultwarden (Bitwarden)"
    )


class DashboardConfig(BaseModel):
    """Dashboard and monitoring services"""

    glance: bool = Field(default=False, description="Enable Glance dashboard")
    uptime_kuma: bool = Field(
        default=False, description="Enable Uptime Kuma monitoring"
    )


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
    nginx_proxy_manager: bool = Field(
        default=False, description="Enable Nginx Proxy Manager"
    )
    caddy: bool = Field(default=False, description="Enable Caddy")


# === New V2 Configuration Models ===


class Profile(str, Enum):
    """Configuration profiles"""

    DEV = "dev"
    PROD = "prod"


class BaseServiceConfig(BaseModel):
    """Base configuration for all services"""

    enabled: bool = Field(default=False, description="Whether the service is enabled")
    custom_env: Dict[str, str] = Field(
        default_factory=dict, description="Custom environment variables"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Service dependencies"
    )
    healthcheck_enabled: bool = Field(default=True, description="Enable health checks")
    profile_overrides: Dict[str, Any] = Field(
        default_factory=dict, description="Profile-specific overrides"
    )


class TraefikConfig(BaseServiceConfig):
    """Traefik reverse proxy configuration"""

    enabled: bool = Field(default=True)  # Traefik is typically always enabled
    domain: str = Field(..., description="Primary domain")
    email: str = Field(..., description="Email for ACME certificates")
    acme_environment: str = Field(
        default="production", description="ACME environment (staging/production)"
    )
    dns_provider: str = Field(
        default="cloudflare", description="DNS provider for challenges"
    )
    dns_provider_type: str = Field(
        default="token", description="DNS provider auth type (token/global_key)"
    )
    wildcard_enabled: bool = Field(
        default=True, description="Enable wildcard certificates"
    )
    dashboard_enabled: bool = Field(
        default=True, description="Enable Traefik dashboard"
    )
    dashboard_username: str = Field(default="admin", description="Dashboard username")
    dashboard_auth_hash: Optional[str] = Field(
        default=None, description="Dashboard auth hash"
    )
    hsts_enabled: bool = Field(default=True, description="Enable HSTS headers")
    https_redirect: bool = Field(default=True, description="Force HTTPS redirects")
    ipv6_enabled: bool = Field(default=False, description="Enable IPv6 support")


class PostgresConfig(BaseServiceConfig):
    """PostgreSQL database configuration"""

    port: int = Field(default=5432, description="PostgreSQL port", ge=1, le=65535)
    superuser: str = Field(default="postgres", description="Superuser username")
    databases: List[str] = Field(
        default_factory=list, description="Additional databases to create"
    )
    max_connections: int = Field(
        default=100, description="Maximum connections", ge=10, le=1000
    )
    shared_buffers: str = Field(default="128MB", description="Shared buffers setting")
    backup_enabled: bool = Field(default=True, description="Enable automated backups")
    backup_schedule: str = Field(
        default="0 2 * * *", description="Backup cron schedule"
    )


class RedisConfig(BaseServiceConfig):
    """Redis configuration"""

    port: int = Field(default=6379, description="Redis port", ge=1, le=65535)
    persistence: str = Field(
        default="rdb",
        description="Persistence mode (rdb/aof/both)",
        pattern=r"^(rdb|aof|both)$",
    )
    maxmemory: Optional[str] = Field(default=None, description="Maximum memory limit")
    maxmemory_policy: str = Field(
        default="allkeys-lru", description="Memory eviction policy"
    )
    save_interval: str = Field(default="900 1", description="RDB save interval")


class MonitoringConfig(BaseServiceConfig):
    """Monitoring stack configuration (Prometheus + Grafana)"""

    prometheus_retention: str = Field(
        default="30d", description="Prometheus data retention"
    )
    external_port: int = Field(
        default=9090, description="External port for Prometheus", ge=1, le=65535
    )
    grafana_port: int = Field(default=3000, description="Grafana port", ge=1, le=65535)
    grafana_admin_user: str = Field(
        default="admin", description="Grafana admin username"
    )
    alerting_enabled: bool = Field(default=True, description="Enable alerting rules")
    provisioning_enabled: bool = Field(
        default=True, description="Enable dashboards provisioning"
    )


class PiholeConfig(BaseServiceConfig):
    """Pi-hole DNS server configuration"""

    upstream_dns: List[str] = Field(
        default_factory=lambda: ["8.8.8.8", "8.8.4.4"],
        description="Upstream DNS servers",
    )
    web_port: int = Field(
        default=8080, description="Web interface port", ge=1, le=65535
    )
    dns_port: int = Field(default=53, description="DNS port", ge=1, le=65535)
    dhcp_enabled: bool = Field(default=False, description="Enable DHCP server")
    server_ip: Optional[str] = Field(default=None, description="Server IP address")
    blocklists: List[str] = Field(
        default_factory=list, description="Additional blocklists"
    )
    whitelist: List[str] = Field(
        default_factory=list, description="Whitelisted domains"
    )


class HeadscaleConfig(BaseServiceConfig):
    """Headscale VPN coordination server configuration"""

    listen_addr: str = Field(
        default="0.0.0.0:8080", description="Listen address and port"
    )
    base_domain: Optional[str] = Field(
        default=None, description="Base domain for Magic DNS"
    )
    derp_enabled: bool = Field(default=True, description="Enable built-in DERP server")
    log_level: str = Field(
        default="info",
        description="Log level",
        pattern=r"^(trace|debug|info|warn|error)$",
    )
    ephemeral_node_timeout: str = Field(
        default="30m", description="Ephemeral node timeout"
    )


class CloudflaredConfig(BaseServiceConfig):
    """Cloudflared tunnel configuration"""

    tunnel_name: str = Field(..., description="Tunnel name")
    tunnel_id: Optional[str] = Field(
        default=None, description="Tunnel ID (auto-generated)"
    )
    ingress_rules: List[Dict[str, str]] = Field(
        default_factory=list, description="Ingress mapping rules"
    )
    log_level: str = Field(default="info", description="Log level")


class VaultwardenConfig(BaseServiceConfig):
    """Vaultwarden (Bitwarden) password manager configuration"""

    domain: Optional[str] = Field(
        default=None, description="Public domain for Vaultwarden"
    )
    web_port: int = Field(
        default=8080, description="Web interface port", ge=1, le=65535
    )
    admin_token_enabled: bool = Field(default=True, description="Enable admin panel")
    signup_allowed: bool = Field(default=False, description="Allow new user signups")
    smtp_host: Optional[str] = Field(default=None, description="SMTP server hostname")
    smtp_port: Optional[int] = Field(
        default=587, description="SMTP server port", ge=1, le=65535
    )
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_from: Optional[str] = Field(default=None, description="SMTP from address")


class VaultConfig(BaseServiceConfig):
    """HashiCorp Vault configuration"""

    storage_backend: str = Field(
        default="file", description="Storage backend (file/consul/etc)"
    )
    listener_port: int = Field(
        default=8200, description="Vault listener port", ge=1, le=65535
    )
    ui_enabled: bool = Field(default=True, description="Enable Vault UI")
    auto_unseal: bool = Field(default=False, description="Enable auto-unseal")
    auto_unseal_provider: Optional[str] = Field(
        default=None, description="Auto-unseal provider"
    )
    log_level: str = Field(default="info", description="Log level")
    dev_mode: bool = Field(default=False, description="Enable development mode")


class NextcloudConfig(BaseServiceConfig):
    """Nextcloud configuration"""

    admin_user: str = Field(default="admin", description="Admin username")
    http_port: int = Field(default=8081, description="HTTP port", ge=1, le=65535)
    domain: Optional[str] = Field(
        default=None, description="Public domain for Nextcloud"
    )
    trusted_domains: List[str] = Field(
        default_factory=list, description="Additional trusted domains"
    )
    upload_max_filesize: str = Field(
        default="2G", description="Maximum upload file size"
    )
    memory_limit: str = Field(default="512M", description="PHP memory limit")
    redis_enabled: bool = Field(default=True, description="Enable Redis for caching")
    cron_enabled: bool = Field(default=True, description="Enable background cron jobs")
    external_storage: List[Dict[str, str]] = Field(
        default_factory=list, description="External storage providers"
    )


class GitlabConfig(BaseServiceConfig):
    """GitLab CE configuration"""

    external_url: Optional[str] = Field(
        default=None, description="External URL for GitLab"
    )
    ssh_port: int = Field(
        default=22, description="SSH port for Git operations", ge=1, le=65535
    )
    http_port: int = Field(default=80, description="HTTP port", ge=1, le=65535)
    https_port: int = Field(default=443, description="HTTPS port", ge=1, le=65535)
    registry_enabled: bool = Field(
        default=True, description="Enable container registry"
    )
    pages_enabled: bool = Field(default=True, description="Enable GitLab Pages")
    backup_schedule: str = Field(
        default="0 2 * * *", description="Backup cron schedule"
    )
    ldap_enabled: bool = Field(default=False, description="Enable LDAP integration")
    ldap_host: Optional[str] = Field(default=None, description="LDAP server hostname")
    ldap_base_dn: Optional[str] = Field(default=None, description="LDAP base DN")
    runner_registration_token: Optional[str] = Field(
        default=None, description="Runner registration token"
    )


class JenkinsConfig(BaseServiceConfig):
    """Jenkins CI/CD configuration"""

    http_port: int = Field(
        default=8080, description="Jenkins HTTP port", ge=1, le=65535
    )
    agent_port: int = Field(
        default=50000, description="Jenkins agent port", ge=1, le=65535
    )
    java_opts: str = Field(
        default="-Xms512m -Xmx1024m", description="Java runtime options"
    )
    plugins: List[str] = Field(default_factory=list, description="Plugins to install")
    security_realm: str = Field(
        default="local", description="Security realm (local/ldap/etc)"
    )
    executor_count: int = Field(
        default=2, description="Number of executors", ge=1, le=10
    )


class N8nConfig(BaseServiceConfig):
    """n8n workflow automation configuration"""

    port: int = Field(default=5678, description="n8n web port", ge=1, le=65535)
    webhook_url: Optional[str] = Field(default=None, description="Webhook base URL")
    timezone: str = Field(default="UTC", description="Timezone for workflows")
    encryption_key: Optional[str] = Field(
        default=None, description="Encryption key for credentials"
    )
    auth_enabled: bool = Field(default=True, description="Enable user authentication")
    basic_auth_user: str = Field(default="admin", description="Basic auth username")
    executions_mode: str = Field(
        default="main", description="Executions mode (main/queue)"
    )


class FumadocsConfig(BaseServiceConfig):
    """Fumadocs documentation platform configuration"""

    port: int = Field(default=3000, description="Fumadocs port", ge=1, le=65535)
    content_path: str = Field(
        default="./docs", description="Path to documentation content"
    )
    auth_enabled: bool = Field(default=False, description="Enable authentication")
    auth_provider: str = Field(default="local", description="Authentication provider")
    theme: str = Field(default="default", description="Documentation theme")
    search_enabled: bool = Field(
        default=True, description="Enable search functionality"
    )


class CustomEnvironmentConfig(BaseModel):
    """Custom environment variables configuration for services"""

    # Dictionary mapping service names to their custom environment variables
    # Format: {"service_name": {"ENV_VAR_NAME": "value"}}
    variables: Dict[str, Dict[str, str]] = Field(
        default_factory=dict, description="Custom environment variables per service"
    )

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


# === V2 Root Configuration Model ===


class LabConfig(BaseModel):
    """Main configuration class for version 2"""

    version: int = Field(default=2, description="Configuration format version")
    profile: Profile = Field(default=Profile.PROD, description="Deployment profile")

    # Core settings
    core: CoreConfig

    # Service configurations (all optional)
    services: Dict[str, BaseServiceConfig] = Field(
        default_factory=dict, description="Service configurations"
    )

    # Custom environment variables
    custom_env: Dict[str, Dict[str, str]] = Field(
        default_factory=dict, description="Custom environment variables per service"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_service_configs(cls, values):
        """Validate service configurations and ensure proper types"""
        if isinstance(values, dict):
            services = values.get("services", {})

            # Map service IDs to their specific config classes
            service_config_types = {
                "traefik": TraefikConfig,
                "postgresql": PostgresConfig,
                "redis": RedisConfig,
                "monitoring": MonitoringConfig,
                "pihole": PiholeConfig,
                "headscale": HeadscaleConfig,
                "cloudflared": CloudflaredConfig,
                "vaultwarden": VaultwardenConfig,
                "vault": VaultConfig,
                "nextcloud": NextcloudConfig,
                "gitlab": GitlabConfig,
                "jenkins": JenkinsConfig,
                "n8n": N8nConfig,
                "fumadocs": FumadocsConfig,
            }

            # Convert dict configs to proper model instances
            for service_id, config in services.items():
                if isinstance(config, dict):
                    config_class = service_config_types.get(
                        service_id, BaseServiceConfig
                    )
                    try:
                        services[service_id] = config_class(**config)
                    except Exception as e:
                        raise ValueError(
                            f"Invalid configuration for service '{service_id}': {e}"
                        )

            values["services"] = services

        return values

    @classmethod
    def load_from_file(cls, config_path: Path) -> "LabConfig":
        """Load configuration from YAML file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            # Convert to dict and handle Enums
            data = self.dict()
            if "profile" in data:
                data["profile"] = (
                    data["profile"].value
                    if hasattr(data["profile"], "value")
                    else data["profile"]
                )

            yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=False)

    def get_enabled_services(self) -> Dict[str, BaseServiceConfig]:
        """Get only enabled services"""
        return {k: v for k, v in self.services.items() if v.enabled}

    def get_service_urls(self) -> Dict[str, str]:
        """Get service URLs based on configuration"""
        base_domain = self.core.domain
        urls = {}

        for service_id, config in self.get_enabled_services().items():
            if hasattr(config, "domain") and config.domain:
                # Use service-specific domain if available
                service_domain = config.domain
            else:
                # Use subdomain of base domain
                service_domain = f"{service_id}.{base_domain}"

            urls[service_id] = f"https://{service_domain}"

        return urls

    def validate_configuration(self) -> List[str]:
        """Validate complete configuration and return issues"""
        issues = []

        # Core validation
        if not self.core.domain or "." not in self.core.domain:
            issues.append("Core domain should be a valid FQDN")

        if not self.core.email or "@" not in self.core.email:
            issues.append("Core email should be a valid email address")

        # Service-specific validation
        enabled_services = self.get_enabled_services()

        # Check for port conflicts
        used_ports = {}
        for service_id, config in enabled_services.items():
            if hasattr(config, "port"):
                port = config.port
                if port in used_ports:
                    issues.append(
                        f"Port {port} used by both {used_ports[port]} and {service_id}"
                    )
                else:
                    used_ports[port] = service_id

        # Dependency validation
        for service_id, config in enabled_services.items():
            if hasattr(config, "dependencies"):
                for dep in config.dependencies:
                    if dep not in enabled_services:
                        issues.append(
                            f"Service {service_id} requires {dep} but it's not enabled"
                        )

        return issues


# === Legacy Configuration Migration ===


def migrate_from_legacy(legacy_config: Dict[str, Any]) -> LabConfig:
    """
    Migrate from legacy configuration format to v2

    Args:
        legacy_config: Legacy configuration dictionary

    Returns:
        New LabConfig instance
    """
    # Extract core configuration
    core_data = legacy_config.get("core", {})
    core_config = CoreConfig(**core_data)

    # Start with base config
    config_data = {
        "version": 2,
        "profile": "prod",
        "core": core_config,
        "services": {},
        "custom_env": legacy_config.get("custom_env", {}).get("variables", {}),
    }

    # Map legacy service configurations
    service_mappings = {
        "monitoring": "monitoring",
        "gitlab": "gitlab",
        "vault": "vault",
        "networking": ["pihole", "headscale", "cloudflared"],
        "databases": ["postgresql", "redis"],
        "passwords": ["vaultwarden"],
        "dashboards": ["glance", "uptime_kuma"],
        "documentation": ["fumadocs"],
        "automation": ["n8n"],
        "ci_cd": ["gitlab", "jenkins"],
        "proxy": ["traefik"],
    }

    # Convert legacy service configs
    for legacy_key, service_ids in service_mappings.items():
        legacy_section = legacy_config.get(legacy_key, {})

        if isinstance(service_ids, str):
            service_ids = [service_ids]

        for service_id in service_ids:
            if isinstance(legacy_section, dict):
                if service_id in legacy_section or legacy_section.get("enabled", False):
                    # Create service config based on legacy data
                    service_data = {"enabled": legacy_section.get(service_id, True)}

                    # Map specific fields based on service type
                    if service_id == "traefik":
                        service_data.update(
                            {
                                "domain": core_data.get("domain", "homelab.local"),
                                "email": core_data.get("email", "admin@example.com"),
                                "acme_environment": (
                                    "staging"
                                    if legacy_config.get("reverse_proxy", {}).get(
                                        "staging", False
                                    )
                                    else "production"
                                ),
                            }
                        )

                    config_data["services"][service_id] = service_data

    return LabConfig(**config_data)


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

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(
                self.dict(), f, default_flow_style=False, indent=2, sort_keys=False
            )

    def validate_requirements(self) -> List[str]:
        """Validate configuration and return warnings"""
        warnings = []

        # Check domain format
        if not self.core.domain or "." not in self.core.domain:
            warnings.append("Domain should be a valid FQDN (e.g., homelab.example.com)")

        # Check email format
        if not self.core.email or "@" not in self.core.email:
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
