"""
Docker Compose composer for Home Lab services
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from .config import Config


class ComposeGenerator:
    """Generates Docker Compose configurations for home lab services"""
    
    def __init__(self, config: Config):
        self.config = config
        self.services = {}
        self.networks = {
            "traefik": {
                "driver": "bridge"
            }
        }
        self.volumes = {}
    
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
    
    def save_compose_file(self, file_path: Path) -> None:
        """Save Docker Compose configuration to file"""
        compose_config = self.generate_compose()
        
        with open(file_path, 'w') as f:
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
    
    def generate_compose(self) -> Dict[str, Any]:
        """Generate complete docker-compose configuration"""
        # Core infrastructure services
        self._add_proxy_services()
        self._add_monitoring_services()
        self._add_database_services()
        
        # Optional services based on config
        self._add_networking_services()
        self._add_security_services()
        self._add_backup_services()
        self._add_dashboard_services()
        self._add_documentation_services()
        self._add_automation_services()
        self._add_cicd_services()
        
        return {
            "version": "3.8",
            "services": self.services,
            "networks": self.networks,
            "volumes": self.volumes
        }
    
    def _add_proxy_services(self):
        """Add reverse proxy services"""
        if self.config.proxy.traefik:
            self._add_traefik()
        if self.config.proxy.nginx_proxy_manager:
            self._add_nginx_proxy_manager()
        if self.config.proxy.caddy:
            self._add_caddy()
    
    def _add_traefik(self):
        """Add Traefik reverse proxy"""
        self.services["traefik"] = {
            "image": "traefik:v3.1",
            "container_name": "traefik",
            "restart": "unless-stopped",
            "command": [
                "--api.dashboard=true",
                "--api.insecure=false",
                "--providers.docker=true",
                "--providers.docker.exposedbydefault=false",
                "--entrypoints.web.address=:80",
                "--entrypoints.websecure.address=:443",
                "--certificatesresolvers.letsencrypt.acme.tlschallenge=true",
                f"--certificatesresolvers.letsencrypt.acme.email={self.config.core.email}",
                "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
            ],
            "ports": [
                "80:80",
                "443:443"
            ],
            "volumes": [
                "/var/run/docker.sock:/var/run/docker.sock:ro",
                "letsencrypt:/letsencrypt"
            ],
            "labels": [
                "traefik.enable=true",
                "traefik.docker.network=traefik",
                # Global HTTP -> HTTPS redirect (catch-all)
                "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https",
                "traefik.http.routers.http-catchall.rule=HostRegexp(`{host:.+}`)",
                "traefik.http.routers.http-catchall.entrypoints=web",
                "traefik.http.routers.http-catchall.middlewares=redirect-to-https@docker",
                # Security headers middleware
                "traefik.http.middlewares.secure-headers.headers.forceSTSHeader=true",
                "traefik.http.middlewares.secure-headers.headers.stsSeconds=31536000",
                "traefik.http.middlewares.secure-headers.headers.stsIncludeSubdomains=true",
                "traefik.http.middlewares.secure-headers.headers.stsPreload=true",
                "traefik.http.middlewares.secure-headers.headers.browserXssFilter=true",
                "traefik.http.middlewares.secure-headers.headers.contentTypeNosniff=true",
                "traefik.http.middlewares.secure-headers.headers.frameDeny=true",
                "traefik.http.middlewares.secure-headers.headers.referrerPolicy=no-referrer-when-downgrade",
                # Basic auth for Traefik dashboard
                "traefik.http.middlewares.dashboard-auth.basicauth.users=${TRAEFIK_DASHBOARD_USERS}",
                # Traefik dashboard Router over HTTPS to api@internal
                f"traefik.http.routers.traefik.rule=Host(`traefik.{self.config.core.domain}`)",
                "traefik.http.routers.traefik.entrypoints=websecure",
                "traefik.http.routers.traefik.tls.certresolver=letsencrypt",
                "traefik.http.routers.traefik.service=api@internal",
                "traefik.http.routers.traefik.middlewares=dashboard-auth@docker,secure-headers@docker"
            ],
            "networks": ["traefik"]
        }
        
        self.volumes["letsencrypt"] = None
    
    def _add_nginx_proxy_manager(self):
        """Add Nginx Proxy Manager"""
        self.services["nginx-proxy-manager"] = {
            "image": "jc21/nginx-proxy-manager:latest",
            "container_name": "nginx-proxy-manager",
            "restart": "unless-stopped",
            "ports": [
                "80:80",
                "443:443",
                "81:81"
            ],
            "environment": [
                "DB_MYSQL_HOST=nginx-db",
                "DB_MYSQL_PORT=3306",
                "DB_MYSQL_USER=npm",
                "DB_MYSQL_PASSWORD=npm",
                "DB_MYSQL_NAME=npm"
            ],
            "volumes": [
                "nginx-data:/data",
                "nginx-letsencrypt:/etc/letsencrypt"
            ],
            "depends_on": ["nginx-db"],
            "networks": ["traefik"]
        }
        
        self.services["nginx-db"] = {
            "image": "mysql:8.0",
            "container_name": "nginx-db",
            "restart": "unless-stopped",
            "environment": [
                "MYSQL_ROOT_PASSWORD=npm",
                "MYSQL_DATABASE=npm",
                "MYSQL_USER=npm",
                "MYSQL_PASSWORD=npm"
            ],
            "volumes": ["nginx-mysql:/var/lib/mysql"],
            "networks": ["traefik"]
        }
        
        self.volumes.update({
            "nginx-data": None,
            "nginx-letsencrypt": None,
            "nginx-mysql": None
        })
    
    def _add_caddy(self):
        """Add Caddy server"""
        self.services["caddy"] = {
            "image": "caddy:2-alpine",
            "container_name": "caddy",
            "restart": "unless-stopped",
            "ports": [
                "80:80",
                "443:443"
            ],
            "volumes": [
                "./Caddyfile:/etc/caddy/Caddyfile",
                "caddy-data:/data",
                "caddy-config:/config"
            ],
            "networks": ["traefik"]
        }
        
        self.volumes.update({
            "caddy-data": None,
            "caddy-config": None
        })
    
    def _add_monitoring_services(self):
        """Add monitoring stack"""
        if not self.config.monitoring.enabled:
            return
            
        # Prometheus
        self.services["prometheus"] = {
            "image": "prom/prometheus:latest",
            "container_name": "prometheus",
            "restart": "unless-stopped",
            "command": [
                "--config.file=/etc/prometheus/prometheus.yml",
                "--storage.tsdb.path=/prometheus",
                f"--storage.tsdb.retention.time={self.config.monitoring.retention}",
                "--web.console.libraries=/etc/prometheus/console_libraries",
                "--web.console.templates=/etc/prometheus/consoles",
                "--web.enable-lifecycle"
            ],
            "volumes": [
                "./prometheus.yml:/etc/prometheus/prometheus.yml",
                "prometheus-data:/prometheus"
            ],
            "labels": self._secure_traefik_labels("prometheus", "prometheus", self.config.monitoring.prometheus_port),
            "networks": ["traefik"]
        }
        
        # Grafana
        self.services["grafana"] = {
            "image": "grafana/grafana:latest",
            "container_name": "grafana",
            "restart": "unless-stopped",
            "environment": [
                "GF_SECURITY_ADMIN_PASSWORD=admin",
                f"GF_SERVER_DOMAIN=grafana.{self.config.core.domain}",
                "GF_SERVER_ROOT_URL=%(protocol)s://%(domain)s/"
            ],
            "volumes": [
                "grafana-data:/var/lib/grafana"
            ],
            "labels": self._secure_traefik_labels("grafana", "grafana", self.config.monitoring.grafana_port),
            "depends_on": ["prometheus"],
            "networks": ["traefik"]
        }
        
        self.volumes.update({
            "prometheus-data": None,
            "grafana-data": None
        })
    
    def _add_database_services(self):
        """Add database services"""
        if self.config.databases.postgresql:
            default_env = [
                "POSTGRES_DB=homelab",
                "POSTGRES_USER=homelab",
                "POSTGRES_PASSWORD=homelab123"
            ]
            self.services["postgres"] = {
                "image": "postgres:16",
                "container_name": "postgres",
                "restart": "unless-stopped",
                "environment": self._merge_environment_variables("postgresql", default_env),
                "volumes": [
                    "postgres-data:/var/lib/postgresql/data"
                ],
                "networks": ["traefik"]
            }
            self.volumes["postgres-data"] = None
        
        if self.config.databases.mongodb:
            default_env = [
                "MONGO_INITDB_ROOT_USERNAME=admin",
                "MONGO_INITDB_ROOT_PASSWORD=admin123"
            ]
            self.services["mongodb"] = {
                "image": "mongo:7",
                "container_name": "mongodb",
                "restart": "unless-stopped",
                "environment": self._merge_environment_variables("mongodb", default_env),
                "volumes": [
                    "mongodb-data:/data/db"
                ],
                "networks": ["traefik"]
            }
            self.volumes["mongodb-data"] = None
        
        if self.config.databases.redis:
            self.services["redis"] = {
                "image": "redis:7-alpine",
                "container_name": "redis",
                "restart": "unless-stopped",
                "volumes": [
                    "redis-data:/data"
                ],
                "networks": ["traefik"]
            }
            self.volumes["redis-data"] = None
    
    def _add_networking_services(self):
        """Add networking services"""
        if self.config.networking.cloudflared:
            self.services["cloudflared"] = {
                "image": "cloudflare/cloudflared:latest",
                "container_name": "cloudflared",
                "restart": "unless-stopped",
                "command": "tunnel --no-autoupdate run --metrics 0.0.0.0:8080",
                "environment": [
                    "TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}"
                ],
                "labels": self._secure_traefik_labels("cloudflared", "cloudflared", 8080),
                "networks": ["traefik"]
            }
        
        if self.config.networking.headscale:
            self.services["headscale"] = {
                "image": "headscale/headscale:latest",
                "container_name": "headscale",
                "restart": "unless-stopped",
                "command": "headscale serve",
                "environment": [
                    "HEADSCALE_CONFIG_FILE=/etc/headscale/config.yaml"
                ],
                "volumes": [
                    "./headscale:/etc/headscale",
                    "headscale-data:/var/lib/headscale"
                ],
                "labels": self._secure_traefik_labels("headscale", "headscale", 8080),
                "networks": ["traefik"]
            }
            self.volumes["headscale-data"] = None
        
        if self.config.networking.pihole:
            default_env = [
                "TZ=${TZ:-UTC}",
                "WEBPASSWORD=admin123",
                "DNSMASQ_LISTENING=all"
            ]
            self.services["pihole"] = {
                "image": "pihole/pihole:latest",
                "container_name": "pihole",
                "restart": "unless-stopped",
                "environment": self._merge_environment_variables("pihole", default_env),
                "volumes": [
                    "pihole-data:/etc/pihole",
                    "pihole-dnsmasq:/etc/dnsmasq.d"
                ],
                "ports": [
                    "53:53/tcp",
                    "53:53/udp"
                ],
                "labels": self._secure_traefik_labels("pihole", "pihole", 80),
                "networks": ["traefik"]
            }
            self.volumes.update({
                "pihole-data": None,
                "pihole-dnsmasq": None
            })
    
    def _add_security_services(self):
        """Add security services"""
        if self.config.vault.enabled:
            self.services["vault"] = {
                "image": "hashicorp/vault:latest",
                "container_name": "vault",
                "restart": "unless-stopped",
                "cap_add": ["IPC_LOCK"],
                "environment": [
                    "VAULT_DEV_ROOT_TOKEN_ID=myroot",
                    "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200"
                ],
                "volumes": [
                    "vault-data:/vault/data"
                ],
                "labels": self._secure_traefik_labels("vault", "vault", 8200),
                "networks": ["traefik"]
            }
            self.volumes["vault-data"] = None
        
        if self.config.passwords.vaultwarden:
            default_env = [
                f"DOMAIN=https://vault.{self.config.core.domain}",
                "SIGNUPS_ALLOWED=false",
                "ADMIN_TOKEN=${VAULTWARDEN_ADMIN_TOKEN}"
            ]
            self.services["vaultwarden"] = {
                "image": "vaultwarden/server:latest",
                "container_name": "vaultwarden",
                "restart": "unless-stopped",
                "environment": self._merge_environment_variables("vaultwarden", default_env),
                "volumes": [
                    "vaultwarden-data:/data"
                ],
                "labels": self._secure_traefik_labels("vaultwarden", "vault", 80),
                "networks": ["traefik"]
            }
            self.volumes["vaultwarden-data"] = None
    
    def _add_backup_services(self):
        """Add backup services"""
        if self.config.backups.enabled and self.config.backups.backrest:
            self.services["pgbackrest"] = {
                "image": "pgbackrest/pgbackrest:latest",
                "container_name": "pgbackrest",
                "restart": "unless-stopped",
                "environment": [
                    "PGBACKREST_REPO1_TYPE=s3",
                    f"PGBACKREST_REPO1_S3_ENDPOINT={getattr(self.config.backups, 's3_endpoint', '')}",
                    "PGBACKREST_REPO1_S3_BUCKET=${BACKUP_S3_BUCKET}",
                    "PGBACKREST_REPO1_S3_KEY=${BACKUP_S3_KEY}",
                    "PGBACKREST_REPO1_S3_KEY_SECRET=${BACKUP_S3_SECRET}"
                ],
                "volumes": [
                    "pgbackrest-config:/etc/pgbackrest",
                    "pgbackrest-spool:/var/spool/pgbackrest"
                ],
                "networks": ["traefik"]
            }
            self.volumes.update({
                "pgbackrest-config": None,
                "pgbackrest-spool": None
            })
    
    def _add_dashboard_services(self):
        """Add dashboard services"""
        if getattr(self.config, 'dashboards', None) and getattr(self.config.dashboards, 'glance', False):
            self.services["glance"] = {
                "image": "glanceapp/glance:latest",
                "container_name": "glance",
                "restart": "unless-stopped",
                "environment": [
                    f"GLANCE_DOMAIN=dashboard.{self.config.core.domain}"
                ],
                "volumes": [
                    "./glance.yml:/app/glance.yml",
                    "glance-data:/app/data"
                ],
                "labels": self._secure_traefik_labels("glance", "dashboard", 8080),
                "networks": ["traefik"]
            }
            self.volumes["glance-data"] = None
        
        if getattr(self.config, 'dashboards', None) and getattr(self.config.dashboards, 'uptime_kuma', False):
            self.services["uptime-kuma"] = {
                "image": "louislam/uptime-kuma:1",
                "container_name": "uptime-kuma",
                "restart": "unless-stopped",
                "volumes": [
                    "uptime-kuma:/app/data"
                ],
                "labels": self._secure_traefik_labels("uptime-kuma", "uptime", 3001),
                "networks": ["traefik"]
            }
            self.volumes["uptime-kuma"] = None
    
    def _add_documentation_services(self):
        """Add documentation services"""
        if getattr(self.config, 'documentation', None) and getattr(self.config.documentation, 'fumadocs', False):
            self.services["fumadocs"] = {
                "image": "fumadocs/fumadocs:latest", 
                "container_name": "fumadocs",
                "restart": "unless-stopped",
                "volumes": [
                    "fumadocs-data:/app/data"
                ],
                "labels": self._secure_traefik_labels("fumadocs", "docs", 3000),
                "networks": ["traefik"]
            }
            self.volumes["fumadocs-data"] = None
    
    def _add_automation_services(self):
        """Add automation services"""
        if getattr(self.config, 'automation', None) and getattr(self.config.automation, 'n8n', False):
            default_env = [
                f"WEBHOOK_URL=https://automation.{self.config.core.domain}",
                "N8N_HOST=0.0.0.0",
                "N8N_PORT=5678"
            ]
            self.services["n8n"] = {
                "image": "docker.n8n.io/n8nio/n8n",
                "container_name": "n8n",
                "restart": "unless-stopped",
                "environment": self._merge_environment_variables("n8n", default_env),
                "volumes": [
                    "n8n-data:/home/node/.n8n"
                ],
                "labels": self._secure_traefik_labels("n8n", "automation", 5678),
                "networks": ["traefik"]
            }
            self.volumes["n8n-data"] = None
    
    def _add_cicd_services(self):
        """Add CI/CD services"""
        if getattr(self.config, 'ci_cd', None) and getattr(self.config.ci_cd, 'gitlab', False):
            self.services["gitlab"] = {
                "image": "gitlab/gitlab-ce:latest",
                "container_name": "gitlab",
                "restart": "unless-stopped",
                "hostname": f"gitlab.{self.config.core.domain}",
                "environment": [
                    f"GITLAB_OMNIBUS_CONFIG=external_url 'https://gitlab.{self.config.core.domain}'"
                ],
                "volumes": [
                    "gitlab-config:/etc/gitlab",
                    "gitlab-logs:/var/log/gitlab", 
                    "gitlab-data:/var/opt/gitlab"
                ],
                "labels": self._secure_traefik_labels("gitlab", "gitlab", 80),
                "networks": ["traefik"]
            }
            self.volumes.update({
                "gitlab-config": None,
                "gitlab-logs": None,
                "gitlab-data": None
            })
        
        if getattr(self.config, 'ci_cd', None) and getattr(self.config.ci_cd, 'jenkins', False):
            self.services["jenkins"] = {
                "image": "jenkins/jenkins:lts",
                "container_name": "jenkins",
                "restart": "unless-stopped",
                "user": "root",
                "environment": [
                    "JENKINS_OPTS=--httpPort=8080"
                ],
                "volumes": [
                    "jenkins-data:/var/jenkins_home",
                    "/var/run/docker.sock:/var/run/docker.sock"
                ],
                "labels": self._secure_traefik_labels("jenkins", "jenkins", 8080),
                "networks": ["traefik"]
            }
            self.volumes["jenkins-data"] = None
        
        with open(output_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")