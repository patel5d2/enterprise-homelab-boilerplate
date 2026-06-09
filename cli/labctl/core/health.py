"""
Health checking module for Home Lab services
"""

import subprocess
from typing import Any, Dict

import requests

from .config import Config
from .exceptions import HomeLabError  # noqa: F401 — re-exported for callers


class HealthChecker:
    """Health checker for Home Lab services

    TLS certificate verification is enabled by default. It is only relaxed
    when the lab is explicitly configured to use staging certificates
    (e.g. Let's Encrypt staging), which are not signed by a trusted CA.
    """

    def __init__(self, config: Config, verify_tls: bool = True):
        self.config = config

        # Staging certificates (Let's Encrypt staging) are intentionally
        # untrusted; only in that explicitly configured case do we relax
        # verification.
        staging = bool(getattr(getattr(config, "reverse_proxy", None), "staging", False))
        self.verify_tls = verify_tls and not staging

        if not self.verify_tls:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

    def _check_https(
        self, service: str, path: str, healthy_codes: tuple = (200,)
    ) -> Dict[str, Any]:
        """Check an HTTPS endpoint for a service subdomain"""
        try:
            url = f"https://{service}.{self.config.core.domain}{path}"
            response = requests.get(url, timeout=10, verify=self.verify_tls)
            return {
                "healthy": response.status_code in healthy_codes,
                "status_code": response.status_code,
                "service": service,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "service": service}

    def check_traefik(self) -> Dict[str, Any]:
        """Check Traefik health"""
        return self._check_https("traefik", "/api/rawdata")

    def check_prometheus(self) -> Dict[str, Any]:
        """Check Prometheus health"""
        return self._check_https("prometheus", "/-/healthy")

    def check_grafana(self) -> Dict[str, Any]:
        """Check Grafana health"""
        return self._check_https("grafana", "/api/health")

    def check_gitlab(self) -> Dict[str, Any]:
        """Check GitLab health"""
        return self._check_https("gitlab", "/-/health")

    def check_vault(self) -> Dict[str, Any]:
        """Check Vault health"""
        # 429 means sealed but healthy
        return self._check_https("vault", "/v1/sys/health", healthy_codes=(200, 429))

    def check_docker_service(self, service_name: str) -> Dict[str, Any]:
        """Check Docker service status"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"name={service_name}",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            status = result.stdout.strip()
            return {
                "healthy": "Up" in status,
                "status": status,
                "service": service_name,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "service": service_name}
