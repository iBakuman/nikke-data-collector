import functools
import sqlite3
from typing import Any, Callable, Optional, TypeVar

from log.config import get_logger

logger = get_logger(__name__)

# Define return type for the decorator
T = TypeVar('T')

def db_operation(default_return_value: Any = None):
    """
    Decorator for database operations that handles common exceptions.

    Args:
        default_return_value: Value to return if an exception occurs

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except sqlite3.IntegrityError as e:
                # Handle constraint violations (unique, foreign key, etc.)
                logger.warning(f"{func.__name__} - IntegrityError: {e}")
                return default_return_value
            except sqlite3.Error as e:
                # Handle other SQLite errors
                logger.error(f"{func.__name__} - Database error: {e}")
                return default_return_value
        return wrapper
    return decorator
