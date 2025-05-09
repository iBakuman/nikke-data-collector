"""
Visual elements for the overlay system.

These classes define various visual elements that can be displayed
on the overlay, such as points, rectangles, and text.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen


class VisualElement(ABC):
    """Base abstract class for all visual elements that can be drawn on the overlay."""
    
    @abstractmethod
    def draw(self, painter: QPainter) -> None:
        """Draw this element using the provided painter.
        
        Args:
            painter: QPainter to use for drawing
        """
        pass


class PointElement(VisualElement):
    """A point element for displaying pixel positions with color information."""
    
    def __init__(
        self, 
        x: int, 
        y: int, 
        color: Union[Tuple[int, int, int], QColor],
        radius: int = 5, 
        border_color: QColor = QColor(255, 0, 0),
        border_width: int = 2
    ):
        """Initialize a point element.
        
        Args:
            x: X coordinate of the point
            y: Y coordinate of the point
            color: Color of the point (RGB tuple or QColor)
            radius: Radius of the point circle
            border_color: Color of the border
            border_width: Width of the border
        """
        self.x = x
        self.y = y
        self.color = color if isinstance(color, QColor) else QColor(color[0], color[1], color[2])
        self.radius = radius
        self.border_color = border_color
        self.border_width = border_width
    
    def draw(self, painter: QPainter) -> None:
        """Draw this point element.
        
        Args:
            painter: QPainter to use for drawing
        """
        # Draw outer border circle
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.setBrush(QColor(0, 0, 0, 0))  # Transparent fill
        painter.drawEllipse(QPoint(self.x, self.y), self.radius, self.radius)
        
        # Draw inner filled circle with the specified color
        painter.setPen(QPen(QColor(0, 0, 0, 0), 0))  # No border
        painter.setBrush(self.color)
        painter.drawEllipse(QPoint(self.x, self.y), self.radius - self.border_width, self.radius - self.border_width)


class RectangleElement(VisualElement):
    """A rectangle element for displaying regions or selections."""
    
    def __init__(
        self, 
        rect: QRect, 
        color: QColor = QColor(0, 255, 0), 
        width: int = 2,
        fill_color: Optional[QColor] = None
    ):
        """Initialize a rectangle element.
        
        Args:
            rect: The rectangle to draw
            color: Color of the rectangle border
            width: Width of the border
            fill_color: Optional color for filling the rectangle
        """
        self.rect = rect
        self.color = color
        self.width = width
        self.fill_color = fill_color
    
    def draw(self, painter: QPainter) -> None:
        """Draw this rectangle element.
        
        Args:
            painter: QPainter to use for drawing
        """
        painter.setPen(QPen(self.color, self.width))
        
        if self.fill_color:
            painter.setBrush(self.fill_color)
        else:
            painter.setBrush(QColor(0, 0, 0, 0))  # Transparent fill
        
        painter.drawRect(self.rect)


class TextElement(VisualElement):
    """A text element for displaying instructions or information."""
    
    def __init__(
        self, 
        text: str, 
        x: int, 
        y: int, 
        color: QColor = QColor(255, 255, 255),
        background: QColor = QColor(0, 0, 0, 180),
        padding: int = 5
    ):
        """Initialize a text element.
        
        Args:
            text: The text to display
            x: X coordinate for top-left corner
            y: Y coordinate for top-left corner
            color: Color of the text
            background: Background color
            padding: Padding around the text
        """
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.background = background
        self.padding = padding
    
    def draw(self, painter: QPainter) -> None:
        """Draw this text element.
        
        Args:
            painter: QPainter to use for drawing
        """
        font = painter.font()
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self.text)
        text_height = metrics.height()
        
        # Draw background with padding
        rect = QRect(
            self.x, 
            self.y, 
            text_width + self.padding * 2, 
            text_height + self.padding * 2
        )
        painter.fillRect(rect, self.background)
        
        # Draw the text
        painter.setPen(self.color)
        painter.drawText(
            self.x + self.padding, 
            self.y + self.padding + metrics.ascent(),  # Adjust for text baseline
            self.text
        ) 
