"""
Overlay widget for capturing user interactions.

This module provides a transparent overlay widget that captures
mouse events and displays visual elements for user interaction.
"""
from typing import Any, List, Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QCloseEvent, QGuiApplication
from PySide6.QtWidgets import QWidget

from collector.window_manager import WindowManager
from log.config import get_logger
from picker.overlay.visual_elements import VisualElement

logger = get_logger(__name__)




class OverlayWidget(QWidget):
    """Transparent overlay widget for capturing user interactions."""

    # Raw mouse event signals
    mouse_pressed = Signal(QMouseEvent)
    mouse_moved = Signal(QMouseEvent)
    mouse_released = Signal(QMouseEvent)
    mouse_dragged = Signal(QPoint, QPoint)  # Start and current points

    def __init__(self, window_manager: WindowManager, parent: Optional[QWidget] = None):
        """Initialize the overlay widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.BypassWindowManagerHint
        )
        self.window_manager = window_manager
        self.setMouseTracking(True)  # Enable mouse tracking
        # Visual elements to display
        self._visual_elements: List[VisualElement] = []

        # Mouse tracking state
        self._is_dragging = False
        self._drag_start = QPoint()
        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.update_overlay_position)
        self.timer.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        # TODO
        self.timer.disconnect()
        super().closeEvent(event)

    def setGeometry(self, rect: QRect, /):
        screen = QGuiApplication.primaryScreen()
        ratio = screen.devicePixelRatio()
        newRect = QRect(int(rect.left() / ratio), int(rect.top() / ratio), int(rect.width() / ratio), int(rect.height() / ratio))
        super().setGeometry(newRect)

    def show(self) -> None:
        """Show the overlay widget."""
        rect = self.window_manager.rect
        self.setGeometry(QRect(rect.left, rect.top, rect.width, rect.height))
        self.timer.start()
        super().show()

    def update_overlay_position(self):
        current_rect = self.window_manager.rect
        if not current_rect:
            logger.warning("Could not get current Nikke window rect.")
            return

        current_pos = QPoint(current_rect.left, current_rect.top)
        current_size = (current_rect.width, current_rect.height)
        overlay_pos = self.pos()
        overlay_size = self.width(), self.height()
        if current_pos != overlay_pos or current_size != overlay_size:
            logger.info(f"Nikke window changed. Updating overlay geometry to {current_rect}")
            self.setGeometry(QRect( current_rect.left, current_rect.top, current_rect.width, current_rect.height))

    def hide(self):
        self.timer.stop()
        super().hide()

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

        super().paintEvent(event)  # Call parent's paintEvent()

    def get_geometry(self) -> QRect:
        """Get the current geometry of the overlay.

        Returns:
            Current geometry as QRect
        """
        return self.geometry()
