"""
Service Schema Models and Loader

This module defines the Pydantic models for service schemas and provides
functionality to load and validate service definitions from YAML files.
"""

import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from rich.console import Console

console = Console()


class FieldType(str, Enum):
    """Supported field types for service configuration"""

    STRING = "string"
    PASSWORD = "password"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    CHOICE = "choice"
    MULTISELECT = "multiselect"
    TEXTAREA = "textarea"


class Maturity(str, Enum):
    """Service maturity levels"""

    ALPHA = "alpha"
    BETA = "beta"
    STABLE = "stable"


class ComposeEnvSource(BaseModel):
    """Environment variable source configuration"""

    key: str = Field(..., description="Environment variable name")
    from_field: Optional[str] = Field(None, description="Source from field value")
    from_service: Optional[str] = Field(None, description="Source from other service")
    value: Optional[str] = Field(None, description="Static literal value")
    template: Optional[str] = Field(None, description="Template with variables")
    generate: Optional[str] = Field(None, description="Generated value type")
    condition: Optional[str] = Field(None, description="Conditional expression")
    value_map: Optional[Dict[str, str]] = Field(None, description="Value mapping")
    value_if: Optional[Dict[str, Any]] = Field(None, description="Conditional value")

    @field_validator("key")
    @classmethod
    def validate_env_key(cls, v):
        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError(
                "Environment variable must be uppercase alphanumeric with underscores"
            )
        return v

    model_config = ConfigDict(extra="forbid")


class ComposeHealthcheck(BaseModel):
    """Docker healthcheck configuration"""

    test: List[str] = Field(..., description="Healthcheck command")
    interval: str = Field(default="30s", description="Check interval")
    timeout: str = Field(default="5s", description="Check timeout")
    retries: int = Field(default=3, description="Number of retries")
    start_period: Optional[str] = Field(None, description="Start period")

    model_config = ConfigDict(extra="forbid")


class ComposeDependsOn(BaseModel):
    """Docker depends_on configuration"""

    condition: str = Field(
        default="service_started", description="Dependency condition"
    )

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v):
        valid_conditions = [
            "service_started",
            "service_healthy",
            "service_completed_successfully",
        ]
        if v not in valid_conditions:
            raise ValueError(f'Condition must be one of: {", ".join(valid_conditions)}')
        return v

    model_config = ConfigDict(extra="forbid")


class ComposeAdditionalService(BaseModel):
    """Additional service configuration"""

    enabled_when: Optional[str] = Field(
        None, description="Condition for enabling this service"
    )
    image: str = Field(..., description="Docker image")
    container_name: str = Field(..., description="Container name")
    restart: str = Field(default="unless-stopped", description="Restart policy")
    ports: Optional[List[str]] = Field(None, description="Port mappings")
    volumes: Optional[List[str]] = Field(None, description="Volume mounts")
    networks: Optional[List[str]] = Field(None, description="Networks to join")
    environment: Optional[List[ComposeEnvSource]] = Field(
        None, description="Environment variables"
    )
    labels: Optional[List[str]] = Field(None, description="Docker labels")
    depends_on: Optional[Dict[str, ComposeDependsOn]] = Field(
        None, description="Service dependencies"
    )
    command: Optional[Union[str, List[str]]] = Field(
        None, description="Container command"
    )
    entrypoint: Optional[Union[str, List[str]]] = Field(
        None, description="Container entrypoint"
    )
    privileged: Optional[bool] = Field(None, description="Privileged mode")
    cap_add: Optional[List[str]] = Field(None, description="Linux capabilities to add")
    devices: Optional[List[str]] = Field(None, description="Device mappings")

    model_config = ConfigDict(extra="forbid")


class ComposeSection(BaseModel):
    """Docker compose service definition"""

    image: str = Field(..., description="Docker image")
    container_name: str = Field(..., description="Container name")
    restart: str = Field(default="unless-stopped", description="Restart policy")
    ports: Optional[List[str]] = Field(None, description="Port mappings")
    volumes: Optional[List[str]] = Field(None, description="Volume mounts")
    networks: Optional[List[str]] = Field(None, description="Networks to join")
    environment: Optional[List[ComposeEnvSource]] = Field(
        None, description="Environment variables"
    )
    labels: Optional[List[str]] = Field(None, description="Docker labels")
    depends_on: Optional[Dict[str, ComposeDependsOn]] = Field(
        None, description="Service dependencies"
    )
    healthcheck: Optional[ComposeHealthcheck] = Field(
        None, description="Health check configuration"
    )
    command: Optional[Union[str, List[str]]] = Field(
        None, description="Container command"
    )
    entrypoint: Optional[Union[str, List[str]]] = Field(
        None, description="Container entrypoint"
    )
    privileged: Optional[bool] = Field(None, description="Privileged mode")
    cap_add: Optional[List[str]] = Field(None, description="Linux capabilities to add")
    dns: Optional[List[str]] = Field(None, description="Custom DNS servers")
    devices: Optional[List[str]] = Field(None, description="Device mappings")
    additional_services: Optional[Dict[str, ComposeAdditionalService]] = Field(
        None, description="Additional services"
    )
    template_vars: Optional[Dict[str, Dict[str, str]]] = Field(
        None, description="Template variables"
    )

    model_config = ConfigDict(extra="forbid")


class FieldSchema(BaseModel):
    """Field definition for service configuration"""

    key: str = Field(..., description="Field identifier")
    label: str = Field(..., description="Human-readable label")
    type: FieldType = Field(..., description="Field type")
    description: str = Field(..., description="Field description")
    default: Optional[Any] = Field(None, description="Default value")
    required: bool = Field(default=False, description="Required field")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    validate_regex: Optional[str] = Field(None, description="Validation regex")
    min: Optional[int] = Field(None, description="Minimum value (integer)")
    max: Optional[int] = Field(None, description="Maximum value (integer)")
    min_length: Optional[int] = Field(None, description="Minimum length (string)")
    max_length: Optional[int] = Field(None, description="Maximum length (string)")
    choices: Optional[List[str]] = Field(None, description="Available choices")
    min_selections: Optional[int] = Field(
        None, description="Minimum selections (multiselect)"
    )
    max_selections: Optional[int] = Field(
        None, description="Maximum selections (multiselect)"
    )
    generate: Optional[bool] = Field(None, description="Auto-generate value (password)")
    length: Optional[int] = Field(None, description="Generated length (password)")
    mask: Optional[bool] = Field(None, description="Mask input (password)")
    show_if: Optional[str] = Field(
        None, description="Conditional visibility expression"
    )
    hidden_if: Optional[str] = Field(None, description="Conditional hiding expression")
    depends_on: Optional[List[str]] = Field(None, description="Field dependencies")

    @field_validator("key")
    @classmethod
    def validate_key(cls, v):
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Field key must be alphanumeric with underscores, starting with letter"
            )
        return v

    @field_validator("validate_regex")
    @classmethod
    def validate_regex_pattern(cls, v):
        if v:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        return v

    @field_validator("choices", mode="before")
    @classmethod
    def validate_choices(cls, v, info):
        values = info.data
        field_type = values.get("type")
        if field_type in [FieldType.CHOICE, FieldType.MULTISELECT] and not v:
            raise ValueError(f"Field type {field_type} requires choices")
        return v

    @field_validator("min", "max")
    @classmethod
    def validate_int_bounds(cls, v, info):
        values = info.data
        field_type = values.get("type")
        if v is not None and field_type != FieldType.INTEGER:
            raise ValueError("min/max only valid for integer fields")
        return v

    @field_validator("min_selections", "max_selections")
    @classmethod
    def validate_multiselect_bounds(cls, v, info):
        values = info.data
        field_type = values.get("type")
        if v is not None and field_type != FieldType.MULTISELECT:
            raise ValueError(
                "min_selections/max_selections only valid for multiselect fields"
            )
        return v

    model_config = ConfigDict(extra="forbid")


class ServiceDefaults(BaseModel):
    """Profile-specific defaults"""

    dev: Optional[Dict[str, Any]] = Field(
        None, description="Development profile defaults"
    )
    prod: Optional[Dict[str, Any]] = Field(
        None, description="Production profile defaults"
    )

    model_config = ConfigDict(extra="forbid")


class ServiceSchema(BaseModel):
    """Complete service schema definition"""

    id: str = Field(..., description="Unique service identifier")
    name: str = Field(..., description="Human-readable service name")
    category: str = Field(..., description="Service category")
    description: str = Field(..., description="Service description")
    maturity: Maturity = Field(
        default=Maturity.STABLE, description="Service maturity level"
    )
    required_capabilities: List[str] = Field(
        default_factory=list, description="Required system capabilities"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Service dependencies"
    )
    fields: List[FieldSchema] = Field(..., description="Configuration fields")
    compose: ComposeSection = Field(..., description="Docker compose configuration")
    defaults: Optional[ServiceDefaults] = Field(
        None, description="Profile-specific defaults"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(
                "Service ID must be lowercase alphanumeric with underscores"
            )
        return v

    @field_validator("fields")
    @classmethod
    def validate_fields_unique(cls, v):
        keys = [field.key for field in v]
        if len(keys) != len(set(keys)):
            raise ValueError("Field keys must be unique within service")
        return v

    @field_validator("fields")
    @classmethod
    def validate_enabled_field(cls, v):
        # Ensure there's always an 'enabled' field
        has_enabled = any(field.key == "enabled" for field in v)
        if not has_enabled:
            raise ValueError('Service must have an "enabled" field')
        return v

    model_config = ConfigDict(extra="forbid")


class SchemaValidationError(Exception):
    """Schema validation error with detailed messages"""

    def __init__(self, service_id: str, errors: List[str]):
        self.service_id = service_id
        self.errors = errors
        super().__init__(
            f"Schema validation failed for {service_id}: {'; '.join(errors)}"
        )


@lru_cache(maxsize=32)
def load_service_schemas(
    schemas_dir: Union[str, Path], reload: bool = False
) -> Dict[str, ServiceSchema]:
    """
    Load and validate service schemas from directory

    Args:
        schemas_dir: Directory containing service YAML files
        reload: Force reload (bypasses cache)

    Returns:
        Dictionary mapping service IDs to ServiceSchema objects

    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If schemas directory doesn't exist
    """
    if reload:
        load_service_schemas.cache_clear()

    schemas_path = Path(schemas_dir)
    if not schemas_path.exists():
        raise FileNotFoundError(f"Schemas directory not found: {schemas_path}")

    schemas = {}
    errors = []

    # Find all YAML files
    yaml_files = list(schemas_path.glob("*.yaml")) + list(schemas_path.glob("*.yml"))
    if not yaml_files:
        console.print(
            f"[yellow]Warning: No YAML schema files found in {schemas_path}[/yellow]"
        )
        return {}

    for yaml_file in yaml_files:
        if yaml_file.name.startswith(".") or yaml_file.name == "SCHEMA.md":
            continue

        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                console.print(
                    f"[yellow]Warning: Empty schema file: {yaml_file}[/yellow]"
                )
                continue

            schema = ServiceSchema(**data)

            if schema.id in schemas:
                errors.append(f"Duplicate service ID '{schema.id}' in {yaml_file}")
                continue

            schemas[schema.id] = schema
            console.print(
                f"[green]✓[/green] Loaded schema: {schema.id} ({schema.name})"
            )

        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error in {yaml_file}: {e}")
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                error_messages.append(f"{location}: {error['msg']}")
            errors.append(
                f"Validation errors in {yaml_file}: {'; '.join(error_messages)}"
            )
        except Exception as e:
            errors.append(f"Unexpected error loading {yaml_file}: {e}")

    if errors:
        for error in errors:
            console.print(f"[red]✗[/red] {error}")
        raise SchemaValidationError("schema_loading", errors)

    console.print(f"[green]Loaded {len(schemas)} service schemas[/green]")
    return schemas


def validate_service_schema(schema: ServiceSchema) -> List[str]:
    """
    Validate a service schema for common issues

    Args:
        schema: ServiceSchema to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check field references in conditional expressions
    field_keys = {field.key for field in schema.fields}

    for field in schema.fields:
        # Validate show_if/hidden_if expressions reference valid fields
        for expr_attr in ["show_if", "hidden_if"]:
            expr = getattr(field, expr_attr)
            if expr:
                # Simple validation - just check if referenced fields exist
                # In a real implementation, you'd want a proper expression parser
                referenced_fields = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*==", expr)
                for ref_field in referenced_fields:
                    if ref_field not in field_keys:
                        errors.append(
                            f"Field '{field.key}' references unknown field "
                            f"'{ref_field}' in {expr_attr}"
                        )

        # Validate depends_on references
        if field.depends_on:
            for dep_field in field.depends_on:
                if dep_field not in field_keys:
                    errors.append(
                        f"Field '{field.key}' depends on unknown field '{dep_field}'"
                    )

    # Check compose environment references
    if schema.compose.environment:
        for env_var in schema.compose.environment:
            if env_var.from_field and env_var.from_field not in field_keys:
                errors.append(
                    f"Environment variable '{env_var.key}' references unknown "
                    f"field '{env_var.from_field}'"
                )

    # Validate dependencies exist (this would need service registry in real
    # implementation)
    # For now, just validate they're reasonable service names
    for dep in schema.dependencies:
        if not re.match(r"^[a-z][a-z0-9_]*$", dep):
            errors.append(f"Invalid dependency name format: '{dep}'")

    return errors


def get_service_categories(schemas: Dict[str, ServiceSchema]) -> Dict[str, List[str]]:
    """
    Group services by category

    Args:
        schemas: Dictionary of service schemas

    Returns:
        Dictionary mapping categories to lists of service IDs
    """
    categories = {}
    for service_id, schema in schemas.items():
        category = schema.category
        if category not in categories:
            categories[category] = []
        categories[category].append(service_id)

    return categories


def filter_schemas_by_maturity(
    schemas: Dict[str, ServiceSchema], min_maturity: Maturity = Maturity.STABLE
) -> Dict[str, ServiceSchema]:
    """
    Filter schemas by minimum maturity level

    Args:
        schemas: Dictionary of service schemas
        min_maturity: Minimum maturity level to include

    Returns:
        Filtered dictionary of schemas
    """
    maturity_order = [Maturity.ALPHA, Maturity.BETA, Maturity.STABLE]
    min_level = maturity_order.index(min_maturity)

    return {
        service_id: schema
        for service_id, schema in schemas.items()
        if maturity_order.index(schema.maturity) >= min_level
    }
