"""
Picker extension for pixel color element capture.

This module provides functionality to capture pixel color elements using
the overlay approach instead of dialog-based selection.
"""

from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)

from collector.logging_config import get_logger
from domain.color import Color
from domain.pixel_element import PixelColorElementEntity
from domain.regions import Point

logger = get_logger(__name__)


class PixelColorCaptureDialog(QDialog):
    """Dialog that manages the pixel color capture process using overlay."""

    def __init__(self, overlay_controller, parent=None):
        """Initialize the pixel color capture dialog.

        Args:
            overlay_controller: Controller managing the overlay widget
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Capture Pixel Colors")
        self.setWindowFlags(Qt.WindowType.Dialog |
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.FramelessWindowHint)

        self.overlay_controller = overlay_controller
        self.points_colors: List[PixelColorElementEntity] = []

        # Setup UI
        self._init_ui()

        # Connect to overlay controller signals
        self.overlay_controller.point_captured.connect(self._on_point_captured)

        # Start capture mode
        self.overlay_controller.start_pixel_capture_mode()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Click on the game window to capture pixel colors.\n"
            "Each click adds a point with its color.\n"
            "When finished, click Done."
        )
        layout.addWidget(instructions)

        # Status
        self.status_label = QLabel("No points captured yet")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.done_button = QPushButton("Done")
        self.done_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.done_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Position the dialog above the overlay
        self.resize(400, 150)

        # Position dialog based on overlay
        overlay_rect = self.overlay_controller.get_overlay_rect()
        if overlay_rect:
            self.move(
                overlay_rect.x() + (overlay_rect.width() - self.width()) // 2,
                overlay_rect.y() - self.height() - 10
            )

    @Slot(object)
    def _on_point_captured(self, point_color: PixelColorElementEntity):
        """Handle captured point from the overlay."""
        self.points_colors.append(point_color)

        # Update status
        point = point_color.point
        color = point_color.color
        self.status_label.setText(
            f"Added point at ({point.x}, {point.y}) with RGB({color.r},{color.g},{color.b}). "
            f"{len(self.points_colors)} points total."
        )

    def done(self, result_code):
        """Clean up when the dialog is closed."""
        # End capture mode in overlay controller
        self.overlay_controller.end_pixel_capture_mode()

        # Disconnect from signals
        self.overlay_controller.point_captured.disconnect(self._on_point_captured)

        # Call base implementation
        super().done(result_code)


def capture_pixel_colors(overlay_controller) -> List[PixelColorElementEntity]:
    """Start the pixel color capture process.

    Args:
        overlay_controller: Controller managing the overlay widget

    Returns:
        List of captured pixel color elements or empty list if cancelled
    """
    dialog = PixelColorCaptureDialog(overlay_controller)
    result = dialog.exec()

    # Return captured points or empty list if cancelled
    if result == QDialog.DialogCode.Accepted and dialog.points_colors:
        return dialog.points_colors

    return []
