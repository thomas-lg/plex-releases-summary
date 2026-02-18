"""Unit tests for logging configuration module."""

import logging
import sys
from logging.handlers import RotatingFileHandler

import pytest

from src import logging_config


@pytest.fixture(autouse=True)
def cleanup_logging_handlers():
    """Ensures root logger handlers do not leak between tests."""
    yield
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)


class TestLoggingSetup:
    """Tests for setup_logging function."""

    @pytest.mark.unit
    def test_setup_logging_creates_rotating_file_handler(self, monkeypatch, tmp_path):
        """Configures both stdout and rotating file handlers with expected limits."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "app.log"

        monkeypatch.setattr(logging_config, "LOG_DIR", log_dir)
        monkeypatch.setattr(logging_config, "LOG_FILE", log_file)

        logging_config.setup_logging("DEBUG")

        root_logger = logging.getLogger()
        handlers = root_logger.handlers

        stream_handlers = [
            handler
            for handler in handlers
            if isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, RotatingFileHandler)
            and getattr(handler, "stream", None) is sys.stdout
        ]
        file_handlers = [handler for handler in handlers if isinstance(handler, RotatingFileHandler)]

        assert root_logger.level == logging.DEBUG
        assert stream_handlers
        assert len(file_handlers) == 1

        rotating_handler = file_handlers[0]
        assert rotating_handler.maxBytes == logging_config.LOG_MAX_BYTES
        assert rotating_handler.backupCount == logging_config.LOG_BACKUP_COUNT
        assert rotating_handler.baseFilename == str(log_file)
        assert log_dir.exists()

    @pytest.mark.unit
    def test_setup_logging_invalid_level_falls_back_to_info(self, monkeypatch, tmp_path):
        """Invalid log level string defaults to INFO."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "app.log"

        monkeypatch.setattr(logging_config, "LOG_DIR", log_dir)
        monkeypatch.setattr(logging_config, "LOG_FILE", log_file)

        logging_config.setup_logging("NOT_A_LEVEL")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
