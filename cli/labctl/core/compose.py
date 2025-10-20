"""
Schema-driven Docker Compose generator for Home Lab services
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from .config import Config, LabConfig, BaseServiceConfig
from .services.schema import ServiceSchema, load_service_schemas
from .services.deps import resolve_with_dependencies
from .secrets import load_or_create_env
from rich.console import Console

console = Console()


class ComposeGenerator:
    """Schema-driven Docker Compose generator"""
    
    def __init__(self, config: Union[Config, LabConfig, dict], schemas: Optional[Dict[str, ServiceSchema]] = None):
        self.config = config
        self.schemas = schemas or {}
        self.services = {}
        self.networks = {
            "traefik": {
                "driver": "bridge",
                "name": "traefik"
            }
        }
        self.volumes = {}
        self.env_vars = {}
        
        # Load schemas if not provided
        if not self.schemas and hasattr(config, 'services'):
            try:
                # Try to load schemas from default location
                schemas_path = Path("config/services")
                if schemas_path.exists():
                    self.schemas = load_service_schemas(str(schemas_path))
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load service schemas: {e}[/yellow]")
    
    def _secure_traefik_labels(self, name: str, subdomain: str, port: Optional[int] = None) -> List[str]:
        """Generate consistent Traefik labels with HTTPS, TLS, and security headers"""
        labels = [
            "traefik.enable=true",
            "traefik.docker.network=traefik",
            f"traefik.http.routers.{name}.rule=Host(`{subdomain}.{self.config.core.domain}`)",
            f"traefik.http.routers.{name}.entrypoints=websecure",
            f"traefik.http.routers.{name}.tls.certresolver=letsencrypt",
            f"traefik.http.routers.{name}.middlewares=secure-headers@docker"
        ]
        if port is not None:
            labels.append(f"traefik.http.services.{name}.loadbalancer.server.port={port}")
        return labels
    
    def _merge_environment_variables(self, service_name: str, default_env: List[str]) -> List[str]:
        """Merge default environment variables with custom ones for a service"""
        # Convert default env list to dict for easier merging
        env_dict = {}
        for env_var in default_env:
            if "=" in env_var:
                key, value = env_var.split("=", 1)
                env_dict[key] = value
            else:
                # Handle environment variables without values (like for docker secrets)
                env_dict[env_var] = ""
        
        # Add custom environment variables (they override defaults)
        custom_vars = {}
        if hasattr(self.config, 'custom_env') and self.config.custom_env.has_custom_vars(service_name):
            # Config object case
            custom_vars = self.config.custom_env.get_service_vars(service_name)
        elif isinstance(self.config, dict) and 'custom_env' in self.config:
            # Dict-based config case (from init command)
            custom_env_data = self.config.get('custom_env', {})
            variables = custom_env_data.get('variables', {})
            custom_vars = variables.get(service_name, {})
        
        if custom_vars:
            env_dict.update(custom_vars)
        
        # Convert back to list format
        result = []
        for key, value in env_dict.items():
            if value:  # Only add =value if there is a value
                result.append(f"{key}={value}")
            else:
                result.append(key)
        
        return result
    
    def _get_enabled_services(self) -> Dict[str, Any]:
        """Get enabled services from config in a consistent format"""
        if isinstance(self.config, LabConfig):
            return self.config.get_enabled_services()
        elif isinstance(self.config, dict) and 'services' in self.config:
            # New dict format
            return {k: v for k, v in self.config['services'].items() if v.get('enabled', False)}
        elif hasattr(self.config, 'proxy') and hasattr(self.config, 'databases'):
            # Legacy Config object format
            enabled = {}
            if self.config.proxy.traefik:
                enabled['traefik'] = {'enabled': True}
            if self.config.databases.postgresql:
                enabled['postgresql'] = {'enabled': True}
            if self.config.databases.redis:
                enabled['redis'] = {'enabled': True}
            if self.config.monitoring.enabled:
                enabled['monitoring'] = {'enabled': True}
            # Add other legacy mappings as needed
            return enabled
        else:
            return {}
    
    def _generate_service_from_schema(self, service_id: str, service_config: Any, schema: ServiceSchema) -> Optional[Dict[str, Any]]:
        """Generate Docker Compose service definition from schema"""
        if not schema.compose:
            console.print(f"[yellow]Warning: No compose configuration in schema for {service_id}[/yellow]")
            return None
        
        compose_service = {
            "image": schema.compose.image,
            "container_name": service_id,
            "restart": "unless-stopped",
            "networks": ["traefik"]
        }
        
        # Add environment variables
        if schema.compose.environment:
            environment = self._build_environment_from_schema(service_id, service_config, schema)
            if environment:
                compose_service["environment"] = environment
        
        # Add ports
        if schema.compose.ports:
            ports = self._build_ports_from_schema(service_config, schema)
            if ports:
                compose_service["ports"] = ports
        
        # Add volumes
        if schema.compose.volumes:
            volumes = self._build_volumes_from_schema(service_id, service_config, schema)
            if volumes:
                compose_service["volumes"] = volumes
                self._register_volumes(service_id, volumes)
        
        # Add labels (especially Traefik)
        if schema.compose.labels:
            labels = self._build_labels_from_schema(service_id, service_config, schema)
            if labels:
                compose_service["labels"] = labels
        
        # Add dependencies
        if schema.compose.depends_on:
            depends_on = self._build_depends_on_from_schema(schema)
            if depends_on:
                compose_service["depends_on"] = depends_on
        
        # Add health check
        if schema.compose.healthcheck and service_config.get('healthcheck_enabled', True):
            healthcheck = self._build_healthcheck_from_schema(schema)
            if healthcheck:
                compose_service["healthcheck"] = healthcheck
        
        # Add any additional compose properties
        if hasattr(schema.compose, 'command') and schema.compose.command:
            compose_service["command"] = schema.compose.command
        
        if hasattr(schema.compose, 'cap_add') and schema.compose.cap_add:
            compose_service["cap_add"] = schema.compose.cap_add
        
        if hasattr(schema.compose, 'privileged') and schema.compose.privileged:
            compose_service["privileged"] = schema.compose.privileged
        
        return compose_service
    
    def _generate_service_legacy(self, service_id: str, service_config: Any) -> Optional[Dict[str, Any]]:
        """Fallback generation for services without schemas"""
        console.print(f"[yellow]Warning: Using legacy generation for {service_id}[/yellow]")
        
        # Basic service structure
        compose_service = {
            "container_name": service_id,
            "restart": "unless-stopped",
            "networks": ["traefik"]
        }
        
        # Try to determine image from service ID
        image_mappings = {
            'traefik': 'traefik:v3.1',
            'postgresql': 'postgres:16',
            'redis': 'redis:7-alpine',
            'monitoring': 'prom/prometheus:latest',
            'grafana': 'grafana/grafana:latest',
            'vaultwarden': 'vaultwarden/server:latest',
            'nextcloud': 'nextcloud:27',
            'pihole': 'pihole/pihole:latest'
        }
        
        compose_service["image"] = image_mappings.get(service_id, f"{service_id}:latest")
        
        return compose_service
    
    def _build_environment_from_schema(self, service_id: str, service_config: Any, schema: ServiceSchema) -> List[str]:
        """Build environment variables from schema and config"""
        environment = []
        
        for env_source in schema.compose.environment:
            env_key = env_source.key
            env_value = None
            
            if env_source.from_field:
                # Get value from service configuration
                if hasattr(service_config, env_source.from_field):
                    env_value = getattr(service_config, env_source.from_field)
                elif isinstance(service_config, dict):
                    env_value = service_config.get(env_source.from_field)
            
            elif env_source.from_service:
                # Get value from another service (e.g., postgresql.host)
                service_name, field = env_source.from_service.split('.', 1)
                env_value = f"${service_name.upper()}_{field.upper()}"
            
            elif env_source.from_secret:
                # Use environment variable reference
                env_value = f"${env_source.from_secret}"
            
            elif env_source.from_literal:
                # Use literal value
                env_value = env_source.from_literal
            
            if env_value is not None:
                environment.append(f"{env_key}={env_value}")
        
        # Add custom environment variables
        custom_env = self._get_custom_environment(service_id)
        for key, value in custom_env.items():
            environment.append(f"{key}={value}")
        
        return environment
    
    def _build_ports_from_schema(self, service_config: Any, schema: ServiceSchema) -> List[str]:
        """Build port mappings from schema"""
        ports = []
        
        for port_spec in schema.compose.ports:
            # Handle template substitution
            if '${' in port_spec:
                # Extract field name from ${field_name}
                import re
                field_matches = re.findall(r'\$\{(\w+)\}', port_spec)
                for field_name in field_matches:
                    if hasattr(service_config, field_name):
                        value = getattr(service_config, field_name)
                        port_spec = port_spec.replace(f'${{{field_name}}}', str(value))
                    elif isinstance(service_config, dict):
                        value = service_config.get(field_name)
                        if value is not None:
                            port_spec = port_spec.replace(f'${{{field_name}}}', str(value))
            
            ports.append(port_spec)
        
        return ports
    
    def _build_volumes_from_schema(self, service_id: str, service_config: Any, schema: ServiceSchema) -> List[str]:
        """Build volume mappings from schema"""
        volumes = []
        
        for volume_spec in schema.compose.volumes:
            # Handle named volumes (service_name_data:/path)
            if '${SERVICE_DATA_DIR}' in volume_spec:
                volume_spec = volume_spec.replace('${SERVICE_DATA_DIR}', f"{service_id}_data")
            
            volumes.append(volume_spec)
        
        return volumes
    
    def _build_labels_from_schema(self, service_id: str, service_config: Any, schema: ServiceSchema) -> List[str]:
        """Build Traefik labels from schema"""
        labels = []
        
        # Get domain from config
        domain = self._get_domain()
        
        for label_spec in schema.compose.labels:
            # Handle template substitution
            label = label_spec
            if '${DOMAIN}' in label:
                label = label.replace('${DOMAIN}', domain)
            if '${SERVICE_ID}' in label:
                label = label.replace('${SERVICE_ID}', service_id)
            
            # Handle service config field substitution
            if hasattr(service_config, 'domain') and service_config.domain:
                if '${SERVICE_DOMAIN}' in label:
                    label = label.replace('${SERVICE_DOMAIN}', service_config.domain)
            
            labels.append(label)
        
        return labels
    
    def _build_depends_on_from_schema(self, schema: ServiceSchema) -> Dict[str, Dict[str, str]]:
        """Build depends_on configuration with health checks"""
        depends_on = {}
        
        for dep_service in schema.compose.depends_on:
            depends_on[dep_service] = {"condition": "service_healthy"}
        
        return depends_on
    
    def _build_healthcheck_from_schema(self, schema: ServiceSchema) -> Dict[str, Any]:
        """Build healthcheck configuration"""
        if not schema.compose.healthcheck:
            return {}
        
        healthcheck = {
            "test": schema.compose.healthcheck.test,
            "interval": schema.compose.healthcheck.interval or "30s",
            "timeout": schema.compose.healthcheck.timeout or "5s",
            "retries": schema.compose.healthcheck.retries or 3,
            "start_period": schema.compose.healthcheck.start_period or "10s"
        }
        
        return healthcheck
    
    def _get_custom_environment(self, service_id: str) -> Dict[str, str]:
        """Get custom environment variables for a service"""
        if isinstance(self.config, LabConfig):
            return self.config.custom_env.get(service_id, {})
        elif isinstance(self.config, dict) and 'custom_env' in self.config:
            return self.config['custom_env'].get(service_id, {})
        else:
            return {}
    
    def _get_domain(self) -> str:
        """Get the primary domain from config"""
        if isinstance(self.config, LabConfig):
            return self.config.core.domain
        elif isinstance(self.config, dict) and 'core' in self.config:
            return self.config['core'].get('domain', 'homelab.local')
        elif hasattr(self.config, 'core'):
            return self.config.core.domain
        else:
            return 'homelab.local'
    
    def _register_volumes(self, service_id: str, volumes: List[str]) -> None:
        """Register named volumes for the compose file"""
        for volume_spec in volumes:
            if ':' in volume_spec:
                volume_name = volume_spec.split(':')[0]
                if not volume_name.startswith('./') and not volume_name.startswith('/'):
                    # This is a named volume
                    self.volumes[volume_name] = None
    
    def save_compose_file(self, file_path: Path) -> None:
        """Save Docker Compose configuration to file"""
        compose_config = self.generate_compose()
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            # Write header comment
            f.write("# Docker Compose configuration for Home Lab\n")
            f.write("# Generated by labctl - do not edit manually\n\n")
            yaml.dump(compose_config, f, default_flow_style=False, indent=2, sort_keys=False)
    
    def save_env_template(self, file_path: Path) -> None:
        """Save environment template file"""
        env_template = [
            "# Home Lab Environment Variables Template",
            "# Copy this file to .env and update the values",
            "# DO NOT COMMIT .env TO VERSION CONTROL",
            "",
            "# Timezone",
            "TZ=UTC",
            "",
            "# Traefik Dashboard Authentication (generate with: htpasswd -nb admin password)",
            "TRAEFIK_DASHBOARD_USERS=admin:$2y$10$example_hash_here",
            "",
            "# Vaultwarden Admin Token (generate with: openssl rand -hex 32)", 
            "VAULTWARDEN_ADMIN_TOKEN=your_secure_token_here",
            "",
            "# Cloudflare Tunnel Token (if using Cloudflared)",
            "CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_here",
            "",
            "# Backup Configuration (if using backups)",
            "BACKUP_S3_BUCKET=your-backup-bucket",
            "BACKUP_S3_KEY=your-s3-access-key",
            "BACKUP_S3_SECRET=your-s3-secret-key",
            ""
        ]
        
        with open(file_path, 'w') as f:
            f.write("\n".join(env_template))
    
    def generate_env_vars(self) -> Dict[str, str]:
        """Generate environment variables for .env file"""
        env_vars = {}
        
        # Add basic environment variables
        env_vars["TZ"] = "UTC"
        
        # Add service-specific environment variables from config
        if isinstance(self.config, dict) and 'env_vars' in self.config:
            env_vars.update(self.config['env_vars'])
        elif hasattr(self.config, 'env_vars'):
            env_vars.update(self.config.env_vars)
        
        return env_vars
