"""
Services module for Home Lab CLI

This module provides service schema management and validation functionality.
"""

from .deps import (
    CircularDependencyError,
    DependencyError,
    DependencyGraph,
    MissingDependencyError,
    get_dependency_info,
    resolve_with_dependencies,
    validate_service_dependencies,
)
from .schema import (
    ComposeEnvSource,
    ComposeSection,
    FieldSchema,
    FieldType,
    Maturity,
    SchemaValidationError,
    ServiceSchema,
    filter_schemas_by_maturity,
    get_service_categories,
    load_service_schemas,
    validate_service_schema,
)

__all__ = [
    "FieldType",
    "Maturity",
    "ServiceSchema",
    "FieldSchema",
    "ComposeSection",
    "ComposeEnvSource",
    "SchemaValidationError",
    "load_service_schemas",
    "validate_service_schema",
    "get_service_categories",
    "filter_schemas_by_maturity",
    "DependencyGraph",
    "DependencyError",
    "CircularDependencyError",
    "MissingDependencyError",
    "resolve_with_dependencies",
    "validate_service_dependencies",
    "get_dependency_info",
]
