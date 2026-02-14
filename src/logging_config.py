import logging
import sys
import os


def setup_logging() -> None:
    """
    Configure logging for the application.

    Sets up console logging with formatted output. Log level can be controlled
    via the LOG_LEVEL environment variable (default: INFO).
    """
    # Safely get log level with fallback
    log_level = os.getenv("LOG_LEVEL", "INFO")
    level = getattr(logging, str(log_level).upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
