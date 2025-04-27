"""
Base data importer classes and interfaces.

This module provides abstract base classes for importing data into DTOs
from various sources like directories, files, and JSON configurations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Generic type variable for any DTO class
T = TypeVar('T')

class DataImporter(Generic[T], ABC):
    """Abstract base class for all data importers.
    
    Each importer handles loading data for a specific DTO type from various sources.
    """
    
    @abstractmethod
    def import_from_directory(self, directory_path: str) -> List[T]:
        """Import data from a directory.
        
        Args:
            directory_path: Path to the directory containing data files
            
        Returns:
            List of imported DTO objects
        """
        pass
        
    @abstractmethod
    def import_from_file(self, file_path: str) -> List[T]:
        """Import data from a specific file.
        
        Args:
            file_path: Path to the file containing data
            
        Returns:
            List of imported DTO objects
        """
        pass
        
    @abstractmethod
    def import_from_json(self, json_path: str) -> List[T]:
        """Import data from a JSON configuration file.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            List of imported DTO objects
        """
        pass
        
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of file formats supported by this importer.
        
        Returns:
            List of supported file extensions (without dot)
        """
        pass
    
    def can_handle_file(self, file_path: str) -> bool:
        """Check if the importer can handle a given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file can be handled, False otherwise
        """
        path = Path(file_path)
        ext = path.suffix.lower()[1:]  # Remove the leading dot
        return ext in self.get_supported_formats() 
