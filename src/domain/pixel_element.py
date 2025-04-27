import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Tuple

from .color import Color
from .regions import Point


@dataclass
class PixelColorElementEntity:
    """Database representation of a PixelColorElement."""

    id: Optional[int] = None  # Primary key, None for new records
    name: str = ""  # Element name

    point: Point = None
    color: Color = None

    # Detection parameters
    tolerance: int = 10
    match_all: bool = True

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def set_points_colors(self,
                          points_colors: List[Tuple[Tuple[int, int, int, int, int], Tuple[int, int, int]]]) -> None:
        """Convert points_colors list to JSON string for storage.

        Format: [([x, y, total_width, total_height], [r, g, b]), ...]

        Args:
            points_colors: List of (point, color) tuples
        """
        serializable_data = [
            ([p[0], p[1], p[2], p[3]], [c[0], c[1], c[2]])
            for p, c in points_colors
        ]
        self.points_colors_json = json.dumps(serializable_data)

    def get_points_colors(self) -> List[Tuple[Tuple[int, int, int, int, int], Tuple[int, int, int]]]:
        """Convert stored JSON string back to points_colors list.

        Returns:
            List of (point, color) tuples
        """
        data = json.loads(self.points_colors_json)
        return [
            ((p[0], p[1], p[2], p[3]), (c[0], c[1], c[2]))
            for p, c in data
        ]
