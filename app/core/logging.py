"""
Logging configuration for the application.

Provides structured logging with:
- Environment-aware log levels
- Consistent formatting
- Easy extension for future log handlers (file, remote, etc.)
"""

import logging
import sys
from typing import Optional

from app.core.config import get_settings


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure and return the application logger.
    
    Args:
        log_level: Override log level. If None, determined by environment.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    settings = get_settings()
    
    # Determine log level based on environment
    if log_level is None:
        log_level = "DEBUG" if settings.is_development else "INFO"
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Configure stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    
    # Get root logger for the application
    logger = logging.getLogger("education_rag")
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(stream_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the given name.
    
    Args:
        name: Name for the logger (typically __name__).
        
    Returns:
        logging.Logger: Child logger instance.
    """
    return logging.getLogger(f"education_rag.{name}")
