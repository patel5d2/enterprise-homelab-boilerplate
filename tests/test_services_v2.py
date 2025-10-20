#!/usr/bin/env python3
"""
Test suite for services v2 schemas
"""

from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cli.labctl.core.services import load_service_schemas, DependencyGraph
from cli.labctl.core.services.schema import ServiceSchema

# Path to services-v2 directory
SERVICES_V2_DIR = Path(__file__).parent.parent / "config" / "services-v2"

class TestServicesV2:
    """Test suite for v2 service schemas"""
    
    def test_loads_all_services(self):
        """Test that all service schemas load without errors"""
        schemas = load_service_schemas(SERVICES_V2_DIR)
        
        # Should have 17 services (7 original + 10 converted)
        assert len(schemas) >= 16, f"Expected at least 16 services, got {len(schemas)}"
        
        # Verify basic structure for each schema
        for service_id, schema in schemas.items():
            assert isinstance(schema, ServiceSchema), f"Service {service_id} is not a ServiceSchema"
            assert schema.name, f"Service {service_id} missing name"
            assert schema.description, f"Service {service_id} missing description"
            assert isinstance(schema.dependencies, list), f"Service {service_id} dependencies not a list"
            
            # Every service should have an enabled field
            enabled_fields = [f for f in schema.fields if f.key == "enabled"]
            assert len(enabled_fields) == 1, f"Service {service_id} should have exactly one 'enabled' field, found {len(enabled_fields)}"
            
            enabled_field = enabled_fields[0]
            assert enabled_field.type == "boolean", f"Service {service_id} enabled field should be boolean"
    
    def test_dependency_graph_builds(self):
        """Test that dependency graph builds without errors"""
        schemas = load_service_schemas(SERVICES_V2_DIR)
        
        # Should not raise any exceptions
        graph = DependencyGraph(schemas)
        
        # Test resolving dependencies for all services
        all_services = list(schemas.keys())
        resolved = graph.resolve_dependencies(all_services[:3])  # Test with first 3 services
        
        assert isinstance(resolved, list), "Dependency resolution should return a list"
        assert len(resolved) >= 3, "Should resolve at least the requested services"
    
    def test_grafana_depends_on_prometheus(self):
        """Test that Grafana properly depends on Prometheus"""
        schemas = load_service_schemas(SERVICES_V2_DIR)
        
        if "grafana" in schemas and "prometheus" in schemas:
            grafana_schema = schemas["grafana"]
            assert "prometheus" in grafana_schema.dependencies, "Grafana should depend on Prometheus"
            
            # Test dependency resolution
            graph = DependencyGraph(schemas)
            resolved = graph.resolve_dependencies(["grafana"])
            assert "prometheus" in resolved, "Resolving Grafana should include Prometheus"
            assert "grafana" in resolved, "Resolving Grafana should include Grafana itself"
    
    def test_service_categories(self):
        """Test that services have proper categories"""
        schemas = load_service_schemas(SERVICES_V2_DIR)
        
        expected_categories = {
            "traefik": "Core Infrastructure",
            "postgresql": "Core Infrastructure", 
            "redis": "Core Infrastructure",
            "grafana": "Observability",
            "prometheus": "Observability",
            "gitlab": "DevOps",
            "jenkins": "DevOps",
            "bookstack": "Productivity",
            "n8n": "Automation",
            "nginx_proxy_manager": "Networking",
            "uptime_kuma": "Monitoring",
            "glance": "Dashboard",
            "mongodb": "Core Infrastructure",
        }
        
        for service_id, expected_category in expected_categories.items():
            if service_id in schemas:
                actual_category = schemas[service_id].category
                assert actual_category == expected_category, f"Service {service_id} should be in category '{expected_category}', got '{actual_category}'"
    
    def test_service_ids_valid_format(self):
        """Test that all service IDs use valid format (lowercase, underscores)"""
        schemas = load_service_schemas(SERVICES_V2_DIR)
        
        for service_id in schemas.keys():
            # Should be lowercase alphanumeric with underscores
            assert service_id.islower(), f"Service ID '{service_id}' should be lowercase"
            assert service_id.replace('_', '').isalnum(), f"Service ID '{service_id}' should only contain alphanumeric and underscores"
            assert not service_id.startswith('_'), f"Service ID '{service_id}' should not start with underscore"
            assert not service_id.endswith('_'), f"Service ID '{service_id}' should not end with underscore"
    
    def test_profile_defaults_exist(self):
        """Test that all services have profile-specific defaults"""
        schemas = load_service_schemas(SERVICES_V2_DIR)
        
        for service_id, schema in schemas.items():
            if schema.defaults:
                # Should have at least dev or prod defaults
                assert schema.defaults.dev is not None or schema.defaults.prod is not None, \
                    f"Service {service_id} should have either dev or prod defaults"
                
                # If enabled field exists, defaults should specify enabled status
                has_enabled_field = any(f.key == "enabled" for f in schema.fields)
                if has_enabled_field and schema.defaults.dev:
                    assert "enabled" in schema.defaults.dev, f"Service {service_id} dev defaults should specify 'enabled'"
                if has_enabled_field and schema.defaults.prod:
                    assert "enabled" in schema.defaults.prod, f"Service {service_id} prod defaults should specify 'enabled'"


def test_service_count():
    """Simple test to verify we have the expected number of services"""
    schemas = load_service_schemas(SERVICES_V2_DIR)
    service_names = sorted(schemas.keys())
    
    print(f"\nLoaded {len(schemas)} services:")
    for name in service_names:
        schema = schemas[name]
        print(f"  • {name} ({schema.category}) - {schema.description}")
    
    assert len(schemas) >= 16, f"Expected at least 16 services, got {len(schemas)}: {service_names}"


if __name__ == "__main__":
    # Run basic test when executed directly
    test_service_count()
    
    # Run all tests
    test_class = TestServicesV2()
    test_class.test_loads_all_services()
    test_class.test_dependency_graph_builds()
    test_class.test_grafana_depends_on_prometheus() 
    test_class.test_service_categories()
    test_class.test_service_ids_valid_format()
    test_class.test_profile_defaults_exist()
    
    print("✅ All tests passed!")