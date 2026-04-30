"""
Tests for labctl doctor command.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Project root for path references
PROJECT_ROOT = Path(__file__).parent.parent


# ── Unit tests for individual checks ─────────────────────────────────────────


class TestDoctorChecks:
    """Unit tests for each individual health check function."""

    def test_python_check_passes_current_version(self):
        from labctl.cli.commands.doctor_cmd import check_python

        passed, detail, hint = check_python()
        assert passed, f"check_python should pass on Python {sys.version_info}; got: {detail}"
        assert "package importable" in detail

    def test_python_check_detail_contains_version(self):
        from labctl.cli.commands.doctor_cmd import check_python

        passed, detail, _ = check_python()
        assert f"{sys.version_info.major}.{sys.version_info.minor}" in detail

    def test_venv_check_passes_when_venv_exists(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_venv

        # Create fake venv structure
        fake_python = tmp_path / "venv" / "bin" / "python3"
        fake_python.parent.mkdir(parents=True)
        fake_python.touch()
        fake_python.chmod(0o755)

        passed, detail, hint = check_venv(tmp_path)
        assert passed
        assert "venv at ./venv/" in detail

    def test_venv_check_fails_when_venv_missing(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_venv

        passed, detail, hint = check_venv(tmp_path)
        assert not passed
        assert hint is not None
        assert "bootstrap.sh" in hint

    def test_env_file_check_fails_when_missing(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_env_file

        passed, detail, hint = check_env_file(tmp_path)
        assert not passed
        assert ".env file not found" in detail
        assert hint is not None

    def test_env_file_check_passes_when_present(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_env_file

        env = tmp_path / ".env"
        env.write_text("POSTGRES_PASSWORD=secret123\nREDIS_PASSWORD=secret456\n")
        passed, detail, hint = check_env_file(tmp_path)
        assert passed
        assert "2 variable(s)" in detail

    def test_env_required_vars_pass_when_no_todos(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_env_required_vars

        env = tmp_path / ".env"
        env.write_text("POSTGRES_PASSWORD=supersecret\n")
        passed, detail, hint = check_env_required_vars(tmp_path)
        assert passed

    def test_env_required_vars_fail_when_todos_present(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_env_required_vars

        env = tmp_path / ".env"
        env.write_text(
            "POSTGRES_PASSWORD=filled\n"
            "# TODO: Set CLOUDFLARE_TUNNEL_TOKEN — your Cloudflare token\n"
        )
        passed, detail, hint = check_env_required_vars(tmp_path)
        assert not passed
        assert "CLOUDFLARE_TUNNEL_TOKEN" in detail

    def test_config_yaml_check_fails_when_missing(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_config_yaml

        passed, detail, hint = check_config_yaml(tmp_path)
        assert not passed
        assert "config/config.yaml not found" in detail

    def test_config_yaml_check_passes_with_valid_config(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_config_yaml

        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "config.yaml").write_text(
            "version: 2\nprofile: prod\nservices:\n  traefik:\n    enabled: true\n"
        )
        (tmp_path / "config" / "services-v2").mkdir()
        (tmp_path / "config" / "services-v2" / "traefik.yaml").write_text("id: traefik\n")

        passed, detail, hint = check_config_yaml(tmp_path)
        assert passed
        assert "config.yaml OK" in detail

    def test_config_yaml_check_warns_unknown_services(self, tmp_path):
        from labctl.cli.commands.doctor_cmd import check_config_yaml

        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "config.yaml").write_text(
            "version: 2\nservices:\n  nonexistent_svc:\n    enabled: true\n"
        )
        schemas_dir = tmp_path / "config" / "services-v2"
        schemas_dir.mkdir()
        # At least one known schema must exist so the check has a reference set
        (schemas_dir / "traefik.yaml").write_text("id: traefik\n")

        passed, detail, _ = check_config_yaml(tmp_path)
        assert not passed, "Should fail because 'nonexistent_svc' is not a known schema ID"
        assert "nonexistent_svc" in detail


# ── Integration test: run command raises SystemExit(1) on failures ────────────


class TestDoctorRun:
    """Integration tests for doctor_cmd.run()."""

    def test_run_exits_1_when_env_missing(self, tmp_path):
        """doctor raises SystemExit(1) when .env is absent."""
        from labctl.cli.commands.doctor_cmd import run

        # Provide minimal structure so other checks pass
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "config.yaml").write_text("version: 2\nservices: {}\n")
        (tmp_path / "config" / "services-v2").mkdir()

        with pytest.raises(SystemExit) as exc_info:
            run(project_root=str(tmp_path))

        assert exc_info.value.code == 1

    def test_run_succeeds_with_healthy_state(self, tmp_path, monkeypatch):
        """doctor exits cleanly when all checks pass."""
        from labctl.cli.commands import doctor_cmd

        # Mock the heavy checks that need live system state
        monkeypatch.setattr(doctor_cmd, "check_python", lambda: (True, "Python 3.12 ✓", None))
        monkeypatch.setattr(doctor_cmd, "check_docker", lambda: (True, "Docker 26 ✓", None))

        # Create the minimal file structure
        venv_py = tmp_path / "venv" / "bin" / "python3"
        venv_py.parent.mkdir(parents=True)
        venv_py.touch()
        venv_py.chmod(0o755)

        env = tmp_path / ".env"
        env.write_text("POSTGRES_PASSWORD=ok\n")

        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "config.yaml").write_text("version: 2\nservices: {}\n")
        (tmp_path / "config" / "services-v2").mkdir()

        # Should not raise
        doctor_cmd.run(project_root=str(tmp_path))
