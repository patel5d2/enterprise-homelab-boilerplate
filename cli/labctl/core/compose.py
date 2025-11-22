"""
Schema-driven Docker Compose generator for Home Lab services
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from rich.console import Console

from .config import BaseServiceConfig, Config, LabConfig
from .secrets import load_or_create_env
from .services.deps import resolve_with_dependencies
from .services.schema import ServiceSchema, load_service_schemas

console = Console()


class ComposeGenerator:
    """Schema-driven Docker Compose generator"""

    def __init__(
        self,
        config: Union[Config, LabConfig, dict],
        schemas: Optional[Dict[str, ServiceSchema]] = None,
    ):
        self.config = config
        self.schemas = schemas or {}
        self.services = {}
        self.networks = {"traefik": {"external": True, "name": "traefik"}}
        self.volumes = {}
        self.env_vars = {}

        # Load schemas if not provided
        if not self.schemas and hasattr(config, "services"):
            try:
                # Try to load schemas from default location
                # Prefer v2 services directory if it exists
                schemas_path = Path("config/services-v2")
                if not schemas_path.exists():
                    schemas_path = Path("config/services")

                if schemas_path.exists():
                    self.schemas = load_service_schemas(str(schemas_path))
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not load service schemas: {e}[/yellow]"
                )

    def _secure_traefik_labels(
        self, name: str, subdomain: str, port: Optional[int] = None
    ) -> List[str]:
        """Generate consistent Traefik labels with HTTPS, TLS, and security headers"""
        labels = [
            "traefik.enable=true",
            "traefik.docker.network=traefik",
            f"traefik.http.routers.{name}.rule=Host(`{subdomain}.{self.config.core.domain}`)",
            f"traefik.http.routers.{name}.entrypoints=websecure",
            f"traefik.http.routers.{name}.tls.certresolver=letsencrypt",
            f"traefik.http.routers.{name}.middlewares=secure-headers@docker",
        ]
        if port is not None:
            labels.append(
                f"traefik.http.services.{name}.loadbalancer.server.port={port}"
            )
        return labels

    def _merge_environment_variables(
        self, service_name: str, default_env: List[str]
    ) -> List[str]:
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
        if hasattr(
            self.config, "custom_env"
        ) and self.config.custom_env.has_custom_vars(service_name):
            # Config object case
            custom_vars = self.config.custom_env.get_service_vars(service_name)
        elif isinstance(self.config, dict) and "custom_env" in self.config:
            # Dict-based config case (from init command)
            custom_env_data = self.config.get("custom_env", {})
            variables = custom_env_data.get("variables", {})
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
        elif isinstance(self.config, dict) and "services" in self.config:
            # New dict format
            return {
                k: v
                for k, v in self.config["services"].items()
                if v.get("enabled", False)
            }
        elif hasattr(self.config, "proxy") and hasattr(self.config, "databases"):
            # Legacy Config object format
            enabled = {}
            if self.config.proxy.traefik:
                enabled["traefik"] = {"enabled": True}
            if self.config.databases.postgresql:
                enabled["postgresql"] = {"enabled": True}
            if self.config.databases.redis:
                enabled["redis"] = {"enabled": True}
            if self.config.monitoring.enabled:
                enabled["monitoring"] = {"enabled": True}
            # Add other legacy mappings as needed
            return enabled
        else:
            return {}

    def _generate_service_from_schema(
        self, service_id: str, service_config: Any, schema: ServiceSchema
    ) -> Optional[Dict[str, Any]]:
        """Generate Docker Compose service definition from schema"""
        if not schema.compose:
            console.print(
                f"[yellow]Warning: No compose configuration in schema for {service_id}[/yellow]"
            )
            return None

        try:
            return self._build_service_from_schema(service_id, service_config, schema)
        except Exception as e:
            console.print(f"[red]Error generating service {service_id}: {e}[/red]")
            console.print(
                f"[yellow]Falling back to legacy generation for {service_id}[/yellow]"
            )
            return self._generate_service_legacy(service_id, service_config)

    def _build_service_from_schema(
        self, service_id: str, service_config: Any, schema: ServiceSchema
    ) -> Dict[str, Any]:
        """Build service configuration from schema (with error handling)"""
        if not schema.compose.image:
            raise ValueError(
                f"Service {service_id} schema missing required 'image' field"
            )

        compose_service = {
            "image": schema.compose.image,
            "container_name": service_id,
            "restart": "unless-stopped",
            "networks": ["traefik"],
        }

        try:
            # Add environment variables
            if schema.compose.environment:
                environment = self._build_environment_from_schema(
                    service_id, service_config, schema
                )
                if environment:
                    compose_service["environment"] = environment
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to build environment for {service_id}: {e}[/yellow]"
            )

        try:
            # Add ports
            if schema.compose.ports:
                ports = self._build_ports_from_schema(service_config, schema)
                if ports:
                    compose_service["ports"] = ports
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to build ports for {service_id}: {e}[/yellow]"
            )

        try:
            # Add volumes
            if schema.compose.volumes:
                volumes = self._build_volumes_from_schema(
                    service_id, service_config, schema
                )
                if volumes:
                    compose_service["volumes"] = volumes
                    self._register_volumes(service_id, volumes)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to build volumes for {service_id}: {e}[/yellow]"
            )

        try:
            # Add labels (especially Traefik)
            if schema.compose.labels:
                labels = self._build_labels_from_schema(
                    service_id, service_config, schema
                )
                if labels:
                    compose_service["labels"] = labels
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to build labels for {service_id}: {e}[/yellow]"
            )

        try:
            # Add dependencies
            if schema.compose.depends_on:
                depends_on = self._build_depends_on_from_schema(schema)
                if depends_on:
                    compose_service["depends_on"] = depends_on
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to build dependencies for {service_id}: {e}[/yellow]"
            )

        try:
            # Add health check
            healthcheck_enabled = True
            if isinstance(service_config, dict):
                healthcheck_enabled = service_config.get("healthcheck_enabled", True)
            else:
                healthcheck_enabled = getattr(service_config, "healthcheck_enabled", True)

            if schema.compose.healthcheck and healthcheck_enabled:
                healthcheck = self._build_healthcheck_from_schema(schema)
                if healthcheck:
                    compose_service["healthcheck"] = healthcheck
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to build healthcheck for {service_id}: {e}[/yellow]"
            )

        # Add any additional compose properties
        try:
            if hasattr(schema.compose, "command") and schema.compose.command:
                command = schema.compose.command
                if isinstance(command, str):
                    compose_service["command"] = self._substitute_template(
                        command, service_id, service_config
                    )
                elif isinstance(command, list):
                    compose_service["command"] = [
                        self._substitute_template(cmd, service_id, service_config)
                        for cmd in command
                    ]

            if hasattr(schema.compose, "cap_add") and schema.compose.cap_add:
                compose_service["cap_add"] = schema.compose.cap_add

            if hasattr(schema.compose, "privileged") and schema.compose.privileged:
                compose_service["privileged"] = schema.compose.privileged
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to add additional properties for {service_id}: {e}[/yellow]"
            )

        return compose_service

    def _generate_service_legacy(
        self, service_id: str, service_config: Any
    ) -> Optional[Dict[str, Any]]:
        """Fallback generation for services without schemas"""
        console.print(
            f"[yellow]Warning: Using legacy generation for {service_id}[/yellow]"
        )

        # Basic service structure
        compose_service = {
            "container_name": service_id,
            "restart": "unless-stopped",
            "networks": ["traefik"],
        }

        # Try to determine image from service ID
        image_mappings = {
            "traefik": "traefik:v3.1",
            "postgresql": "postgres:16",
            "redis": "redis:7-alpine",
            "monitoring": "prom/prometheus:latest",
            "grafana": "grafana/grafana:latest",
            "vaultwarden": "vaultwarden/server:latest",
            "nextcloud": "nextcloud:27",
            "pihole": "pihole/pihole:latest",
        }

        compose_service["image"] = image_mappings.get(
            service_id, f"{service_id}:latest"
        )

        return compose_service

    def _build_environment_from_schema(
        self, service_id: str, service_config: Any, schema: ServiceSchema
    ) -> List[str]:
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

                    # If not in service config, try global env_vars
                    if env_value is None:
                        if (
                            hasattr(self.config, "env_vars")
                            and env_source.from_field.upper() in self.config.env_vars
                        ):
                            env_value = f"${{{env_source.from_field.upper()}}}"
                        elif (
                            isinstance(self.config, dict) and "env_vars" in self.config
                        ):
                            if env_source.from_field.upper() in self.config["env_vars"]:
                                env_value = f"${{{env_source.from_field.upper()}}}"

            elif env_source.from_service:
                # Get value from another service (e.g., postgresql.host)
                service_name, field = env_source.from_service.split(".", 1)
                env_value = f"${service_name.upper()}_{field.upper()}"

            elif env_source.value:
                # Use static literal value
                env_value = env_source.value

            elif env_source.template:
                # Use template with variable substitution
                env_value = self._substitute_template(
                    env_source.template, service_id, service_config
                )

            elif env_source.value_map and env_source.from_field:
                # Use value mapping based on field value
                field_value = None
                if hasattr(service_config, env_source.from_field):
                    field_value = getattr(service_config, env_source.from_field)
                elif isinstance(service_config, dict):
                    field_value = service_config.get(env_source.from_field)

                if field_value and str(field_value) in env_source.value_map:
                    env_value = env_source.value_map[str(field_value)]

            # Apply condition if present
            if env_source.condition and not self._evaluate_condition(
                env_source.condition, service_config
            ):
                continue

            if env_value is not None:
                environment.append(f"{env_key}={env_value}")

        # Add custom environment variables
        custom_env = self._get_custom_environment(service_id)
        for key, value in custom_env.items():
            environment.append(f"{key}={value}")

        return environment

    def _build_ports_from_schema(
        self, service_config: Any, schema: ServiceSchema
    ) -> List[str]:
        """Build port mappings from schema"""
        ports = []

        for port_spec in schema.compose.ports:
            # Handle template substitution
            if "${" in port_spec:
                # Extract field name from ${field_name}
                import re

                field_matches = re.findall(r"\$\{(\w+)\}", port_spec)
                for field_name in field_matches:
                    if hasattr(service_config, field_name):
                        value = getattr(service_config, field_name)
                        port_spec = port_spec.replace(f"${{{field_name}}}", str(value))
                    elif isinstance(service_config, dict):
                        value = service_config.get(field_name)
                        if value is not None:
                            port_spec = port_spec.replace(
                                f"${{{field_name}}}", str(value)
                            )

            ports.append(port_spec)

        return ports

    def _build_volumes_from_schema(
        self, service_id: str, service_config: Any, schema: ServiceSchema
    ) -> List[str]:
        """Build volume mappings from schema"""
        volumes = []

        for volume_spec in schema.compose.volumes:
            # Handle named volumes (service_name_data:/path)
            if "${SERVICE_DATA_DIR}" in volume_spec:
                volume_spec = volume_spec.replace(
                    "${SERVICE_DATA_DIR}", f"{service_id}_data"
                )

            volumes.append(volume_spec)

        return volumes

    def _build_labels_from_schema(
        self, service_id: str, service_config: Any, schema: ServiceSchema
    ) -> List[str]:
        """Build Traefik labels from schema"""
        labels = []

        # Get domain from config
        domain = self._get_domain()

        for label_spec in schema.compose.labels:
            # Handle template substitution using the centralized method
            label = self._substitute_template(label_spec, service_id, service_config)
            
            # Handle legacy manual substitutions (if any remain not covered by _substitute_template)
            if hasattr(service_config, "domain") and service_config.domain:
                if "${SERVICE_DOMAIN}" in label:
                    label = label.replace("${SERVICE_DOMAIN}", service_config.domain)

            labels.append(label)

        return labels

    def _build_depends_on_from_schema(
        self, schema: ServiceSchema
    ) -> Dict[str, Dict[str, str]]:
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
            "start_period": schema.compose.healthcheck.start_period or "10s",
        }

        return healthcheck

    def _substitute_template(
        self, template: str, service_id: str, service_config: Any
    ) -> str:
        """Substitute template variables with actual values"""
        import re

        result = template

        # Replace ${field} with service config values
        if isinstance(service_config, dict):
            for key, value in service_config.items():
                result = result.replace(f"${{{key}}}", str(value))
        elif hasattr(service_config, "__dict__"):
            # Handle pydantic models
            for key, value in service_config.__dict__.items():
                result = result.replace(f"${{{key}}}", str(value))

        # Replace common template variables
        result = result.replace("${service}", service_id)
        result = result.replace("${SERVICE_ID}", service_id)
        result = result.replace("${DOMAIN}", self._get_domain())

        # Handle environment variable references
        env_pattern = r"\$\{ENV:([^}]+)\}"
        env_matches = re.findall(env_pattern, result)
        for env_var in env_matches:
            if hasattr(self.config, "env_vars") and env_var in self.config.env_vars:
                result = result.replace(
                    f"${{ENV:{env_var}}}", str(self.config.env_vars[env_var])
                )
            elif (
                isinstance(self.config, dict)
                and "env_vars" in self.config
                and env_var in self.config["env_vars"]
            ):
                result = result.replace(
                    f"${{ENV:{env_var}}}", str(self.config["env_vars"][env_var])
                )

        # Handle generate:htpasswd
        if "${generate:htpasswd" in result:
            import re
            # Pattern: ${generate:htpasswd:user_field:pass_field}
            pattern = r"\$\{generate:htpasswd:(\w+):(\w+)\}"
            matches = re.findall(pattern, result)
            for user_field, pass_field in matches:
                # Try to find values in config
                user_val = "admin"
                if isinstance(service_config, dict):
                    user_val = service_config.get(user_field, "admin")
                elif hasattr(service_config, user_field):
                    user_val = getattr(service_config, user_field)
                elif user_field == "dashboard_user" and hasattr(service_config, "dashboard_username"):
                    user_val = getattr(service_config, "dashboard_username")

                # For password/hash, check if we have a pre-calculated hash
                hash_val = None
                if hasattr(service_config, "dashboard_auth_hash") and service_config.dashboard_auth_hash:
                    hash_val = service_config.dashboard_auth_hash
                
                # If no hash, we should ideally generate it, but for now let's use a placeholder or environment variable
                # The .env template uses TRAEFIK_DASHBOARD_USERS
                if not hash_val:
                    replacement = "${TRAEFIK_DASHBOARD_USERS}"
                else:
                    replacement = f"{user_val}:{hash_val}"
                
                result = result.replace(f"${{generate:htpasswd:{user_field}:{pass_field}}}", replacement)

        # Handle from_field:field_name
        if "${from_field:" in result:
            import re
            pattern = r"\$\{from_field:(\w+)\}"
            matches = re.findall(pattern, result)
            for field_name in matches:
                value = None
                if isinstance(service_config, dict):
                    value = service_config.get(field_name)
                elif hasattr(service_config, field_name):
                    value = getattr(service_config, field_name)
                
                if value is not None:
                    result = result.replace(f"${{from_field:{field_name}}}", str(value))

        return result

    def _evaluate_condition(self, condition: str, service_config: Any) -> bool:
        """Evaluate simple conditions for environment variables"""
        if not condition:
            return True

        # Handle simple field existence checks
        if condition.startswith("has_"):
            field_name = condition[4:]  # Remove 'has_' prefix
            if isinstance(service_config, dict):
                return (
                    field_name in service_config
                    and service_config[field_name] is not None
                )
            elif hasattr(service_config, field_name):
                return getattr(service_config, field_name) is not None

        # Handle field value comparisons (field=value)
        if "=" in condition:
            field, expected_value = condition.split("=", 1)
            if isinstance(service_config, dict):
                actual_value = service_config.get(field)
            elif hasattr(service_config, field):
                actual_value = getattr(service_config, field)
            else:
                return False
            return str(actual_value) == expected_value

        # Handle negation (!field)
        if condition.startswith("!"):
            field_name = condition[1:]
            if isinstance(service_config, dict):
                return not service_config.get(field_name)
            elif hasattr(service_config, field_name):
                return not getattr(service_config, field_name)

        # Default: check if field exists and is truthy
        if isinstance(service_config, dict):
            return bool(service_config.get(condition))
        elif hasattr(service_config, condition):
            return bool(getattr(service_config, condition))

        return True

    def _get_custom_environment(self, service_id: str) -> Dict[str, str]:
        """Get custom environment variables for a service"""
        if isinstance(self.config, LabConfig):
            return self.config.custom_env.get(service_id, {})
        elif isinstance(self.config, dict) and "custom_env" in self.config:
            return self.config["custom_env"].get(service_id, {})
        else:
            return {}

    def _get_domain(self) -> str:
        """Get the primary domain from config"""
        if isinstance(self.config, LabConfig):
            return self.config.core.domain
        elif isinstance(self.config, dict) and "core" in self.config:
            return self.config["core"].get("domain", "homelab.local")
        elif hasattr(self.config, "core"):
            return self.config.core.domain
        else:
            return "homelab.local"

    def _register_volumes(self, service_id: str, volumes: List[str]) -> None:
        """Register named volumes for the compose file"""
        for volume_spec in volumes:
            if ":" in volume_spec:
                volume_name = volume_spec.split(":")[0]
                if not volume_name.startswith("./") and not volume_name.startswith("/"):
                    # This is a named volume
                    self.volumes[volume_name] = None

    def generate_compose(self) -> Dict[str, Any]:
        """Generate complete docker-compose configuration"""
        # Get enabled services
        enabled_services = self._get_enabled_services()

        # Generate services using schemas or legacy fallback
        for service_id, service_config in enabled_services.items():
            if service_id in self.schemas:
                # Use schema-based generation
                schema = self.schemas[service_id]
                compose_service = self._generate_service_from_schema(
                    service_id, service_config, schema
                )
            else:
                # Use legacy generation
                compose_service = self._generate_service_legacy(
                    service_id, service_config
                )

            if compose_service:
                self.services[service_id] = compose_service

        return {
            "version": "3.8",
            "services": self.services,
            "networks": self.networks,
            "volumes": self.volumes,
        }

    def save_compose_file(self, file_path: Path) -> None:
        """Save Docker Compose configuration to file"""
        compose_config = self.generate_compose()

        # Validate compose configuration before saving
        validation_errors = self._validate_compose_config(compose_config)
        if validation_errors:
            console.print("[yellow]⚠️  Compose validation warnings:[/yellow]")
            for error in validation_errors:
                console.print(f"  • {error}")

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            # Write header comment
            f.write("# Docker Compose configuration for Home Lab\n")
            f.write("# Generated by labctl - do not edit manually\n\n")
            yaml.dump(
                compose_config, f, default_flow_style=False, indent=2, sort_keys=False
            )

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
            "TRAEFIK_DASHBOARD_USERS=admin:$$2y$$10$$example_hash_here",
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
            "",
        ]

        with open(file_path, "w") as f:
            f.write("\n".join(env_template))

    def generate_env_vars(self) -> Dict[str, str]:
        """Generate environment variables for .env file"""
        env_vars = {}

        # Add basic environment variables
        env_vars["TZ"] = "UTC"

        # Add service-specific environment variables from config
        if isinstance(self.config, dict) and "env_vars" in self.config:
            env_vars.update(self.config["env_vars"])
        elif hasattr(self.config, "env_vars"):
            env_vars.update(self.config.env_vars)

        return env_vars

    def _validate_compose_config(self, compose_config: Dict[str, Any]) -> List[str]:
        """Validate generated compose configuration and return warnings"""
        warnings = []

        services = compose_config.get("services", {})

        # Check for missing essential fields
        for service_id, service in services.items():
            if not service.get("image"):
                warnings.append(f"Service '{service_id}' missing image specification")

            if not service.get("container_name"):
                warnings.append(f"Service '{service_id}' missing container name")

            # Check for deprecated fields
            if "links" in service:
                warnings.append(
                    f"Service '{service_id}' uses deprecated 'links'. Use 'depends_on' instead"
                )

            # Check port conflicts
            ports = service.get("ports", [])
            for port in ports:
                if isinstance(port, str) and ":" in port:
                    host_port = port.split(":")[0]
                    if host_port.isdigit() and int(host_port) < 1024:
                        warnings.append(
                            f"Service '{service_id}' uses privileged port {host_port}"
                        )

        # Check for missing networks
        networks = compose_config.get("networks", {})
        if "traefik" not in networks:
            warnings.append("Missing 'traefik' network definition")

        # Check for orphaned volumes
        volumes = compose_config.get("volumes", {})
        used_volumes = set()
        for service in services.values():
            for vol in service.get("volumes", []):
                if isinstance(vol, str) and ":" in vol:
                    vol_name = vol.split(":")[0]
                    if not vol_name.startswith("./") and not vol_name.startswith("/"):
                        used_volumes.add(vol_name)

        for volume_name in volumes:
            if volume_name not in used_volumes:
                warnings.append(f"Volume '{volume_name}' defined but not used")

        return warnings
