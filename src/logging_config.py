import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("/app/logs")
LOG_FILE = LOG_DIR / "app.log"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Sets up console logging with formatted output.
    Reconfigures existing handlers if called multiple times.

    Args:
        log_level: Logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, str(log_level).upper(), logging.INFO)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                filename=LOG_FILE,
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
            ),
        ],
        force=True,
    )
