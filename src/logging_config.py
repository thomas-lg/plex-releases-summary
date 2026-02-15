import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Sets up console logging with formatted output.
    
    Args:
        log_level: Logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, str(log_level).upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
