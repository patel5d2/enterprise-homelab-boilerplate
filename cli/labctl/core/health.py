"""
Health checking module for Home Lab services
"""

import requests
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

from .config import Config
from .exceptions import HealthCheckError, NetworkError


class HealthChecker:
    """Health checker for Home Lab services"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all enabled services"""
        results = {}
        
        # Check core services
        if self.config.reverse_proxy.provider == "traefik":
            results["traefik"] = self.check_traefik()
        
        # Check monitoring services
        if self.config.monitoring.enabled:
            results["prometheus"] = self.check_prometheus()
            results["grafana"] = self.check_grafana()
        
        # Check GitLab
        if self.config.gitlab.enabled:
            results["gitlab"] = self.check_gitlab()
        
        # Check Vault
        if self.config.vault.enabled:
            results["vault"] = self.check_vault()
        
        return results
    
    def check_traefik(self) -> Dict[str, Any]:
        """Check Traefik health"""
        try:
            url = f"https://traefik.{self.config.core.domain}/api/rawdata"
            response = requests.get(url, timeout=10, verify=False)
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "service": "traefik"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "service": "traefik"
            }
    
    def check_prometheus(self) -> Dict[str, Any]:
        """Check Prometheus health"""
        try:
            url = f"https://prometheus.{self.config.core.domain}/-/healthy"
            response = requests.get(url, timeout=10, verify=False)
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "service": "prometheus"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "service": "prometheus"
            }
    
    def check_grafana(self) -> Dict[str, Any]:
        """Check Grafana health"""
        try:
            url = f"https://grafana.{self.config.core.domain}/api/health"
            response = requests.get(url, timeout=10, verify=False)
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "service": "grafana"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "service": "grafana"
            }
    
    def check_gitlab(self) -> Dict[str, Any]:
        """Check GitLab health"""
        try:
            url = f"https://gitlab.{self.config.core.domain}/-/health"
            response = requests.get(url, timeout=10, verify=False)
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "service": "gitlab"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "service": "gitlab"
            }
    
    def check_vault(self) -> Dict[str, Any]:
        """Check Vault health"""
        try:
            url = f"https://vault.{self.config.core.domain}/v1/sys/health"
            response = requests.get(url, timeout=10, verify=False)
            return {
                "healthy": response.status_code in [200, 429],  # 429 is sealed but healthy
                "status_code": response.status_code,
                "service": "vault"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "service": "vault"
            }
    
    def check_docker_service(self, service_name: str) -> Dict[str, Any]:
        """Check Docker service status"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Status}}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            status = result.stdout.strip()
            return {
                "healthy": "Up" in status,
                "status": status,
                "service": service_name
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "service": service_name
            }