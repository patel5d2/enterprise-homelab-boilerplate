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
                "--api.insecure=true",
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
                "443:443",
                "8080:8080"
            ],
            "volumes": [
                "/var/run/docker.sock:/var/run/docker.sock:ro",
                "letsencrypt:/letsencrypt"
            ],
            "labels": [
                "traefik.enable=true",
                f"traefik.http.routers.traefik.rule=Host(`traefik.{self.config.core.domain}`)",
                "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
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
            "labels": [
                "traefik.enable=true",
                f"traefik.http.routers.prometheus.rule=Host(`prometheus.{self.config.core.domain}`)",
                "traefik.http.routers.prometheus.tls.certresolver=letsencrypt",
                f"traefik.http.services.prometheus.loadbalancer.server.port={self.config.monitoring.prometheus_port}"
            ],
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
            "labels": [
                "traefik.enable=true",
                f"traefik.http.routers.grafana.rule=Host(`grafana.{self.config.core.domain}`)",
                "traefik.http.routers.grafana.tls.certresolver=letsencrypt",
                f"traefik.http.services.grafana.loadbalancer.server.port={self.config.monitoring.grafana_port}"
            ],
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
            self.services["postgres"] = {
                "image": "postgres:16",
                "container_name": "postgres",
                "restart": "unless-stopped",
                "environment": [
                    "POSTGRES_DB=homelab",
                    "POSTGRES_USER=homelab",
                    "POSTGRES_PASSWORD=homelab123"
                ],
                "volumes": [
                    "postgres-data:/var/lib/postgresql/data"
                ],
                "networks": ["traefik"]
            }
            self.volumes["postgres-data"] = None
        
        if self.config.databases.mongodb:
            self.services["mongodb"] = {
                "image": "mongo:7",
                "container_name": "mongodb",
                "restart": "unless-stopped",
                "environment": [
                    "MONGO_INITDB_ROOT_USERNAME=admin",
                    "MONGO_INITDB_ROOT_PASSWORD=admin123"
                ],
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
                "command": "tunnel --no-autoupdate run",
                "environment": [
                    "TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}"
                ],
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
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.headscale.rule=Host(`headscale.{self.config.core.domain}`)",
                    "traefik.http.routers.headscale.tls.certresolver=letsencrypt",
                    "traefik.http.services.headscale.loadbalancer.server.port=8080"
                ],
                "networks": ["traefik"]
            }
            self.volumes["headscale-data"] = None
        
        if self.config.networking.pihole:
            self.services["pihole"] = {
                "image": "pihole/pihole:latest",
                "container_name": "pihole",
                "restart": "unless-stopped",
                "environment": [
                    "TZ=${TZ:-UTC}",
                    "WEBPASSWORD=admin123",
                    "DNSMASQ_LISTENING=all"
                ],
                "volumes": [
                    "pihole-data:/etc/pihole",
                    "pihole-dnsmasq:/etc/dnsmasq.d"
                ],
                "ports": [
                    "53:53/tcp",
                    "53:53/udp"
                ],
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.pihole.rule=Host(`pihole.{self.config.core.domain}`)",
                    "traefik.http.routers.pihole.tls.certresolver=letsencrypt",
                    "traefik.http.services.pihole.loadbalancer.server.port=80"
                ],
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
                "image": "vault:latest",
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
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.vault.rule=Host(`vault.{self.config.core.domain}`)",
                    "traefik.http.routers.vault.tls.certresolver=letsencrypt",
                    "traefik.http.services.vault.loadbalancer.server.port=8200"
                ],
                "networks": ["traefik"]
            }
            self.volumes["vault-data"] = None
        
        if self.config.passwords.vaultwarden:
            self.services["vaultwarden"] = {
                "image": "vaultwarden/server:latest",
                "container_name": "vaultwarden",
                "restart": "unless-stopped",
                "environment": [
                    f"DOMAIN=https://vault.{self.config.core.domain}",
                    "SIGNUPS_ALLOWED=false",
                    "ADMIN_TOKEN=${VAULTWARDEN_ADMIN_TOKEN}"
                ],
                "volumes": [
                    "vaultwarden-data:/data"
                ],
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.vaultwarden.rule=Host(`vault.{self.config.core.domain}`)",
                    "traefik.http.routers.vaultwarden.tls.certresolver=letsencrypt",
                    "traefik.http.services.vaultwarden.loadbalancer.server.port=80"
                ],
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
                    f"PGBACKREST_REPO1_S3_ENDPOINT={self.config.backups.s3_endpoint}",
                    "PGBACKREST_REPO1_S3_BUCKET=${BACKUP_S3_BUCKET}",
                    "PGBACKREST_REPO1_S3_KEY=${BACKUP_S3_KEY}",
                    "PGBACKREST_REPO1_S3_KEY_SECRET=${BACKUP_S3_SECRET}"
                ],
                "volumes": [
                    "pgbackrest-config:/etc/pgbackrest"
                ],
                "depends_on": ["postgres"],
                "networks": ["traefik"]
            }
            self.volumes["pgbackrest-config"] = None
    
    def _add_dashboard_services(self):
        """Add dashboard services"""
        if self.config.dashboards.glance:
            self.services["glance"] = {
                "image": "glanceapp/glance:latest",
                "container_name": "glance",
                "restart": "unless-stopped",
                "volumes": [
                    "./glance.yml:/app/glance.yml",
                    "glance-data:/app/data"
                ],
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.glance.rule=Host(`dashboard.{self.config.core.domain}`)",
                    "traefik.http.routers.glance.tls.certresolver=letsencrypt",
                    "traefik.http.services.glance.loadbalancer.server.port=8080"
                ],
                "networks": ["traefik"]
            }
            self.volumes["glance-data"] = None
        
        if self.config.dashboards.uptime_kuma:
            self.services["uptime-kuma"] = {
                "image": "louislam/uptime-kuma:1",
                "container_name": "uptime-kuma",
                "restart": "unless-stopped",
                "volumes": [
                    "uptime-kuma-data:/app/data"
                ],
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.uptime-kuma.rule=Host(`uptime.{self.config.core.domain}`)",
                    "traefik.http.routers.uptime-kuma.tls.certresolver=letsencrypt",
                    "traefik.http.services.uptime-kuma.loadbalancer.server.port=3001"
                ],
                "networks": ["traefik"]
            }
            self.volumes["uptime-kuma-data"] = None
    
    def _add_documentation_services(self):
        """Add documentation services"""
        if self.config.documentation.fumadocs:
            self.services["fumadocs"] = {
                "image": "node:18-alpine",
                "container_name": "fumadocs",
                "restart": "unless-stopped",
                "working_dir": "/app",
                "command": "npm run start",
                "volumes": [
                    "./docs:/app",
                    "fumadocs-modules:/app/node_modules"
                ],
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.fumadocs.rule=Host(`docs.{self.config.core.domain}`)",
                    "traefik.http.routers.fumadocs.tls.certresolver=letsencrypt",
                    "traefik.http.services.fumadocs.loadbalancer.server.port=3000"
                ],
                "networks": ["traefik"]
            }
            self.volumes["fumadocs-modules"] = None
    
    def _add_automation_services(self):
        """Add automation services"""
        if self.config.automation.n8n:
            self.services["n8n"] = {
                "image": "n8nio/n8n:latest",
                "container_name": "n8n",
                "restart": "unless-stopped",
                "environment": [
                    f"WEBHOOK_URL=https://automation.{self.config.core.domain}",
                    "GENERIC_TIMEZONE=${TZ:-UTC}",
                    "N8N_SECURE_COOKIE=false"
                ],
                "volumes": [
                    "n8n-data:/home/node/.n8n"
                ],
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.n8n.rule=Host(`automation.{self.config.core.domain}`)",
                    "traefik.http.routers.n8n.tls.certresolver=letsencrypt",
                    "traefik.http.services.n8n.loadbalancer.server.port=5678"
                ],
                "networks": ["traefik"]
            }
            self.volumes["n8n-data"] = None
    
    def _add_cicd_services(self):
        """Add CI/CD services"""
        if self.config.gitlab.enabled or self.config.ci_cd.gitlab:
            self.services["gitlab"] = {
                "image": "gitlab/gitlab-ee:latest",
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
                "shm_size": "256m",
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.gitlab.rule=Host(`gitlab.{self.config.core.domain}`)",
                    "traefik.http.routers.gitlab.tls.certresolver=letsencrypt",
                    "traefik.http.services.gitlab.loadbalancer.server.port=80"
                ],
                "networks": ["traefik"]
            }
            self.volumes.update({
                "gitlab-config": None,
                "gitlab-logs": None,
                "gitlab-data": None
            })
        
        if self.config.ci_cd.jenkins:
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
                "labels": [
                    "traefik.enable=true",
                    f"traefik.http.routers.jenkins.rule=Host(`jenkins.{self.config.core.domain}`)",
                    "traefik.http.routers.jenkins.tls.certresolver=letsencrypt",
                    "traefik.http.services.jenkins.loadbalancer.server.port=8080"
                ],
                "networks": ["traefik"]
            }
            self.volumes["jenkins-data"] = None
    
    def save_compose_file(self, output_path: Path):
        """Save the generated compose configuration to a file"""
        compose_config = self.generate_compose()
        
        with open(output_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2, sort_keys=False)
    
    def generate_env_template(self) -> Dict[str, str]:
        """Generate environment variable template"""
        env_vars = {
            "CLOUDFLARE_TUNNEL_TOKEN": "your-cloudflare-tunnel-token",
            "VAULTWARDEN_ADMIN_TOKEN": "your-vaultwarden-admin-token",
            "BACKUP_S3_BUCKET": "your-backup-bucket",
            "BACKUP_S3_KEY": "your-s3-access-key",
            "BACKUP_S3_SECRET": "your-s3-secret-key",
            "TZ": self.config.core.timezone
        }
        return env_vars
    
    def save_env_template(self, output_path: Path):
        """Save environment template file"""
        env_vars = self.generate_env_template()
        
        with open(output_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")