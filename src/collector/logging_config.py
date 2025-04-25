"""
Logging configuration module for NIKKE Arena application.
This module provides a centralized configuration for all loggers in the application.
"""

import logging
import os
import sys


def configure_logging(
        level=logging.INFO,
        log_file=None,
        include_file_info=True
):
    """
    Configure logging for the application

    Args:
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        include_file_info: Whether to include file info in log messages

    Returns:
        The configured root logger
    """
    # Create formatter
    if include_file_info:
        # Detailed format: includes timestamp, level, filename, line number and function name
        log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d - %(funcName)s] - %(message)s'
    else:
        # Simple format
        log_format = '%(asctime)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(log_format)

    # Configure handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler (if log file path is provided)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Force reconfiguration, overriding any existing configuration
    )

    # Return root logger
    return logging.getLogger()


def get_logger(name):
    """
    Get a logger with the specified name

    Args:
        name: Logger name, typically __name__

    Returns:
        A configured logger
    """
    return logging.getLogger(name)
