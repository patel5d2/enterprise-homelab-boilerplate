#!/usr/bin/env python3
"""
Infrastructure Generator
Converts the detailed configuration into Docker Compose files
"""

import os
import sys
import yaml
import secrets
import string
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from rich.console import Console
    from rich.progress import track
    from rich.panel import Panel
except ImportError:
    print("Installing dependencies...")
    os.system("pip install rich")
    from rich.console import Console
    from rich.progress import track
    from rich.panel import Panel

console = Console()

class InfrastructureGenerator:
    def __init__(self, config_file: str = "homelab-config.yaml"):
        self.config_file = Path(config_file)
        self.config = {}
        self.compose_services = {}
        self.compose_volumes = {}
        self.compose_networks = {"traefik": {"driver": "bridge"}}
        self.env_vars = {}
        
    def load_configuration(self):
        """Load the detailed configuration"""
        if not self.config_file.exists():
            console.print(f"[red]Configuration file {self.config_file} not found![/red]")
            console.print("Run the interactive setup first: [cyan]./labctl init[/cyan]")
            sys.exit(1)
            
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        console.print(f"✅ Loaded configuration from {self.config_file}")
    
    def generate_infrastructure(self):
        """Generate Docker Compose infrastructure"""
        console.print("\n🏗️ [bold]Generating Infrastructure...[/bold]")
        
        enabled_services = list(self.config.get('services', {}).keys())
        
        for service_name in track(enabled_services, description="Generating services..."):
            if service_name == 'traefik':
                self.generate_traefik()
            elif service_name == 'postgresql':
                self.generate_postgresql()
            elif service_name == 'redis':
                self.generate_redis()
            elif service_name == 'prometheus':
                self.generate_prometheus()
            elif service_name == 'grafana':
                self.generate_grafana()
            elif service_name == 'uptime_kuma':
                self.generate_uptime_kuma()
            elif service_name == 'glance':
                self.generate_glance()
            elif service_name == 'pihole':
                self.generate_pihole()
            elif service_name == 'headscale':
                self.generate_headscale()
            elif service_name == 'cloudflared':
                self.generate_cloudflared()
            elif service_name == 'vaultwarden':
                self.generate_vaultwarden()
            elif service_name == 'vault':
                self.generate_vault()
            elif service_name == 'gitlab':
                self.generate_gitlab()
            elif service_name == 'jenkins':
                self.generate_jenkins()
            elif service_name == 'gitea':
                self.generate_gitea()
            elif service_name == 'mongodb':
                self.generate_mongodb()
            elif service_name == 'minio':
                self.generate_minio()
            elif service_name == 'n8n':
                self.generate_n8n()
            elif service_name == 'home_assistant':
                self.generate_home_assistant()
            elif service_name == 'node_red':
                self.generate_node_red()
            elif service_name == 'bookstack':
                self.generate_bookstack()
            elif service_name == 'outline':
                self.generate_outline()
            elif service_name == 'dokuwiki':
                self.generate_dokuwiki()
            elif service_name == 'jellyfin':
                self.generate_jellyfin()
            elif service_name == 'nextcloud':
                self.generate_nextcloud()
            elif service_name == 'photoprism':
                self.generate_photoprism()
            elif service_name == 'nginx_proxy_manager':
                self.generate_nginx_proxy_manager()
            elif service_name == 'caddy':
                self.generate_caddy()
            elif service_name == 'haproxy':
                self.generate_haproxy()
    
    def generate_traefik(self):
        """Generate Traefik reverse proxy"""
        domain = self.config['core']['domain']
        traefik_config = self.config['services'].get('traefik', {})
        ssl_config = traefik_config.get('ssl', {})
        
        command = [
            "--api.dashboard=true",
            "--providers.docker=true",
            "--providers.docker.exposedbydefault=false",
            "--entrypoints.web.address=:80",
            "--entrypoints.websecure.address=:443",
        ]
        
        # SSL Configuration
        if ssl_config.get('provider') == 'letsencrypt':
            command.extend([
                "--certificatesresolvers.letsencrypt.acme.tlschallenge=true",
                f"--certificatesresolvers.letsencrypt.acme.email={ssl_config.get('email')}",
                "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
            ])
            
            if ssl_config.get('staging', False):
                command.append("--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory")
        
        labels = ["traefik.enable=true"]
        if traefik_config.get('dashboard', {}).get('enabled', True):
            labels.extend([
                f"traefik.http.routers.traefik.rule=Host(`traefik.{domain}`)",
                "traefik.http.routers.traefik.tls.certresolver=letsencrypt" if ssl_config.get('provider') == 'letsencrypt' else ""
            ])
        
        self.compose_services['traefik'] = {
            "image": "traefik:v3.1",
            "container_name": "traefik",
            "restart": "unless-stopped",
            "command": command,
            "ports": ["80:80", "443:443", "8080:8080"],
            "volumes": [
                "/var/run/docker.sock:/var/run/docker.sock:ro",
                "letsencrypt:/letsencrypt"
            ],
            "labels": [label for label in labels if label],
            "networks": ["traefik"]
        }
        
        self.compose_volumes['letsencrypt'] = None
    
    def generate_postgresql(self):
        """Generate PostgreSQL database"""
        pg_config = self.config['services'].get('postgresql', {})
        db_config = pg_config.get('database', {})
        storage_config = pg_config.get('storage', {})
        
        # Generate secure password
        db_password = self.generate_password()
        self.env_vars['POSTGRES_PASSWORD'] = db_password
        
        self.compose_services['postgres'] = {
            "image": "postgres:16",
            "container_name": "postgres",
            "restart": "unless-stopped",
            "environment": [
                f"POSTGRES_DB={db_config.get('name', 'homelab')}",
                f"POSTGRES_USER={db_config.get('user', 'postgres')}",
                "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
            ],
            "volumes": ["postgres-data:/var/lib/postgresql/data"],
            "networks": ["traefik"],
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            }
        }
        
        self.compose_volumes['postgres-data'] = None
        
        # Add backup container if enabled
        backup_config = pg_config.get('backup', {})
        if backup_config.get('enabled', False):
            self.generate_postgres_backup(backup_config)
    
    def generate_postgres_backup(self, backup_config):
        """Generate PostgreSQL backup service"""
        self.compose_services['postgres-backup'] = {
            "image": "postgres:16",
            "container_name": "postgres-backup",
            "restart": "unless-stopped",
            "environment": [
                "PGUSER=postgres",
                "PGPASSWORD=${POSTGRES_PASSWORD}",
                "PGHOST=postgres"
            ],
            "volumes": ["postgres-backups:/backups"],
            "networks": ["traefik"],
            "depends_on": ["postgres"],
            "command": [
                "sh", "-c",
                f"while true; do sleep 86400; pg_dumpall -h postgres > /backups/backup-$(date +%Y%m%d-%H%M%S).sql; find /backups -name '*.sql' -mtime +{backup_config.get('retention_days', 30)} -delete; done"
            ]
        }
        
        self.compose_volumes['postgres-backups'] = None
    
    def generate_redis(self):
        """Generate Redis service"""
        self.compose_services['redis'] = {
            "image": "redis:7-alpine",
            "container_name": "redis",
            "restart": "unless-stopped",
            "volumes": ["redis-data:/data"],
            "networks": ["traefik"],
            "healthcheck": {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            }
        }
        
        self.compose_volumes['redis-data'] = None
    
    def generate_grafana(self):
        """Generate Grafana service"""
        domain = self.config['core']['domain']
        grafana_config = self.config['services'].get('grafana', {})
        
        # Generate admin password
        admin_password = self.generate_password()
        self.env_vars['GRAFANA_ADMIN_PASSWORD'] = admin_password
        
        environment = [
            "GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}",
            f"GF_SERVER_DOMAIN=grafana.{domain}",
            "GF_SERVER_ROOT_URL=%(protocol)s://%(domain)s/",
            f"GF_DEFAULT_THEME={grafana_config.get('theme', 'dark')}"
        ]
        
        # Add plugins
        plugins = grafana_config.get('plugins', [])
        if plugins:
            environment.append(f"GF_INSTALL_PLUGINS={','.join(plugins)}")
        
        self.compose_services['grafana'] = {
            "image": "grafana/grafana:latest",
            "container_name": "grafana",
            "restart": "unless-stopped",
            "environment": environment,
            "volumes": ["grafana-data:/var/lib/grafana"],
            "labels": [
                "traefik.enable=true",
                f"traefik.http.routers.grafana.rule=Host(`grafana.{domain}`)",
                "traefik.http.routers.grafana.tls.certresolver=letsencrypt",
                "traefik.http.services.grafana.loadbalancer.server.port=3000"
            ],
            "networks": ["traefik"],
            "depends_on": ["prometheus"]
        }
        
        self.compose_volumes['grafana-data'] = None
    
    def generate_prometheus(self):
        """Generate Prometheus service"""
        domain = self.config['core']['domain']
        
        self.compose_services['prometheus'] = {
            "image": "prom/prometheus:latest",
            "container_name": "prometheus",
            "restart": "unless-stopped",
            "command": [
                "--config.file=/etc/prometheus/prometheus.yml",
                "--storage.tsdb.path=/prometheus",
                "--storage.tsdb.retention.time=30d",
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
                f"traefik.http.routers.prometheus.rule=Host(`prometheus.{domain}`)",
                "traefik.http.routers.prometheus.tls.certresolver=letsencrypt",
                "traefik.http.services.prometheus.loadbalancer.server.port=9090"
            ],
            "networks": ["traefik"]
        }
        
        self.compose_volumes['prometheus-data'] = None
    
    def generate_vaultwarden(self):
        """Generate Vaultwarden password manager"""
        domain = self.config['core']['domain']
        vw_config = self.config['services'].get('vaultwarden', {})
        
        # Generate admin token
        admin_token = self.generate_password(32)
        self.env_vars['VAULTWARDEN_ADMIN_TOKEN'] = admin_token
        
        environment = [
            f"DOMAIN=https://vault.{domain}",
            f"SIGNUPS_ALLOWED={'true' if vw_config.get('signups_allowed', False) else 'false'}",
            "ADMIN_TOKEN=${VAULTWARDEN_ADMIN_TOKEN}" if vw_config.get('admin_enabled', True) else ""
        ]
        
        # Email configuration
        email_config = vw_config.get('email', {})
        if email_config:
            environment.extend([
                f"SMTP_HOST={email_config.get('smtp_host', '')}",
                f"SMTP_PORT={email_config.get('smtp_port', 587)}",
                f"SMTP_USERNAME={email_config.get('smtp_user', '')}"
            ])
        
        self.compose_services['vaultwarden'] = {
            "image": "vaultwarden/server:latest",
            "container_name": "vaultwarden",
            "restart": "unless-stopped",
            "environment": [env for env in environment if env],
            "volumes": ["vaultwarden-data:/data"],
            "labels": [
                "traefik.enable=true",
                f"traefik.http.routers.vaultwarden.rule=Host(`vault.{domain}`)",
                "traefik.http.routers.vaultwarden.tls.certresolver=letsencrypt",
                "traefik.http.services.vaultwarden.loadbalancer.server.port=80"
            ],
            "networks": ["traefik"]
        }
        
        self.compose_volumes['vaultwarden-data'] = None
    
    def generate_nextcloud(self):
        """Generate Nextcloud service"""
        domain = self.config['core']['domain']
        nc_config = self.config['services'].get('nextcloud', {})
        
        # Generate passwords
        admin_password = self.generate_password()
        db_password = self.generate_password()
        
        self.env_vars['NEXTCLOUD_ADMIN_PASSWORD'] = admin_password
        self.env_vars['NEXTCLOUD_DB_PASSWORD'] = db_password
        
        # Nextcloud database
        self.compose_services['nextcloud-db'] = {
            "image": "mariadb:10",
            "container_name": "nextcloud-db",
            "restart": "unless-stopped",
            "environment": [
                "MYSQL_ROOT_PASSWORD=${NEXTCLOUD_DB_PASSWORD}",
                "MYSQL_DATABASE=nextcloud",
                "MYSQL_USER=nextcloud",
                "MYSQL_PASSWORD=${NEXTCLOUD_DB_PASSWORD}"
            ],
            "volumes": ["nextcloud-db:/var/lib/mysql"],
            "networks": ["traefik"]
        }
        
        # Nextcloud app
        self.compose_services['nextcloud'] = {
            "image": "nextcloud:latest",
            "container_name": "nextcloud",
            "restart": "unless-stopped",
            "environment": [
                "MYSQL_HOST=nextcloud-db",
                "MYSQL_DATABASE=nextcloud",
                "MYSQL_USER=nextcloud",
                "MYSQL_PASSWORD=${NEXTCLOUD_DB_PASSWORD}",
                f"NEXTCLOUD_ADMIN_USER={nc_config.get('admin_user', 'admin')}",
                "NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_ADMIN_PASSWORD}",
                f"NEXTCLOUD_TRUSTED_DOMAINS=nextcloud.{domain}"
            ],
            "volumes": [
                "nextcloud-data:/var/www/html",
                "nextcloud-apps:/var/www/html/custom_apps",
                "nextcloud-config:/var/www/html/config"
            ],
            "labels": [
                "traefik.enable=true",
                f"traefik.http.routers.nextcloud.rule=Host(`nextcloud.{domain}`)",
                "traefik.http.routers.nextcloud.tls.certresolver=letsencrypt",
                "traefik.http.services.nextcloud.loadbalancer.server.port=80"
            ],
            "networks": ["traefik"],
            "depends_on": ["nextcloud-db"]
        }
        
        self.compose_volumes.update({
            'nextcloud-db': None,
            'nextcloud-data': None,
            'nextcloud-apps': None,
            'nextcloud-config': None
        })
    
    def generate_pihole(self):
        """Generate Pi-hole DNS service"""
        domain = self.config['core']['domain']
        pihole_config = self.config['services'].get('pihole', {})
        dns_config = pihole_config.get('dns', {})
        
        # Generate web password
        web_password = self.generate_password()
        self.env_vars['PIHOLE_PASSWORD'] = web_password
        
        environment = [
            f"TZ={self.config['core'].get('timezone', 'UTC')}",
            "WEBPASSWORD=${PIHOLE_PASSWORD}",
            "DNSMASQ_LISTENING=all"
        ]
        
        # Add upstream DNS
        upstream_dns = dns_config.get('upstream', ['1.1.1.1', '8.8.8.8'])
        if upstream_dns:
            environment.append(f"PIHOLE_DNS_={';'.join(upstream_dns)}")
        
        labels = []
        if pihole_config.get('web_interface', {}).get('enabled', True):
            labels = [
                "traefik.enable=true",
                f"traefik.http.routers.pihole.rule=Host(`pihole.{domain}`)",
                "traefik.http.routers.pihole.tls.certresolver=letsencrypt",
                "traefik.http.services.pihole.loadbalancer.server.port=80"
            ]
        
        self.compose_services['pihole'] = {
            "image": "pihole/pihole:latest",
            "container_name": "pihole",
            "restart": "unless-stopped",
            "environment": environment,
            "volumes": [
                "pihole-data:/etc/pihole",
                "pihole-dnsmasq:/etc/dnsmasq.d"
            ],
            "ports": ["53:53/tcp", "53:53/udp"],
            "labels": labels,
            "networks": ["traefik"]
        }
        
        self.compose_volumes.update({
            'pihole-data': None,
            'pihole-dnsmasq': None
        })
    
    def generate_password(self, length: int = 16) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def save_docker_compose(self):
        """Save Docker Compose file"""
        compose_config = {
            "version": "3.8",
            "services": self.compose_services,
            "networks": self.compose_networks,
            "volumes": self.compose_volumes
        }
        
        compose_path = Path("docker-compose.yml")
        with open(compose_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2, sort_keys=False)
        
        console.print(f"✅ Generated {compose_path}")
    
    def save_environment_file(self):
        """Save environment variables file"""
        env_path = Path(".env")
        
        with open(env_path, 'w') as f:
            f.write("# Home Lab Environment Variables\n")
            f.write("# Generated automatically - DO NOT COMMIT TO VERSION CONTROL\n\n")
            
            for key, value in self.env_vars.items():
                f.write(f"{key}={value}\n")
            
            # Add timezone
            f.write(f"\nTZ={self.config['core'].get('timezone', 'UTC')}\n")
        
        console.print(f"✅ Generated {env_path}")
        console.print("[yellow]⚠️  Keep .env file secure - it contains passwords![/yellow]")
    
    def save_supporting_files(self):
        """Save supporting configuration files"""
        # Prometheus configuration
        if 'prometheus' in self.config.get('services', {}):
            prometheus_config = {
                'global': {
                    'scrape_interval': '15s',
                    'evaluation_interval': '15s'
                },
                'scrape_configs': [
                    {
                        'job_name': 'prometheus',
                        'static_configs': [{'targets': ['localhost:9090']}]
                    },
                    {
                        'job_name': 'traefik',
                        'static_configs': [{'targets': ['traefik:8080']}]
                    }
                ]
            }
            
            with open("prometheus.yml", 'w') as f:
                yaml.dump(prometheus_config, f, default_flow_style=False, indent=2)
            
            console.print("✅ Generated prometheus.yml")
    
    def show_summary(self):
        """Show deployment summary"""
        domain = self.config['core']['domain']
        enabled_services = list(self.config.get('services', {}).keys())
        
        summary_text = f"""
🎉 [bold green]Infrastructure Generated![/bold green]

📦 [bold]Services ({len(enabled_services)}):[/bold] {', '.join(enabled_services)}

🌐 [bold]Service URLs:[/bold]
• Traefik Dashboard: https://traefik.{domain}
• Grafana: https://grafana.{domain}
• Prometheus: https://prometheus.{domain}
"""
        
        if 'vaultwarden' in enabled_services:
            summary_text += f"• Vaultwarden: https://vault.{domain}\n"
        if 'nextcloud' in enabled_services:
            summary_text += f"• Nextcloud: https://nextcloud.{domain}\n"
        if 'pihole' in enabled_services:
            summary_text += f"• Pi-hole: https://pihole.{domain}\n"
        
        summary_text += """
🚀 [bold]Deploy Commands:[/bold]

1. Start services:   docker compose up -d
2. Check status:     docker compose ps
3. View logs:        docker compose logs -f
4. Stop services:    docker compose down

💡 [bold]First-time setup:[/bold]
• Check .env file for generated passwords
• Wait 2-3 minutes for services to initialize
• Access Traefik dashboard first to verify SSL
        """
        
        panel = Panel(
            summary_text.strip(),
            title="🏠 Home Lab Infrastructure Ready",
            border_style="bright_green",
            padding=(1, 2)
        )
        
        console.print(panel)

def main():
    generator = InfrastructureGenerator()
    
    try:
        generator.load_configuration()
        generator.generate_infrastructure()
        generator.save_docker_compose()
        generator.save_environment_file()
        generator.save_supporting_files()
        generator.show_summary()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()