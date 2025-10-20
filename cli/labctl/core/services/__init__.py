"""
Services module for Home Lab CLI

This module provides service schema management and validation functionality.
"""

from .schema import (
    FieldType,
    Maturity,
    ServiceSchema,
    FieldSchema,
    ComposeSection,
    ComposeEnvSource,
    SchemaValidationError,
    load_service_schemas,
    validate_service_schema,
    get_service_categories,
    filter_schemas_by_maturity,
)

from .deps import (
    DependencyGraph,
    DependencyError,
    CircularDependencyError,
    MissingDependencyError,
    resolve_with_dependencies,
    validate_service_dependencies,
    get_dependency_info,
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
