#!/usr/bin/env python3
"""
Convert v1 service schemas to v2 format
"""

from pathlib import Path
import yaml
import sys
import re

SRC = Path("config/services")
DST = Path("config/services-v2")
DST.mkdir(parents=True, exist_ok=True)

# Service-specific overrides and improvements
SERVICE_OVERRIDES = {
    "grafana": {"category": "Observability", "dependencies": ["prometheus"]},
    "prometheus": {"category": "Observability", "dependencies": []},
    "gitlab": {"category": "DevOps", "dependencies": ["postgresql", "redis"]},
    "jenkins": {"category": "DevOps", "dependencies": []},
    "bookstack": {"category": "Productivity", "dependencies": ["postgresql"]},
    "n8n": {"category": "Automation", "dependencies": ["postgresql", "redis"]},
    "mongodb": {"category": "Core Infrastructure", "dependencies": []},
    "nginx-proxy-manager": {"category": "Networking", "dependencies": []},
    "uptime-kuma": {"category": "Monitoring", "dependencies": []},
    "glance": {"category": "Dashboard", "dependencies": []},
}

# Type mapping from v1 to v2
TYPE_MAPPING = {
    "string": "string",
    "password": "password", 
    "boolean": "boolean",
    "integer": "integer",
    "multiselect": "multiselect",
    "select": "choice",
}

def normalize_field(field_key: str, field_config: dict) -> dict:
    """Convert v1 field configuration to v2 schema format"""
    field_type = field_config.get("type", "string")
    v2_type = TYPE_MAPPING.get(field_type, "string")
    
    v2_field = {
        "key": field_key,
        "label": field_config.get("name", field_key.replace("_", " ").title()),
        "type": v2_type,
        "description": field_config.get("description", f"Configure {field_key}"),
    }
    
    # Handle default values
    if "default" in field_config:
        v2_field["default"] = field_config["default"]
    
    # Handle required fields
    if field_config.get("required", False):
        v2_field["required"] = True
    
    # Handle choices/options
    if "choices" in field_config:
        v2_field["choices"] = field_config["choices"]
    
    # Handle validation regex
    if "validation" in field_config and "regex" in field_config["validation"]:
        v2_field["validate_regex"] = field_config["validation"]["regex"]
    
    # Handle password fields
    if v2_type == "password":
        v2_field["generate"] = True
        v2_field["length"] = 24
        
    # Handle integer constraints
    if v2_type == "integer":
        if "min" in field_config:
            v2_field["min"] = field_config["min"]
        if "max" in field_config:
            v2_field["max"] = field_config["max"]
    
    return v2_field

def convert_configuration_to_fields(config_dict: dict) -> list:
    """Convert v1 configuration section to v2 fields"""
    fields = []
    
    def process_section(section_dict, prefix=""):
        for key, value in section_dict.items():
            if isinstance(value, dict) and "type" in value:
                # This is a field definition
                field_key = f"{prefix}{key}" if prefix else key
                field = normalize_field(field_key, value)
                fields.append(field)
            elif isinstance(value, dict):
                # This is a nested section
                new_prefix = f"{prefix}{key}_" if prefix else f"{key}_"
                process_section(value, new_prefix)
    
    process_section(config_dict)
    return fields

def extract_compose_info(docker_config: dict) -> dict:
    """Extract compose configuration from v1 docker section"""
    compose = {
        "image": docker_config.get("image", ""),
        "container_name": docker_config.get("container_name", ""),
        "restart": docker_config.get("restart", "unless-stopped"),
    }
    
    # Add optional sections
    if "ports" in docker_config:
        compose["ports"] = docker_config["ports"]
    if "volumes" in docker_config:
        compose["volumes"] = docker_config["volumes"]
    if "networks" in docker_config:
        compose["networks"] = docker_config["networks"]
    if "environment" in docker_config:
        compose["environment"] = []
        for env in docker_config["environment"]:
            if isinstance(env, str) and "=" in env:
                key, value = env.split("=", 1)
                compose["environment"].append({
                    "key": key,
                    "value": value
                })
            elif isinstance(env, dict):
                # Already in key-value format
                compose["environment"].append(env)
    if "command" in docker_config:
        compose["command"] = docker_config["command"]
    if "labels" in docker_config:
        compose["labels"] = docker_config["labels"]
        
    return compose

def convert_one(src_path: Path, dst_path: Path):
    """Convert a single v1 service to v2 format"""
    print(f"Converting {src_path.name}...")
    
    with open(src_path, 'r', encoding='utf-8') as f:
        v1 = yaml.safe_load(f)
    
    if not v1:
        print(f"  WARNING: Empty or invalid YAML in {src_path}")
        return
    
    service_id = v1.get("service_name", src_path.stem)
    
    # Build v2 structure
    v2 = {
        "id": service_id,
        "name": v1.get("display_name", service_id.title()),
        "category": v1.get("category", "Uncategorized").title(),
        "description": v1.get("description", f"{service_id} service"),
        "maturity": "stable",
        "required_capabilities": [],
        "dependencies": v1.get("dependencies", []),
    }
    
    # Convert configuration to fields
    fields = []
    if "configuration" in v1:
        fields = convert_configuration_to_fields(v1["configuration"])
    
    # Ensure enabled field exists at the beginning
    has_enabled = any(f.get("key") == "enabled" for f in fields)
    if not has_enabled:
        enabled_field = {
            "key": "enabled",
            "label": f"Enable {v2['name']}",
            "type": "boolean",
            "description": f"Enable {v2['name']} service",
            "default": v1.get("default_enabled", True),
            "required": True,
        }
        fields.insert(0, enabled_field)
    
    v2["fields"] = fields
    
    # Extract compose configuration
    if "docker" in v1:
        v2["compose"] = extract_compose_info(v1["docker"])
    else:
        v2["compose"] = {
            "image": f"{service_id}:latest",
            "container_name": service_id,
            "restart": "unless-stopped",
        }
    
    # Add profile-specific defaults
    v2["defaults"] = {
        "dev": {
            "enabled": v1.get("default_enabled", True),
        },
        "prod": {
            "enabled": v1.get("default_enabled", True),
        }
    }
    
    # Apply service-specific overrides
    if service_id in SERVICE_OVERRIDES:
        overrides = SERVICE_OVERRIDES[service_id]
        v2.update(overrides)
    
    # Write v2 file
    with open(dst_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(v2, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)
    
    print(f"  ✓ Converted to {dst_path}")

def main():
    """Convert all missing services from v1 to v2"""
    targets = [
        "bookstack.yaml", "gitlab.yaml", "glance.yaml", "grafana.yaml", "jenkins.yaml",
        "mongodb.yaml", "n8n.yaml", "nginx-proxy-manager.yaml", "prometheus.yaml", "uptime-kuma.yaml",
    ]
    
    print(f"Converting {len(targets)} services from v1 to v2 format...")
    print(f"Source: {SRC}")
    print(f"Destination: {DST}")
    
    converted = 0
    for name in targets:
        src_file = SRC / name
        if not src_file.exists():
            print(f"  WARNING: Source file missing: {src_file}")
            continue
        
        dst_file = DST / name
        try:
            convert_one(src_file, dst_file)
            converted += 1
        except Exception as e:
            print(f"  ERROR: Failed to convert {name}: {e}")
    
    print(f"\n✓ Successfully converted {converted}/{len(targets)} services")
    print(f"All converted files are in: {DST}")

if __name__ == "__main__":
    main()