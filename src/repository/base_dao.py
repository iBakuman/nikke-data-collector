from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from repository.connection import get_db_connection

T = TypeVar('T')

class BaseDAO:
    """
    Base Data Access Object class that provides common functionality for all DAOs.
    
    This class handles database connection management and provides a template
    for DAO operations.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the base DAO with a database path
        
        Args:
            db_path: Path to the SQLite database file, or None to use default
        """
        self.db_path = db_path
    
    def with_connection(self, operation: Callable[[Any], T]) -> T:
        """
        Execute a database operation with a database connection
        
        This method provides a connection to the operation callback and handles
        the context management of the connection.
        
        Args:
            operation: A function that takes a connection and returns a result
            
        Returns:
            The result of the operation
        """
        with get_db_connection(self.db_path) as conn:
            return operation(conn)
