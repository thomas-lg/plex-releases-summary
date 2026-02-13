import logging
import sys
import os

def setup_logging():
    # Safely get log level with fallback
    log_level = os.getenv("LOG_LEVEL", "INFO")
    level = getattr(logging, str(log_level).upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )