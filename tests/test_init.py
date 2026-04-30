"""
Tests for labctl init command (Phase 2 wizard).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent


class TestInitCmd:
    """Unit tests for init_cmd.run()."""

    def test_run_skips_when_config_exists_non_interactive(self, tmp_path):
        """Non-interactive mode skips init when config already exists."""
        from labctl.cli.commands import init_cmd

        config_path = tmp_path / "config" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("version: 2\nprofile: prod\nservices: {}\n")

        # Should return without raising
        init_cmd.run(
            config_file=str(config_path),
            non_interactive=True,
        )
        # Config file should remain unchanged
        assert config_path.exists()

    def test_merge_env_file_adds_new_vars(self, tmp_path):
        """_merge_env_file adds new vars without overwriting existing ones."""
        from labctl.cli.commands.init_cmd import _merge_env_file

        env_path = tmp_path / ".env"
        env_path.write_text("EXISTING_VAR=original_value\n")

        _merge_env_file(env_path, {"NEW_VAR": "new_value", "EXISTING_VAR": "should_not_overwrite"})

        content = env_path.read_text()
        assert "EXISTING_VAR=original_value" in content
        assert "NEW_VAR=new_value" in content
        assert "should_not_overwrite" not in content

    def test_merge_env_file_creates_file_if_missing(self, tmp_path):
        """_merge_env_file creates .env from scratch if it doesn't exist."""
        from labctl.cli.commands.init_cmd import _merge_env_file

        env_path = tmp_path / ".env"
        _merge_env_file(env_path, {"POSTGRES_PASSWORD": "secret123"})

        assert env_path.exists()
        assert "POSTGRES_PASSWORD=secret123" in env_path.read_text()

    def test_show_next_steps_does_not_raise(self):
        """_show_next_steps should not raise for any valid config shape."""
        from labctl.cli.commands.init_cmd import _show_next_steps

        config = {
            "version": 2,
            "profile": "prod",
            "core": {"domain": "homelab.local", "email": "admin@example.com"},
            "services": {
                "traefik": {"enabled": True},
                "postgresql": {"enabled": True},
                "redis": {"enabled": False},
            },
        }
        # Should not raise
        _show_next_steps(config)

    def test_create_directories(self, tmp_path):
        """_create_directories creates expected subdirectory structure."""
        from labctl.cli.commands.init_cmd import _create_directories

        _create_directories(tmp_path)

        for d in ["compose", "data", "logs", "backups", "ssl"]:
            assert (tmp_path / d).is_dir(), f"Expected {d} to be created"


class TestWizardOrchestrator:
    """Unit tests for the WizardOrchestrator class."""

    def _get_schemas(self):
        from labctl.core.services.schema import load_service_schemas
        schemas_dir = PROJECT_ROOT / "config" / "services-v2"
        return load_service_schemas(str(schemas_dir))

    def test_orchestrator_loads_schemas(self):
        from labctl.cli.wizard.orchestrator import WizardOrchestrator
        schemas = self._get_schemas()
        orch = WizardOrchestrator(schemas)
        assert len(orch.schemas) >= 16

    def test_non_interactive_wizard_returns_valid_config(self):
        """Non-interactive wizard returns a valid config dict with expected shape."""
        from labctl.cli.wizard.orchestrator import WizardOrchestrator
        schemas = self._get_schemas()
        orch = WizardOrchestrator(schemas)

        existing = {
            "profile": "prod",
            "core": {"domain": "test.local", "email": "test@example.com"},
            "services": {
                "traefik": {"enabled": True},
                "postgresql": {"enabled": True},
            },
        }

        result = orch.run_wizard(
            profile="prod",
            existing_config=existing,
            non_interactive=True,
        )

        assert result["version"] == 2
        assert result["profile"] == "prod"
        assert "core" in result
        assert "services" in result
        assert "traefik" in result["services"]

    def test_non_interactive_generates_secrets(self):
        """Non-interactive mode auto-generates secrets for password fields."""
        from labctl.cli.wizard.orchestrator import WizardOrchestrator
        schemas = self._get_schemas()
        orch = WizardOrchestrator(schemas)

        existing = {
            "profile": "prod",
            "core": {"domain": "test.local", "email": "test@example.com"},
            "services": {"postgresql": {"enabled": True}},
        }

        result = orch.run_wizard(
            profile="prod",
            existing_config=existing,
            non_interactive=True,
        )

        env_vars = result.get("env_vars", {})
        # At least one secret should have been generated
        assert any("PASSWORD" in k or "TOKEN" in k or "SECRET" in k for k in env_vars)

    def test_env_var_name_helper(self):
        from labctl.cli.wizard.orchestrator import _env_var_name
        assert _env_var_name("postgresql", "superuser_password") == "POSTGRESQL_SUPERUSER_PASSWORD"
        assert _env_var_name("redis", "password") == "REDIS_PASSWORD"

    def test_is_secret_field(self):
        from labctl.cli.wizard.orchestrator import _is_secret_field
        assert _is_secret_field("admin_password") is True
        assert _is_secret_field("cloudflare_api_token") is True
        assert _is_secret_field("database_port") is False
        assert _is_secret_field("retention_days") is False
