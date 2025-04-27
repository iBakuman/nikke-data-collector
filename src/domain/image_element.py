"""
Data Transfer Objects for UI Elements in the database.

This module provides DTO classes that represent database records for UI elements,
facilitating the transfer of data between the database and the application.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ImageElementEntity:
    """Database representation of an ImageElement."""

    id: Optional[int] = None  # Primary key, None for new records
    name: str = ""  # Element name

    # Region data
    region_x: int = 0
    region_y: int = 0
    region_width: int = 0
    region_height: int = 0
    region_total_width: int = 0
    region_total_height: int = 0

    # Image data as binary blob
    image_data: Optional[bytes] = None

    # Detection parameters
    threshold: float = 0.8

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


