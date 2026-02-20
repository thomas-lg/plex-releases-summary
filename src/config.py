"""Configuration module for loading and validating application settings from YAML."""

import logging
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict, cast

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# Type definitions for configuration


class ConfigInput(TypedDict, total=False):
    tautulli_url: str
    tautulli_api_key: str
    days_back: int
    cron_schedule: str | None
    discord_webhook_url: str | None
    plex_url: str
    plex_server_id: str | None
    run_once: bool
    log_level: str
    initial_batch_size: int | None


logger = logging.getLogger(__name__)

# Constants
ENV_VAR_PATTERN = re.compile(r"\$\{[^}]+\}")
REQUIRED_FIELDS = {"tautulli_url", "tautulli_api_key"}
DEFAULT_CONFIG_PATH = "/app/configs/config.yml"

type ConfigScalar = str | int | float | bool | None
type ConfigValue = ConfigScalar | list["ConfigValue"] | dict[str, "ConfigValue"]


def _is_env_var_reference(value: str) -> bool:
    """
    Check if a string value is an environment variable reference.

    Args:
        value: String to check

    Returns:
        True if value matches ${VAR} pattern, False otherwise
    """
    return isinstance(value, str) and bool(ENV_VAR_PATTERN.search(value))


def _resolve_value(value: ConfigValue, required_field: str | None = None) -> ConfigValue:
    """
    Resolve a configuration value, reading from file if it's a file path.

    If the value is a string starting with '/', attempts to read it as a file path.
    This supports Docker secrets pattern where env vars point to secret files.

    Args:
        value: The value to resolve (can be any type)
        required_field: Required field name for strict secret-file validation

    Returns:
        The resolved value - file contents if applicable, otherwise original value

    Raises:
        ValueError: If secret file exceeds size limit or contains invalid data

    Examples:
        "/run/secrets/api_key" -> reads and returns file content
        "my-api-key" -> returns "my-api-key" as-is
        123 -> returns 123 as-is
    """
    max_secret_size = 10 * 1024  # 10KB max for secret files

    if isinstance(value, str) and value.startswith("/"):
        file_path = Path(value)
        if file_path.exists() and file_path.is_file():
            try:
                # Check file size before reading
                file_size = file_path.stat().st_size
                if file_size > max_secret_size:
                    logger.error(
                        "Secret file %s exceeds maximum size (%d bytes > %d bytes). "
                        "This may not be a valid secret file.",
                        value,
                        file_size,
                        max_secret_size,
                    )
                    raise ValueError(f"Secret file {value} too large: {file_size} bytes")

                content = file_path.read_text().strip()

                # Validate content is reasonable (printable ASCII or UTF-8)
                if not content:
                    if required_field:
                        raise ValueError(
                            f"Required field '{required_field}' references secret file '{value}', "
                            "but the file is empty."
                        )
                    logger.warning("Secret file %s is empty", value)
                    return value

                logger.info("Successfully read secret from file: %s", value)
                return content
            except OSError as e:
                if required_field:
                    raise ValueError(
                        f"Required field '{required_field}' references secret file '{value}', "
                        f"but it could not be read: {e}"
                    ) from e
                logger.warning("I/O error reading file %s: %s", value, e)
                return value
            except UnicodeDecodeError as e:
                logger.error("Secret file %s contains invalid UTF-8 data: %s", value, e)
                raise ValueError(f"Secret file {value} is not valid text") from None
        else:
            if required_field:
                raise ValueError(
                    f"Required field '{required_field}' references secret file '{value}', "
                    "but the file does not exist or is not a regular file."
                )
            logger.info("Path %s does not exist, treating as literal value", value)
            return value
    elif isinstance(value, dict):
        return {k: _resolve_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_value(item) for item in value]

    return value


def _expand_env_vars(data: Mapping[str, ConfigValue]) -> dict[str, ConfigValue]:
    """
    Recursively expand environment variables in dictionary values.

    Supports ${VAR} syntax for environment variable substitution.
    After expansion, also resolves any file paths (for secret files).

    For optional fields:
    - Undefined env vars: Silently omitted (Pydantic defaults apply)
    - Empty env vars: Logs WARNING and omitted (possible config mistake)
    For required fields: Undefined/empty env vars are kept and caught by validation.

    Args:
        data: Dictionary with potential ${VAR} references

    Returns:
        Dictionary with all environment variables expanded and files resolved
    """
    expanded: dict[str, ConfigValue] = {}
    for key, value in data.items():
        if isinstance(value, str):
            is_env_var_ref = _is_env_var_reference(value)
            expanded_value = os.path.expandvars(value)

            # Check if there are still unresolved env vars after expansion (undefined)
            if ENV_VAR_PATTERN.search(expanded_value):
                if key in REQUIRED_FIELDS:
                    expanded[key] = expanded_value
                # For optional fields, silently omit (expected behavior)
            # Check if env var expanded to empty string (defined but empty)
            elif is_env_var_ref and expanded_value == "":
                if key in REQUIRED_FIELDS:
                    expanded[key] = expanded_value
                else:
                    logger.warning(
                        "Environment variable for field '%s' is defined but empty. Using default value instead.",
                        key,
                    )
            else:
                required_field = key if key in REQUIRED_FIELDS else None
                expanded[key] = _resolve_value(expanded_value, required_field=required_field)
        elif isinstance(value, dict):
            expanded[key] = _expand_env_vars(value)
        elif isinstance(value, list):
            expanded_list: list[ConfigValue] = []
            for item in value:
                if isinstance(item, str):
                    expanded_item: ConfigValue = os.path.expandvars(item)
                else:
                    expanded_item = item
                expanded_list.append(_resolve_value(expanded_item))
            expanded[key] = expanded_list
        else:
            expanded[key] = value

    return expanded


class Config(BaseModel):
    """
    Application configuration with validation.

    All configuration values are loaded from config.yml with support for:
    - Static values in YAML
    - Environment variable interpolation: ${VAR_NAME}
    - Docker secrets: ${VAR} where VAR points to a file path
    """

    # Tautulli Configuration (Required)
    tautulli_url: str = Field(..., min_length=1, description="Full URL to Tautulli instance (e.g., http://localhost:8181)")
    tautulli_api_key: str = Field(..., min_length=1, description="Tautulli API key for authentication")

    # Core Settings (Optional with defaults)
    days_back: int = Field(default=7, description="Number of days to look back for media releases (default: 7)", ge=1)

    # Scheduling (Optional with defaults)
    cron_schedule: str | None = Field(
        default="0 16 * * SUN",
        description="CRON expression for scheduled execution (default: '0 16 * * SUN' - weekly Sunday 4pm)",
    )

    # Discord Configuration (Optional)
    discord_webhook_url: str | None = Field(None, description="Discord webhook URL for notifications")

    # Plex Configuration (Optional)
    plex_url: str = Field("https://app.plex.tv", description="Plex server URL for media links")
    plex_server_id: str | None = Field(None, description="Plex server machine identifier (auto-detected if not set)")

    # Execution Mode (Optional)
    run_once: bool = Field(False, description="Set to true for one-shot execution instead of scheduled")

    # Advanced Settings (Optional)
    log_level: str = Field("INFO", description="Logging verbosity level")
    initial_batch_size: int | None = Field(
        None, description="Override batch size for Tautulli API fetching", ge=1, le=10000
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard Python logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got '{v}'")
        return v_upper

    @model_validator(mode="after")
    def validate_cron_schedule_required(self) -> "Config":
        """Validate that cron_schedule is provided when run_once is False."""
        if not self.run_once and not self.cron_schedule:
            raise ValueError(
                "cron_schedule is required when run_once is False. "
                "Either set run_once: true or provide a cron_schedule."
            )
        return self

    @model_validator(mode="after")
    def validate_no_unresolved_env_vars(self) -> "Config":
        """Detect unresolved environment variable references in required fields."""
        required_fields = [
            ("tautulli_url", self.tautulli_url),
            ("tautulli_api_key", self.tautulli_api_key),
        ]

        for field_name, field_value in required_fields:
            if isinstance(field_value, str):
                match = ENV_VAR_PATTERN.search(field_value)
                if match:
                    raise ValueError(
                        f"Unresolved environment variable: {match.group(0)} in required field '{field_name}'. "
                        f"Ensure the environment variable is set or provide a value in config.yml."
                    )

        return self


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Config:
    """
    Load and validate configuration from YAML file.

    Supports:
    - Environment variable interpolation: ${VAR_NAME}
    - Docker secrets: variables pointing to file paths are automatically read

    Args:
        config_path: Path to config.yml file (default: /app/configs/config.yml)

    Returns:
        Validated Config instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        pydantic.ValidationError: If configuration validation fails

    Examples:
        >>> config = load_config()
        >>> print(config.tautulli_url)
        http://localhost:8181
    """
    config_file = Path(config_path)

    if not config_file.exists():
        error_msg = (
            f"Configuration file not found: {config_path}\n"
            "Please create a config.yml file based on configs/config.yml in the repository."
        )
        raise FileNotFoundError(error_msg)

    try:
        logger.info("Loading configuration from %s", config_path)
        with config_file.open("r") as f:
            raw_config = yaml.safe_load(f)

        if raw_config is None:
            raise ValueError("Configuration file is empty")
        if not isinstance(raw_config, dict):
            raise ValueError(
                "config.yml must contain a mapping/object at the root " "(not a list, string, or other type)"
            )

        # Expand environment variables and resolve file paths
        expanded_config = cast(ConfigInput, _expand_env_vars(raw_config))

        # Validate and create Config instance
        config = Config.model_validate(expanded_config)

        logger.info("Configuration loaded and validated successfully")
        logger.info("Config: run_once=%s, log_level=%s", config.run_once, config.log_level)

        return config

    except yaml.YAMLError:
        raise


def get_bootstrap_log_level(config_path: str = DEFAULT_CONFIG_PATH) -> str:
    """
    Read log_level from config file before full validation.

    This enables early logger setup so load-time logs can honor configured verbosity.
    Falls back to INFO for any missing/invalid/unreadable value.

    Args:
        config_path: Path to config.yml file

    Returns:
        Uppercased log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            return "INFO"

        with config_file.open("r") as f:
            raw_config = yaml.safe_load(f)

        if not isinstance(raw_config, dict):
            return "INFO"

        expanded = _expand_env_vars({"log_level": raw_config.get("log_level", "INFO")})
        level = expanded.get("log_level", "INFO")

        if not isinstance(level, str):
            return "INFO"

        return Config.validate_log_level(level.strip())
    except Exception:
        return "INFO"
