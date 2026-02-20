"""Unit tests for configuration module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from src.config import (
    Config,
    _expand_env_vars,
    _is_env_var_reference,
    _resolve_value,
    get_bootstrap_log_level,
    load_config,
)


class TestEnvVarReference:
    """Tests for _is_env_var_reference function."""

    @pytest.mark.unit
    def test_valid_env_var_reference(self):
        """Test that valid ${VAR} patterns are detected."""
        assert _is_env_var_reference("${MY_VAR}")
        assert _is_env_var_reference("prefix_${MY_VAR}_suffix")
        assert _is_env_var_reference("${VAR1}_${VAR2}")

    @pytest.mark.unit
    def test_invalid_env_var_reference(self):
        """Test that non-env-var strings are not detected."""
        assert not _is_env_var_reference("plain_string")
        assert not _is_env_var_reference("$VAR")  # Missing braces
        assert not _is_env_var_reference("{VAR}")  # Missing $
        assert not _is_env_var_reference("")
        assert not _is_env_var_reference(123)  # type: ignore


class TestResolveValue:
    """Tests for _resolve_value function."""

    @pytest.mark.unit
    def test_resolve_plain_string(self):
        """Test that plain strings are returned as-is."""
        assert _resolve_value("plain_string") == "plain_string"

    @pytest.mark.unit
    def test_resolve_plain_values(self):
        """Test that non-string values are returned as-is."""
        assert _resolve_value(123) == 123
        assert _resolve_value(True) is True
        assert _resolve_value(None) is None

    @pytest.mark.unit
    def test_resolve_file_path(self):
        """Test reading value from file (Docker secrets pattern)."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("secret_value\n")
            temp_path = f.name

        try:
            result = _resolve_value(temp_path)
            assert result == "secret_value"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_resolve_nonexistent_file_path(self):
        """Test that non-existent file paths are returned as-is."""
        fake_path = "/nonexistent/path/to/secret"
        assert _resolve_value(fake_path) == fake_path

    @pytest.mark.unit
    def test_resolve_dict_recursively(self):
        """Test recursive resolution in dictionaries."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("nested_secret")
            temp_path = f.name

        try:
            data = {"key1": "value1", "key2": temp_path, "nested": {"key3": temp_path}}
            result = _resolve_value(data)
            assert result["key1"] == "value1"
            assert result["key2"] == "nested_secret"
            assert result["nested"]["key3"] == "nested_secret"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_resolve_list_recursively(self):
        """Test recursive resolution in lists."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("list_secret")
            temp_path = f.name

        try:
            data = ["value1", temp_path, 123]
            result = _resolve_value(data)
            assert result == ["value1", "list_secret", 123]
        finally:
            Path(temp_path).unlink()


class TestExpandEnvVars:
    """Tests for _expand_env_vars function."""

    @pytest.mark.unit
    def test_expand_defined_env_var(self):
        """Test expansion of defined environment variables."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            data = {"key": "${TEST_VAR}"}
            result = _expand_env_vars(data)
            assert result["key"] == "test_value"

    @pytest.mark.unit
    def test_expand_undefined_env_var_required_field(self):
        """Test that undefined env vars in required fields are kept."""
        data = {"tautulli_url": "${UNDEFINED_VAR}"}
        result = _expand_env_vars(data)
        assert result["tautulli_url"] == "${UNDEFINED_VAR}"

    @pytest.mark.unit
    def test_expand_undefined_env_var_optional_field(self):
        """Test that undefined env vars in optional fields are omitted."""
        data = {"discord_webhook_url": "${UNDEFINED_VAR}"}
        result = _expand_env_vars(data)
        assert "discord_webhook_url" not in result

    @pytest.mark.unit
    def test_expand_empty_env_var_required_field(self):
        """Test that empty env vars in required fields are kept."""
        with patch.dict(os.environ, {"TEST_VAR": ""}):
            data = {"tautulli_url": "${TEST_VAR}"}
            result = _expand_env_vars(data)
            assert result["tautulli_url"] == ""

    @pytest.mark.unit
    def test_expand_empty_env_var_optional_field(self, caplog):
        """Test that empty env vars in optional fields are omitted with warning."""
        with patch.dict(os.environ, {"TEST_VAR": ""}):
            data = {"discord_webhook_url": "${TEST_VAR}"}
            result = _expand_env_vars(data)
            assert "discord_webhook_url" not in result
            assert "defined but empty" in caplog.text

    @pytest.mark.unit
    def test_expand_nested_dict(self):
        """Test recursive expansion in nested dictionaries."""
        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}):
            data = {"outer": "${VAR1}", "nested": {"inner": "${VAR2}"}}
            result = _expand_env_vars(data)
            assert result["outer"] == "value1"
            assert result["nested"]["inner"] == "value2"

    @pytest.mark.unit
    def test_expand_list(self):
        """Test expansion in lists."""
        with patch.dict(os.environ, {"VAR1": "value1"}):
            data = {"items": ["${VAR1}", "static", "${VAR1}"]}
            result = _expand_env_vars(data)
            assert result["items"] == ["value1", "static", "value1"]


class TestConfigModel:
    """Tests for Config Pydantic model validation."""

    @pytest.mark.unit
    def test_minimal_valid_config(self):
        """Test creating config with only required fields."""
        config = Config(
            tautulli_url="http://localhost:8181",
            tautulli_api_key="test_api_key",
            run_once=True,  # Avoid needing cron_schedule
        )
        assert config.tautulli_url == "http://localhost:8181"
        assert config.tautulli_api_key == "test_api_key"
        assert config.days_back == 7  # Default value
        assert config.run_once is True

    @pytest.mark.unit
    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config(tautulli_url="http://localhost:8181")  # Missing api_key

        assert "tautulli_api_key" in str(exc_info.value)

    @pytest.mark.unit
    def test_log_level_validation_valid(self):
        """Test that valid log levels are accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = Config(
                tautulli_url="http://localhost:8181", tautulli_api_key="test_key", log_level=level, run_once=True
            )
            assert config.log_level == level

    @pytest.mark.unit
    def test_log_level_validation_case_insensitive(self):
        """Test that log level validation is case-insensitive."""
        config = Config(
            tautulli_url="http://localhost:8181", tautulli_api_key="test_key", log_level="info", run_once=True
        )
        assert config.log_level == "INFO"

    @pytest.mark.unit
    def test_log_level_validation_invalid(self):
        """Test that invalid log levels raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                tautulli_url="http://localhost:8181", tautulli_api_key="test_key", log_level="INVALID", run_once=True
            )

        assert "log_level" in str(exc_info.value)


class TestBootstrapLogLevel:
    """Tests for get_bootstrap_log_level helper."""

    @pytest.mark.unit
    def test_bootstrap_log_level_from_config_file(self):
        """Reads and normalizes a valid log level from config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.safe_dump({"log_level": "debug"}, f)
            temp_path = f.name

        try:
            assert get_bootstrap_log_level(temp_path) == "DEBUG"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_bootstrap_log_level_invalid_value_falls_back_to_info(self):
        """Invalid log level falls back to INFO."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.safe_dump({"log_level": "verbose"}, f)
            temp_path = f.name

        try:
            assert get_bootstrap_log_level(temp_path) == "INFO"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_bootstrap_log_level_missing_file_falls_back_to_info(self):
        """Missing config file falls back to INFO."""
        assert get_bootstrap_log_level("/nonexistent/config.yml") == "INFO"

    @pytest.mark.unit
    def test_bootstrap_log_level_from_env_var(self):
        """Expands env var references in log_level before validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.safe_dump({"log_level": "${TEST_LOG_LEVEL}"}, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"TEST_LOG_LEVEL": "WARNING"}):
                assert get_bootstrap_log_level(temp_path) == "WARNING"
        finally:
            Path(temp_path).unlink()


class TestConfigValidation:
    """Additional validation tests for Config model."""

    @pytest.mark.unit
    def test_cron_schedule_required_when_not_run_once(self):
        """Test that cron_schedule is required when run_once is False."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                tautulli_url="http://localhost:8181", tautulli_api_key="test_key", run_once=False, cron_schedule=None
            )

        assert "cron_schedule is required" in str(exc_info.value)

    @pytest.mark.unit
    def test_cron_schedule_not_required_when_run_once(self):
        """Test that cron_schedule is optional when run_once is True."""
        config = Config(
            tautulli_url="http://localhost:8181", tautulli_api_key="test_key", run_once=True, cron_schedule=None
        )
        assert config.run_once is True
        assert config.cron_schedule is None

    @pytest.mark.unit
    def test_days_back_validation_positive(self):
        """Test that days_back must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            Config(tautulli_url="http://localhost:8181", tautulli_api_key="test_key", days_back=0, run_once=True)

        assert "days_back" in str(exc_info.value)

    @pytest.mark.unit
    def test_initial_batch_size_validation_range(self):
        """Test that initial_batch_size is within valid range."""
        # Valid range
        config = Config(
            tautulli_url="http://localhost:8181", tautulli_api_key="test_key", initial_batch_size=500, run_once=True
        )
        assert config.initial_batch_size == 500

        # Too small
        with pytest.raises(ValidationError):
            Config(
                tautulli_url="http://localhost:8181", tautulli_api_key="test_key", initial_batch_size=0, run_once=True
            )

        # Too large
        with pytest.raises(ValidationError):
            Config(
                tautulli_url="http://localhost:8181",
                tautulli_api_key="test_key",
                initial_batch_size=10001,
                run_once=True,
            )

    @pytest.mark.unit
    def test_unresolved_env_var_detection_in_required_fields(self):
        """Test detection of unresolved env vars in required fields."""
        with pytest.raises(ValidationError) as exc_info:
            Config(tautulli_url="${UNSET_VAR}", tautulli_api_key="test_key", run_once=True)

        error_msg = str(exc_info.value)
        assert "Unresolved environment variable" in error_msg
        assert "${UNSET_VAR}" in error_msg

    @pytest.mark.unit
    def test_default_values(self):
        """Test that default values are correctly applied."""
        config = Config(tautulli_url="http://localhost:8181", tautulli_api_key="test_key", run_once=True)
        assert config.days_back == 7
        assert config.plex_url == "https://app.plex.tv"
        assert config.log_level == "INFO"
        assert config.discord_webhook_url is None
        assert config.plex_server_id is None


class TestLoadConfig:
    """Tests for load_config function."""

    @pytest.mark.unit
    def test_load_valid_config_file(self):
        """Test loading a valid configuration file."""
        config_data = {
            "tautulli_url": "http://localhost:8181",
            "tautulli_api_key": "test_api_key",
            "run_once": True,
            "days_back": 14,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.tautulli_url == "http://localhost:8181"
            assert config.days_back == 14
            assert config.run_once is True
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_load_config_with_env_vars(self):
        """Test loading config with environment variable interpolation."""
        config_data = {
            "tautulli_url": "${TEST_TAUTULLI_URL}",
            "tautulli_api_key": "${TEST_TAUTULLI_KEY}",
            "run_once": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"TEST_TAUTULLI_URL": "http://env-url:8181", "TEST_TAUTULLI_KEY": "env-key"}):
                config = load_config(temp_path)
                assert config.tautulli_url == "http://env-url:8181"
                assert config.tautulli_api_key == "env-key"
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_load_config_with_docker_secrets(self):
        """Test loading config with Docker secrets (file paths)."""
        # Create secret files
        with tempfile.TemporaryDirectory() as temp_dir:
            secret_file = Path(temp_dir) / "api_key_secret"
            secret_file.write_text("secret_from_file")

            config_data = {
                "tautulli_url": "http://localhost:8181",
                "tautulli_api_key": "${API_KEY_FILE}",
                "run_once": True,
            }

            config_file = Path(temp_dir) / "config.yml"
            config_file.write_text(yaml.dump(config_data))

            with patch.dict(os.environ, {"API_KEY_FILE": str(secret_file)}):
                config = load_config(str(config_file))
                assert config.tautulli_api_key == "secret_from_file"

    @pytest.mark.unit
    def test_load_config_file_not_found(self):
        """Test that FileNotFoundError is raised for missing config."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yml")

    @pytest.mark.unit
    def test_load_config_invalid_yaml(self):
        """Test that invalid YAML raises an error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("invalid: yaml: content: {{{}}")
            temp_path = f.name

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_load_config_validation_failure(self):
        """Test that invalid config data raises ValidationError."""
        config_data = {
            "tautulli_url": "http://localhost:8181",
            # Missing required tautulli_api_key
            "run_once": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValidationError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_load_config_fails_for_missing_required_secret_file(self):
        """Required fields pointing to missing secret files should fail fast."""
        config_data = {
            "tautulli_url": "http://localhost:8181",
            "tautulli_api_key": "/nonexistent/path/to/secret",
            "run_once": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="does not exist or is not a regular file"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    @pytest.mark.unit
    def test_load_config_fails_for_empty_required_secret_file(self):
        """Required fields pointing to empty secret files should fail fast."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_secret = Path(temp_dir) / "empty_secret"
            empty_secret.write_text("\n")

            config_data = {
                "tautulli_url": "http://localhost:8181",
                "tautulli_api_key": str(empty_secret),
                "run_once": True,
            }

            config_file = Path(temp_dir) / "config.yml"
            config_file.write_text(yaml.dump(config_data))

            with pytest.raises(ValueError, match="file is empty"):
                load_config(str(config_file))
