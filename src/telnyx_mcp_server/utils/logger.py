"""Logging utilities."""

import logging
import sys
from typing import Optional

from ..config import settings


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger.

    Args:
        name: Logger name

    Returns:
        logging.Logger: Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))

    # Add console handler if not already added
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, settings.log_level))
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
