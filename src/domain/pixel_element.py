"""
Data Transfer Objects for Pixel Color Elements in the database.

This module provides DTO classes that represent database records for pixel color elements,
facilitating the transfer of data between the database and the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from dataclass_wizard import JSONPyWizard, JSONWizard

from domain.color import Color
from domain.regions import Point
from mixin.json import JSONSerializableMixin


@dataclass
class PixelColorPointEntity(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    id: Optional[int] = None
    element_id: Optional[int] = None
    point_x: int = 0
    point_y: int = 0
    total_width: int = 0
    total_height: int = 0
    color_r: int = 0
    color_g: int = 0
    color_b: int = 0

    def to_point_and_color(self) -> tuple[Point, Color]:
        """Convert entity data to Point and Color objects."""
        point = Point(
            x=self.point_x,
            y=self.point_y,
            total_width=self.total_width,
            total_height=self.total_height
        )

        color = Color(
            r=self.color_r,
            g=self.color_g,
            b=self.color_b
        )

        return point, color

    @classmethod
    def from_point_and_color(cls, point: Point, color: Color,
                             element_id: Optional[int] = None) -> 'PixelColorPointEntity':
        """Create entity from Point and Color objects."""
        return cls(
            element_id=element_id,
            point_x=point.x,
            point_y=point.y,
            total_width=point.total_width,
            total_height=point.total_height,
            color_r=color.r,
            color_g=color.g,
            color_b=color.b
        )


@dataclass
class PixelColorElementEntity(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    id: Optional[int] = None  # Primary key, None for new records
    name: str = ""  # Element name

    # Detection parameters
    tolerance: int = 10
    match_all: bool = True

    # Collection of points and colors
    points: List[PixelColorPointEntity] = field(default_factory=list)

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def get_points_colors(self) -> List[tuple[Point, Color]]:
        """Get list of Point and Color pairs from stored entities.
        
        Returns:
            List of (Point, Color) tuples
        """
        return [point_entity.to_point_and_color() for point_entity in self.points]

    def set_points_colors(self, points_colors: List[tuple[Point, Color]]) -> None:
        """Set points and colors from a list of Point and Color pairs.
        
        Args:
            points_colors: List of (Point, Color) tuples
        """
        self.points = []
        for point, color in points_colors:
            self.points.append(PixelColorPointEntity.from_point_and_color(point, color, self.id))
