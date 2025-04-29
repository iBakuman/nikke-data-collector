"""
Overlay widget for capturing user interactions.

This module provides a transparent overlay widget that captures
mouse events and displays visual elements for user interaction.
"""
from typing import Any, List, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import QWidget

from picker.overlay.visual_elements import VisualElement


class OverlayWidget(QWidget):
    """Transparent overlay widget for capturing user interactions."""
    
    # Raw mouse event signals
    mouse_pressed = Signal(QMouseEvent)
    mouse_moved = Signal(QMouseEvent)
    mouse_released = Signal(QMouseEvent)
    mouse_dragged = Signal(QPoint, QPoint)  # Start and current points
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the overlay widget.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setMouseTracking(True)  # Enable mouse tracking
        
        # Visual elements to display
        self._visual_elements: List[VisualElement] = []
        
        # Mouse tracking state
        self._is_dragging = False
        self._drag_start = QPoint()
    
    def add_visual_element(self, element: VisualElement) -> None:
        """Add a visual element to be displayed on the overlay.
        
        Args:
            element: The visual element to add
        """
        self._visual_elements.append(element)
        self.update()
    
    def clear_visual_elements(self) -> None:
        """Clear all visual elements from the overlay."""
        self._visual_elements.clear()
        self.update()
    
    def get_visual_elements(self) -> List[VisualElement]:
        """Get all current visual elements.
        
        Returns:
            List of current visual elements
        """
        return self._visual_elements.copy()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.
        
        Args:
            event: The mouse press event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start = event.position().toPoint()
            self.mouse_pressed.emit(event)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events.
        
        Args:
            event: The mouse move event
        """
        current_pos = event.position().toPoint()
        self.mouse_moved.emit(event)
        
        if self._is_dragging:
            self.mouse_dragged.emit(self._drag_start, current_pos)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events.
        
        Args:
            event: The mouse release event
        """
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.mouse_released.emit(event)
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event: Any) -> None:
        """Paint the overlay with all visual elements.
        
        Args:
            event: The paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))  # Almost transparent
        
        # Draw all visual elements
        for element in self._visual_elements:
            element.draw(painter)
    
    def get_geometry(self) -> QRect:
        """Get the current geometry of the overlay.
        
        Returns:
            Current geometry as QRect
        """
        return self.geometry() 
