"""
Custom exceptions for Home Lab CLI
"""

from typing import Any, Dict, List, Optional


class HomeLabError(Exception):
    """Base exception for Home Lab CLI"""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(HomeLabError):
    """Configuration-related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class ValidationError(HomeLabError):
    """Configuration validation errors"""

    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        self.errors = errors or []
        super().__init__(message, "VALIDATION_ERROR", {"errors": self.errors})


class DeploymentError(HomeLabError):
    """Deployment-related errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DEPLOYMENT_ERROR", details)


class ServiceError(HomeLabError):
    """Service management errors"""

    def __init__(
        self, message: str, service: str = "", details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if service:
            details["service"] = service
        super().__init__(message, "SERVICE_ERROR", details)


class NetworkError(HomeLabError):
    """Network connectivity errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NETWORK_ERROR", details)


class HealthCheckError(HomeLabError):
    """Health check failures"""

    def __init__(
        self, message: str, service: str = "", details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if service:
            details["service"] = service
        super().__init__(message, "HEALTH_CHECK_ERROR", details)
