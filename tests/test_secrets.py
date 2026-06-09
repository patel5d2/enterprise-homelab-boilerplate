"""Tests for secure secret generation and .env file handling."""

import stat
import string

import pytest

from labctl.core.secrets import (
    SecretGenerationError,
    create_backup_env,
    generate_api_key,
    generate_htpasswd_hash,
    generate_password,
    load_or_create_env,
    merge_env_vars,
    redact_secrets,
    validate_env_key,
    validate_secret_strength,
    write_env,
)


class TestGeneratePassword:
    def test_default_length(self):
        assert len(generate_password()) == 24

    def test_complexity(self):
        password = generate_password(32, ensure_complexity=True)
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)

    def test_uniqueness(self):
        assert generate_password() != generate_password()

    def test_invalid_length(self):
        with pytest.raises(SecretGenerationError):
            generate_password(0)


class TestGenerateApiKey:
    def test_length_and_charset(self):
        key = generate_api_key(64)
        assert len(key) <= 64
        allowed = set(string.ascii_letters + string.digits + "-_")
        assert set(key) <= allowed


class TestHtpasswdHash:
    def test_bcrypt_format(self):
        result = generate_htpasswd_hash("admin", "s3cretPassw0rd!")
        user, hashed = result.split(":", 1)
        assert user == "admin"
        # bcrypt ($2y$/$2b$) or SHA-512 crypt ($6$) — never a weak scheme
        assert hashed.startswith(("$2y$", "$2b$", "$6$"))
        assert "{SHA256}" not in hashed

    def test_hash_is_salted(self):
        a = generate_htpasswd_hash("admin", "same-password")
        b = generate_htpasswd_hash("admin", "same-password")
        assert a != b

    def test_rejects_invalid_username(self):
        with pytest.raises(SecretGenerationError):
            generate_htpasswd_hash("bad:user", "password")
        with pytest.raises(SecretGenerationError):
            generate_htpasswd_hash("", "password")


class TestEnvFilePermissions:
    def test_write_env_is_owner_only(self, tmp_path):
        env_path = tmp_path / ".env"
        write_env({"POSTGRES_PASSWORD": "secret"}, env_path)
        mode = stat.S_IMODE(env_path.stat().st_mode)
        assert mode == 0o600

    def test_write_env_tightens_existing_file(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text("OLD=1\n")
        env_path.chmod(0o644)
        write_env({"NEW": "2"}, env_path)
        mode = stat.S_IMODE(env_path.stat().st_mode)
        assert mode == 0o600

    def test_backup_is_owner_only(self, tmp_path):
        env_path = tmp_path / ".env"
        write_env({"TOKEN": "abc"}, env_path)
        backup = create_backup_env(env_path)
        assert backup is not None
        assert backup.exists()
        mode = stat.S_IMODE(backup.stat().st_mode)
        assert mode == 0o600
        assert "TOKEN=abc" in backup.read_text()

    def test_roundtrip(self, tmp_path):
        env_path = tmp_path / ".env"
        write_env({"KEY_ONE": "value one", "KEY_TWO": "plain"}, env_path)
        loaded = load_or_create_env(env_path)
        assert loaded["KEY_ONE"] == "value one"
        assert loaded["KEY_TWO"] == "plain"


class TestMergeEnvVars:
    def test_preserves_existing(self):
        merged = merge_env_vars({"A": "old"}, {"A": "new", "B": "added"})
        assert merged == {"A": "old", "B": "added"}

    def test_rejects_invalid_keys(self):
        merged = merge_env_vars({}, {"lower_case": "x", "VALID_KEY": "y"})
        assert "lower_case" not in merged
        assert merged["VALID_KEY"] == "y"


class TestValidateEnvKey:
    def test_valid(self):
        assert validate_env_key("POSTGRES_PASSWORD")

    def test_invalid(self):
        assert not validate_env_key("lower")
        assert not validate_env_key("1STARTS_WITH_DIGIT")
        assert not validate_env_key("HAS SPACE")


class TestRedactSecrets:
    def test_redacts_sensitive_keys(self):
        data = {"password": "hunter2", "domain": "example.com"}
        redacted = redact_secrets(data)
        assert redacted["password"] != "hunter2"
        assert redacted["domain"] == "example.com"

    def test_keeps_ordinary_long_strings(self):
        data = {"description": "a long human readable description of the service"}
        redacted = redact_secrets(data)
        assert redacted["description"] == data["description"]

    def test_keeps_domains_and_images(self):
        data = {"image": "ghcr.io/example/service:latest", "host": "vault.homelab.example.com"}
        redacted = redact_secrets(data)
        assert redacted == data

    def test_redacts_high_entropy_tokens_in_lists(self):
        token = "aB3dEf6hIj9kLm2nOp5qRs8tUv1wXy4z"
        redacted = redact_secrets([token])
        assert redacted[0] != token


class TestValidateSecretStrength:
    def test_strong_password(self):
        ok, issues = validate_secret_strength("Str0ng!Passw0rd#2024")
        assert ok
        assert issues == []

    def test_weak_password(self):
        ok, issues = validate_secret_strength("password")
        assert not ok
        assert issues
