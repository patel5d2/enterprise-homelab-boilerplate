"""Tests for the Docker Compose generator, including security hardening defaults."""

from pathlib import Path

import yaml

from labctl.core.compose import ComposeGenerator
from labctl.core.services import load_service_schemas

SERVICES_V2_DIR = Path(__file__).parent.parent / "config" / "services-v2"


def make_config(services):
    return {
        "core": {"domain": "homelab.test", "email": "admin@homelab.test", "timezone": "UTC"},
        "services": services,
        "env_vars": {},
    }


class TestComposeGeneration:
    def test_generates_enabled_services_only(self):
        schemas = load_service_schemas(SERVICES_V2_DIR)
        config = make_config(
            {
                "redis": {"enabled": True},
                "postgresql": {"enabled": False},
            }
        )
        compose = ComposeGenerator(config, schemas).generate_compose()
        assert "redis" in compose["services"]
        assert "postgresql" not in compose["services"]

    def test_no_obsolete_version_key(self):
        schemas = load_service_schemas(SERVICES_V2_DIR)
        config = make_config({"redis": {"enabled": True}})
        compose = ComposeGenerator(config, schemas).generate_compose()
        assert "version" not in compose

    def test_services_have_no_new_privileges(self):
        schemas = load_service_schemas(SERVICES_V2_DIR)
        config = make_config({"redis": {"enabled": True}, "grafana": {"enabled": True}})
        compose = ComposeGenerator(config, schemas).generate_compose()
        for service_id, service in compose["services"].items():
            assert "no-new-privileges:true" in service.get(
                "security_opt", []
            ), f"Service {service_id} missing no-new-privileges hardening"

    def test_services_have_log_rotation(self):
        schemas = load_service_schemas(SERVICES_V2_DIR)
        config = make_config({"redis": {"enabled": True}})
        compose = ComposeGenerator(config, schemas).generate_compose()
        logging = compose["services"]["redis"]["logging"]
        assert logging["driver"] == "json-file"
        assert logging["options"]["max-size"]

    def test_compose_file_is_valid_yaml(self, tmp_path):
        schemas = load_service_schemas(SERVICES_V2_DIR)
        config = make_config({"redis": {"enabled": True}})
        out = tmp_path / "docker-compose.yml"
        ComposeGenerator(config, schemas).save_compose_file(out)
        parsed = yaml.safe_load(out.read_text())
        assert "services" in parsed
        assert "redis" in parsed["services"]

    def test_restart_policy(self):
        schemas = load_service_schemas(SERVICES_V2_DIR)
        config = make_config({"redis": {"enabled": True}})
        compose = ComposeGenerator(config, schemas).generate_compose()
        assert compose["services"]["redis"]["restart"] == "unless-stopped"
