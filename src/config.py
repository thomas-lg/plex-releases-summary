"""Configuration module for loading and validating application settings from YAML."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
import re
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


def _resolve_value(value: Any) -> Any:
    """
    Resolve a configuration value, reading from file if it's a file path.
    
    If the value is a string starting with '/', attempts to read it as a file path.
    This supports Docker secrets pattern where env vars point to secret files.
    
    Args:
        value: The value to resolve (can be any type)
        
    Returns:
        The resolved value - file contents if applicable, otherwise original value
        
    Examples:
        "/run/secrets/api_key" -> reads and returns file content
        "my-api-key" -> returns "my-api-key" as-is
        123 -> returns 123 as-is
    """
    if isinstance(value, str) and value.startswith("/"):
        file_path = Path(value)
        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text().strip()
                logger.info(f"Successfully read secret from file: {value}")
                return content
            except Exception as e:
                logger.warning(f"Failed to read file {value}: {e}")
                # Return original value if read fails
                return value
        else:
            # Path doesn't exist - might be a regular value, not a file path
            logger.info(f"Path {value} does not exist, treating as literal value")
            return value
    elif isinstance(value, dict):
        return {k: _resolve_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_value(item) for item in value]
    
    return value


def _expand_env_vars(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively expand environment variables in dictionary values.
    
    Supports ${VAR} syntax for environment variable substitution.
    After expansion, also resolves any file paths (for secret files).
    
    Args:
        data: Dictionary with potential ${VAR} references
        
    Returns:
        Dictionary with all environment variables expanded and files resolved
        
    Examples:
        {"key": "${API_KEY}"} -> {"key": "actual_api_key_value"}
        {"key": "${SECRET_FILE}"} where SECRET_FILE=/run/secrets/key
            -> {"key": "contents_of_secret_file"}
    """
    expanded = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Expand environment variables
            expanded_value = os.path.expandvars(value)
            # Then try to resolve as file path
            expanded[key] = _resolve_value(expanded_value)
        elif isinstance(value, dict):
            expanded[key] = _expand_env_vars(value)
        elif isinstance(value, list):
            expanded[key] = [
                os.path.expandvars(item) if isinstance(item, str) else item
                for item in value
            ]
            # Resolve file paths in list items
            expanded[key] = [_resolve_value(item) for item in expanded[key]]
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
    tautulli_url: str = Field(
        ...,
        description="Full URL to Tautulli instance (e.g., http://localhost:8181)"
    )
    tautulli_api_key: str = Field(
        ...,
        description="Tautulli API key for authentication"
    )
    
    # Core Settings (Optional with defaults)
    days_back: int = Field(
        default=7,
        description="Number of days to look back for media releases (default: 7)",
        ge=1
    )
    
    # Scheduling (Optional with defaults)
    cron_schedule: Optional[str] = Field(
        default="0 16 * * SUN",
        description="CRON expression for scheduled execution (default: '0 16 * * SUN' - weekly Sunday 4pm)"
    )
    
    # Discord Configuration (Optional)
    discord_webhook_url: Optional[str] = Field(
        None,
        description="Discord webhook URL for notifications"
    )
    
    # Plex Configuration (Optional)
    plex_url: str = Field(
        "https://app.plex.tv",
        description="Plex server URL for media links"
    )
    plex_server_id: Optional[str] = Field(
        None,
        description="Plex server machine identifier (auto-detected if not set)"
    )
    
    # Execution Mode (Optional)
    run_once: bool = Field(
        False,
        description="Set to true for one-shot execution instead of scheduled"
    )
    
    # Advanced Settings (Optional)
    log_level: str = Field(
        "INFO",
        description="Logging verbosity level"
    )
    initial_batch_size: Optional[int] = Field(
        None,
        description="Override batch size for Tautulli API fetching",
        ge=1,
        le=10000
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard Python logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got '{v}'"
            )
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
        """Detect unresolved environment variable references like ${UNDEFINED_VAR}."""
        import re
        env_var_pattern = re.compile(r'\$\{[^}]+\}')
        
        # Check all string fields for unresolved ${VAR} patterns
        string_fields = [
            ('tautulli_url', self.tautulli_url),
            ('tautulli_api_key', self.tautulli_api_key),
            ('cron_schedule', self.cron_schedule),
            ('discord_webhook_url', self.discord_webhook_url),
            ('plex_url', self.plex_url),
            ('plex_server_id', self.plex_server_id),
            ('log_level', self.log_level),
        ]
        
        for field_name, field_value in string_fields:
            if field_value and isinstance(field_value, str):
                match = env_var_pattern.search(field_value)
                if match:
                    unresolved_var = match.group(0)
                    raise ValueError(
                        f"Unresolved environment variable: {unresolved_var} in field '{field_name}'. "
                        f"Ensure the environment variable is set or remove the reference from config.yml."
                    )
        
        return self


def load_config(config_path: str = "/app/configs/config.yml") -> Config:
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
            f"Please create a config.yml file based on config.yml.example"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        # Load YAML file
        logger.info(f"Loading configuration from {config_path}")
        with open(config_file, "r") as f:
            raw_config = yaml.safe_load(f)
        # Check for unresolved environment variables in required fields
        env_var_pattern = re.compile(r'\$\{[^}]+\}')
        required_fields = ["tautulli_url", "tautulli_api_key"]
        missing_vars = []

        for field in required_fields:
            value = raw_config.get(field)
            if isinstance(value, str):
                matches = env_var_pattern.findall(os.path.expandvars(value))
                if matches:
                    missing_vars.extend([f"{field}: {match}" for match in matches])

        if missing_vars:
            error_msg = (
                "Unresolved environment variable placeholders found in required fields:\n"
                + "\n".join(missing_vars)
                + "\nPlease set the missing environment variables or update config.yml."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        if raw_config is None:
            raise ValueError("Configuration file is empty")
        if not isinstance(raw_config, dict):
            raise ValueError("config.yml must contain a mapping/object at the root (not a list, string, or other type)")
        
        # Expand environment variables and resolve file paths
        expanded_config = _expand_env_vars(raw_config)
        
        # Validate and create Config instance
        config = Config(**expanded_config)
        
        logger.info("Configuration loaded and validated successfully")
        logger.info(f"Config: run_once={config.run_once}, log_level={config.log_level}")
        
        return config
        
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse YAML configuration: {e}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Failed to load configuration: {e}"
        logger.error(error_msg)
        raise
