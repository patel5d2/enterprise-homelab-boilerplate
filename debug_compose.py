#!/usr/bin/env python3
"""
Debug script for v2 compose generation
"""

import sys
from pathlib import Path

# Add CLI to path
sys.path.insert(0, str(Path("cli").absolute()))

from cli.labctl.core.config import Config
from cli.labctl.core.compose import ComposeGenerator
from cli.labctl.core.services.schema import load_service_schemas

def test_compose_generation():
    """Test v2 compose generation step by step"""
    
    print("🔍 Testing v2 compose generation...")
    
    # Step 1: Load v2 configuration
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ No config.yaml found")
        return
        
    print("📋 Loading configuration...")
    config = Config.load_from_file(config_path)
    print(f"✅ Config loaded: version={getattr(config, 'version', 'unknown')}")
    
    # Step 2: Load v2 schemas
    print("📦 Loading v2 schemas...")
    schemas_path = Path("config/services-v2")
    try:
        schemas = load_service_schemas(str(schemas_path))
        print(f"✅ Loaded {len(schemas)} schemas: {list(schemas.keys())}")
    except Exception as e:
        print(f"❌ Failed to load schemas: {e}")
        return
    
    # Step 3: Test compose generator with schemas
    print("🔧 Creating compose generator...")
    generator = ComposeGenerator(config, schemas)
    print(f"✅ Generator created with {len(generator.schemas)} schemas")
    
    # Step 4: Check enabled services
    print("🎯 Getting enabled services...")
    enabled = generator._get_enabled_services()
    print(f"✅ Enabled services: {list(enabled.keys())}")
    for service_id, service_config in enabled.items():
        print(f"   • {service_id}: {type(service_config)} = {service_config}")
    
    # Step 5: Test individual service generation
    print("🧪 Testing individual service generation...")
    for service_id, service_config in enabled.items():
        if service_id in schemas:
            print(f"\n--- Testing {service_id} ---")
            schema = schemas[service_id]
            print(f"Schema compose: {hasattr(schema, 'compose')}")
            if hasattr(schema, 'compose') and schema.compose:
                print(f"  Image: {schema.compose.image}")
                print(f"  Ports: {getattr(schema.compose, 'ports', 'None')}")
                print(f"  Environment: {len(getattr(schema.compose, 'environment', []))} vars")
                
                # Try to generate compose service
                try:
                    compose_service = generator._generate_service_from_schema(service_id, service_config, schema)
                    if compose_service:
                        print(f"✅ Generated compose for {service_id}")
                        print(f"   Keys: {list(compose_service.keys())}")
                    else:
                        print(f"❌ No compose generated for {service_id}")
                except Exception as e:
                    print(f"❌ Error generating {service_id}: {e}")
        else:
            print(f"⚠️  No schema found for {service_id}")
    
    # Step 6: Generate full compose
    print("\n🏗️  Generating full compose...")
    try:
        compose_config = generator.generate_compose()
        print(f"✅ Generated compose with {len(compose_config['services'])} services")
        
        for service_id, service_def in compose_config['services'].items():
            print(f"   • {service_id}: {list(service_def.keys())}")
            
    except Exception as e:
        print(f"❌ Failed to generate compose: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_compose_generation()