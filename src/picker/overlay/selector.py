"""
Capture strategies for different element types.

This module provides strategies for capturing different types of elements
using the overlay system. Each strategy defines the interaction flow for
a specific type of element capture.
"""
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, TypeVar

from PySide6.QtCore import QObject, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                               QWidget)

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from domain.color import Color
from domain.pixel_element import PixelColorPointEntity
from domain.regions import Point
from picker.overlay.overlay_widget import OverlayWidget
from picker.overlay.visual_elements import (PointElement, RectangleElement,
                                            VisualElement)

logger = get_logger(__name__)


@dataclass
class StrategyInfo:
    """Information about a capture strategy."""
    type_id: str  # Unique identifier
    display_name: str  # User-friendly display name
    description: str  # Description of what this strategy captures
    strategy_class: Type['ElementSelector']  # Strategy class


# Type variable for result data
T = TypeVar('T')


class ElementSelector(QObject):
    selection_completed = Signal(object)  # Result data
    selection_cancelled = Signal()

    @classmethod
    @abstractmethod
    def get_strategy_info(cls) -> StrategyInfo:
        """Get information about this strategy.

        Returns:
            StrategyInfo object containing metadata about this strategy
        """
        pass

    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the capture strategy.

        Args:
            overlay: The overlay widget to display visual feedback
            window_capturer: The window capturer for screenshots
        """
        super().__init__()
        self.overlay = overlay
        self.window_capturer = window_capturer
        self.result_data: Any = None

        # Original visual elements to restore when complete
        self._original_visual_elements: List[VisualElement] = []

    def start_selection(self) -> QWidget:
        """Start the selection process.

        This method should:
        1. Save original overlay state
        2. Set up initial visual elements
        3. Create and return a control panel widget

        Returns:
            A widget containing controls for this selection strategy
        """
        # Save original overlay state
        self._original_visual_elements = self.overlay.get_visual_elements().copy()

        # Clear overlay for our elements
        self.overlay.clear_visual_elements()

        # Create control panel (implemented by subclasses)
        control_panel = self._create_control_panel()
        self.overlay.show()
        return control_panel

    def cancel_selection(self) -> None:
        """Cancel the selection process."""
        self._cleanup()
        self.selection_cancelled.emit()

    def complete_selection(self) -> None:
        """Complete the selection process with current result data."""
        if self.can_complete():
            self._cleanup()
            self.selection_completed.emit(self.result_data)
        else:
            # Subclasses should prevent this by disabling the complete button
            logger.warning("Attempted to complete selection without valid data")

    def _cleanup(self) -> None:
        """Clean up resources used during selection."""
        # Remove our visual elements
        self.overlay.clear_visual_elements()

        # Restore original elements
        for element in self._original_visual_elements:
            self.overlay.add_visual_element(element)

        # Disconnect any connected signals
        self._disconnect_signals()

    @abstractmethod
    def _create_control_panel(self) -> QWidget:
        """Create a control panel widget for this strategy.

        Returns:
            A widget containing controls for the capture process
        """
        pass

    @abstractmethod
    def can_complete(self) -> bool:
        """Check if the capture can be completed with current data.

        Returns:
            True if capture can be completed, False otherwise
        """
        pass

    def _connect_signals(self) -> None:
        """Connect to overlay signals needed by this strategy."""
        pass

    def _disconnect_signals(self) -> None:
        """Disconnect from overlay signals."""
        pass

    @classmethod
    @abstractmethod
    def create_visual_element(cls, config: Dict[str, Any]) -> VisualElement:
        """Create a visual element from configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Visual element created from config
        """
        pass

    @classmethod
    @abstractmethod
    def get_config_from_element(cls, element: VisualElement) -> Dict[str, Any]:
        """Get configuration from a visual element.

        Args:
            element: Visual element to extract config from

        Returns:
            Configuration dictionary
        """
        pass

    @classmethod
    def handles_element_type(cls, element: VisualElement) -> bool:
        """Check if this strategy can handle a specific visual element type.

        Args:
            element: Element to check

        Returns:
            True if this strategy can handle this element
        """
        return False


class ControlPanel(QWidget):
    """Base class for strategy control panels.

    This provides common UI elements and layout for all strategy control panels.
    """

    def __init__(self, strategy: 'ElementSelector', parent: Optional[QWidget] = None):
        """Initialize the control panel.

        Args:
            strategy: The strategy this panel controls
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.strategy = strategy

        # Set up layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # Add title
        info = strategy.get_strategy_info()
        title_label = QLabel(f"<h3>{info.display_name}</h3>")
        self.main_layout.addWidget(title_label)

        # Add description
        desc_label = QLabel(info.description)
        desc_label.setWordWrap(True)
        self.main_layout.addWidget(desc_label)

        # Content area (to be filled by subclasses)
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        # Add spacer
        self.main_layout.addStretch(1)

        # Buttons area
        self.buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.buttons_layout)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.strategy.cancel_selection)

        # Complete button
        self.complete_button = QPushButton("Complete")
        self.complete_button.clicked.connect(self.strategy.complete_selection)

        # Add buttons to layout
        self.buttons_layout.addWidget(self.cancel_button)
        self.buttons_layout.addStretch(1)
        self.buttons_layout.addWidget(self.complete_button)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    def keyPressEvent(self, event):
        """Handle key press events.

        Args:
            event: Key event
        """
        # Escape cancels capture
        if event.key() == Qt.Key.Key_Escape:
            self.strategy.cancel_selection()

        # Enter completes capture if it can be completed
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.strategy.can_complete():
                self.strategy.complete_selection()

        super().keyPressEvent(event)


class PixelColorSelector(ElementSelector):
    """Strategy for selecting pixel colors.

    This strategy allows users to click on points in the overlay to select
    the color at those points. It displays the selected points and their colors
    in the control panel, allowing users to remove points or complete the selection.
    """

    @classmethod
    def get_strategy_info(cls) -> StrategyInfo:
        """Get strategy information."""
        return StrategyInfo(
            type_id="pixel_color",
            display_name="Pixel Color",
            description="Select the color of specific pixels by clicking on them",
            strategy_class=cls
        )

    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the pixel color selector."""
        super().__init__(overlay, window_capturer)
        self.selected_points: List[PixelColorPointEntity] = []
        self.control_panel: Optional['PixelColorControlPanel'] = None
        # Track visual elements for easier removal
        self.point_elements: List[PointElement] = []

    def _create_control_panel(self) -> QWidget:
        """Create the control panel for pixel color selection."""
        self.control_panel = PixelColorControlPanel(self)
        return self.control_panel

    def start_selection(self) -> QWidget:
        """Start the pixel color selection process."""
        # Initialize the list of captured points
        self.selected_points = []
        self.point_elements = []
        self.result_data = self.selected_points
        self._connect_signals()
        return super().start_selection()

    def _connect_signals(self) -> None:
        """Connect to overlay signals."""
        self.overlay.mouse_pressed.connect(self._on_mouse_pressed)

    def _disconnect_signals(self) -> None:
        """Disconnect from overlay signals."""
        self.overlay.mouse_pressed.disconnect(self._on_mouse_pressed)

    def _on_mouse_pressed(self, event: QMouseEvent) -> None:
        """Handle mouse press to select pixel color.

        Args:
            event: Mouse press event
        """
        # Only handle left button clicks
        if event.button() != Qt.MouseButton.LeftButton:
            return

        x = int(event.position().x())
        y = int(event.position().y())

        try:
            # Capture window screenshot
            capture_result = self.window_capturer.capture_window()
            if not capture_result:
                logger.error("Failed to capture screen during pixel color selection")
                return

            # Get pixel color from screenshot
            pixel_color = capture_result.to_pil().getpixel((x, y))
            r, g, b = pixel_color

            # Create point and color objects
            point = Point(
                x=x,
                y=y,
                total_width=capture_result.width,
                total_height=capture_result.height
            )
            color = Color(r, g, b)

            # Create pixel color element
            pixel_element = PixelColorPointEntity.from_point_and_color(
                point=point,
                color=color,
            )

            # Add to captured points
            self.selected_points.append(pixel_element)

            # Add visual feedback to overlay
            point_element = PointElement(x, y, QColor(r, g, b))
            self.overlay.add_visual_element(point_element)
            self.point_elements.append(point_element)

            # Update the control panel
            if self.control_panel:
                self.control_panel.update_point_list()

            logger.info(f"Captured pixel at ({x}, {y}) with color RGB({r}, {g}, {b})")

        except Exception as e:
            logger.exception(f"Error capturing pixel color: {e}")

    def remove_point(self, index: int) -> None:
        """Remove a selected point.

        Args:
            index: Index of the point to remove
        """
        if 0 <= index < len(self.selected_points):
            # Remove from the list
            removed_point = self.selected_points.pop(index)
            # Remove the corresponding visual element
            if 0 <= index < len(self.point_elements):
                point_element = self.point_elements.pop(index)
                self.overlay.clear_visual_elements()

            # Update the control panel
            if self.control_panel:
                self.control_panel.update_point_list()

    def can_complete(self) -> bool:
        """Check if selection can be completed."""
        # Require at least one point to complete
        return len(self.selected_points) > 0

    @classmethod
    def create_visual_element(cls, config: Dict[str, Any]) -> VisualElement:
        """Create a visual element from configuration."""
        if config.get("type") != "pixel_color":
            raise ValueError(f"Invalid config type: {config.get('type')}")

        position = config.get("position", {})
        color = config.get("color", {})

        x = position.get("x", 0)
        y = position.get("y", 0)
        r = color.get("r", 0)
        g = color.get("g", 0)
        b = color.get("b", 0)

        return PointElement(x, y, QColor(r, g, b))

    @classmethod
    def get_config_from_element(cls, element: VisualElement) -> Dict[str, Any]:
        """Get configuration from a visual element."""
        if not isinstance(element, PointElement):
            raise ValueError(f"Element is not a PointElement: {type(element).__name__}")

        # Extract color components
        color = element.color
        r, g, b, _ = color.getRgb()

        return {
            "type": "pixel_color",
            "position": {"x": element.x, "y": element.y},
            "color": {"r": r, "g": g, "b": b}
        }

    @classmethod
    def handles_element_type(cls, element: VisualElement) -> bool:
        """Check if this strategy can handle this element type."""
        return isinstance(element, PointElement)


class PixelColorControlPanel(ControlPanel):
    """Control panel for the pixel color selection strategy."""

    def __init__(self, strategy: PixelColorSelector):
        """Initialize the control panel.

        Args:
            strategy: The pixel color selector
        """
        super().__init__(strategy)
        self.strategy = strategy  # For type checking

        # Add instructions
        instructions = QLabel(
            "Click on the overlay to select pixel colors. "
            "You can remove points from the list below."
        )
        instructions.setWordWrap(True)
        self.content_layout.addWidget(instructions)

        # Points list
        self.points_list = QLabel("<i>No points captured yet</i>")
        self.points_list.setWordWrap(True)
        self.content_layout.addWidget(self.points_list)

        # Buttons to remove points
        self.remove_last_button = QPushButton("Remove Last Point")
        self.remove_last_button.clicked.connect(self._remove_last_point)
        self.remove_last_button.setEnabled(False)
        self.content_layout.addWidget(self.remove_last_button)

        # Initial update
        self.update_point_list()

    def update_point_list(self) -> None:
        """Update the list of selected points displayed in the panel."""
        points = self.strategy.selected_points

        if not points:
            self.points_list.setText("<i>No points selected yet</i>")
            self.remove_last_button.setEnabled(False)
            return

        # Build HTML for points list
        html = "<h4>Selected Points:</h4><ol>"

        for point in points:
            # Access point properties safely

            html += f'<li>({point.point_x}, {point.point_y}) - RGB({point.color_r}, {point.color_g}, {point.color_b})</li>'

        html += "</ol>"
        self.points_list.setText(html)
        self.remove_last_button.setEnabled(True)
        self.content_layout.update()

    def _remove_last_point(self) -> None:
        """Remove the last selected point."""
        if self.strategy.selected_points:
            self.strategy.remove_point(len(self.strategy.selected_points) - 1)


class ImageSelector(ElementSelector):
    """Strategy for selecting rectangular image elements.

    This strategy allows users to drag a rectangle on the overlay to select
    a portion of the screen as an image element.
    """

    @classmethod
    def get_strategy_info(cls) -> StrategyInfo:
        """Get strategy information."""
        return StrategyInfo(
            type_id="image_element",
            display_name="Image Element",
            description="Select a rectangular area of the screen as an image element",
            strategy_class=cls
        )

    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the image element capture strategy."""
        super().__init__(overlay, window_capturer)
        self.start_point: Optional[QPoint] = None
        self.current_point: Optional[QPoint] = None
        self.is_dragging = False
        self.rectangle_element: Optional[RectangleElement] = None
        self.selected_image: Optional[QImage] = None
        self.control_panel: Optional['ImageSelectorControlPanel'] = None
        self.selected_rect: Optional[QRect] = None

    def _create_control_panel(self) -> QWidget:
        """Create the control panel for image element capture."""
        self.control_panel = ImageSelectorControlPanel(self)
        return self.control_panel

    def start_selection(self) -> QWidget:
        """Start the image element capture process."""
        # Reset state
        self.start_point = None
        self.current_point = None
        self.is_dragging = False
        self.rectangle_element = None
        self.selected_image = None
        self.selected_rect = None
        self.result_data = None

        # Connect to overlay signals
        self._connect_signals()

        # Call parent method to set up and get control panel
        return super().start_selection()

    def _connect_signals(self) -> None:
        """Connect to overlay signals."""
        self.overlay.mouse_pressed.connect(self._on_mouse_pressed)
        self.overlay.mouse_moved.connect(self._on_mouse_moved)
        self.overlay.mouse_released.connect(self._on_mouse_released)

    def _disconnect_signals(self) -> None:
        """Disconnect from overlay signals."""
        self.overlay.mouse_pressed.disconnect(self._on_mouse_pressed)
        self.overlay.mouse_moved.disconnect(self._on_mouse_moved)
        self.overlay.mouse_released.disconnect(self._on_mouse_released)

    def _on_mouse_pressed(self, event: QMouseEvent) -> None:
        """Handle mouse press to start rectangle selection.

        Args:
            event: Mouse press event
        """
        # Only handle left button clicks
        if event.button() != Qt.MouseButton.LeftButton:
            return

        # Start new selection
        self.start_point = event.position().toPoint()
        self.current_point = self.start_point
        self.is_dragging = True

        # Create or update rectangle element
        self._update_rectangle()

    def _on_mouse_moved(self, event: QMouseEvent) -> None:
        """Handle mouse move during selection.

        Args:
            event: Mouse move event
        """
        if not self.is_dragging:
            return

        self.current_point = event.position().toPoint()
        self._update_rectangle()

    def _on_mouse_released(self, event: QMouseEvent) -> None:
        """Handle mouse release to complete rectangle selection.

        Args:
            event: Mouse release event
        """
        if not self.is_dragging or event.button() != Qt.MouseButton.LeftButton:
            return

        self.is_dragging = False
        self.current_point = event.position().toPoint()

        # Create normalized rectangle
        x1 = min(self.start_point.x(), self.current_point.x())
        y1 = min(self.start_point.y(), self.current_point.y())
        x2 = max(self.start_point.x(), self.current_point.x())
        y2 = max(self.start_point.y(), self.current_point.y())

        width = x2 - x1
        height = y2 - y1

        # Ensure rectangle has minimum size
        if width < 10 or height < 10:
            # Too small, ignore
            if self.rectangle_element:
                try:
                    self.overlay.clear_visual_elements()
                except Exception as e:
                    logger.warning(f"Failed to remove rectangle element: {e}")
                self.rectangle_element = None
            return

        # Save the rect
        self.selected_rect = QRect(x1, y1, width, height)

        # Final update to rectangle
        self._update_rectangle()

        # Capture the image
        self._capture_image()

        # Update UI state
        if self.control_panel:
            self.control_panel.update_image_preview()

    def _update_rectangle(self) -> None:
        """Update or create the rectangle visual element."""
        if not self.start_point or not self.current_point:
            return

        # Calculate rectangle coordinates
        x1 = min(self.start_point.x(), self.current_point.x())
        y1 = min(self.start_point.y(), self.current_point.y())
        x2 = max(self.start_point.x(), self.current_point.x())
        y2 = max(self.start_point.y(), self.current_point.y())

        rect = QRect(x1, y1, x2 - x1, y2 - y1)

        # Create or update rectangle element
        if self.rectangle_element:
            # Remove existing rectangle
            try:
                self.overlay.clear_visual_elements()
            except Exception as e:
                logger.warning(f"Failed to remove rectangle element: {e}")

        # Create new rectangle with semi-transparent fill
        self.rectangle_element = RectangleElement(
            rect,
            color=QColor(0, 120, 215),
            width=2,
            fill_color=QColor(0, 120, 215, 40)
        )

        # Add to overlay
        self.overlay.add_visual_element(self.rectangle_element)

    def _capture_image(self) -> None:
        """Capture the image within the selected rectangle."""
        if not self.selected_rect:
            return

        # Capture screen
        screen_image = self.window_capturer.capture_window()
        if not screen_image:
            logger.error("Failed to capture screen for image element")
            return

        # Crop to selection
        self.selected_image = screen_image.to_pil().crop(
            (
                float(self.selected_rect.x()),
                float(self.selected_rect.y()),
                float(self.selected_rect.x() + self.selected_rect.width()),
                float(self.selected_rect.y() + self.selected_rect.height())
            )
        )

        # Create result data
        self.result_data = {
            "rect": {
                "x": self.selected_rect.x(),
                "y": self.selected_rect.y(),
                "width": self.selected_rect.width(),
                "height": self.selected_rect.height()
            },
            "image": self.selected_image
        }

        # Update the preview in the control panel
        if self.control_panel:
            self.control_panel.update_image_preview()

    def reset_selection(self) -> None:
        """Reset the selection and start over."""
        # Clear current selection
        if self.rectangle_element:
            try:
                self.overlay.clear_visual_elements()
            except Exception as e:
                logger.warning(f"Failed to remove rectangle element: {e}")
            self.rectangle_element = None

        # Reset state
        self.start_point = None
        self.current_point = None
        self.is_dragging = False
        self.selected_image = None
        self.selected_rect = None
        self.result_data = None

        # Update UI
        if self.control_panel:
            self.control_panel.update_image_preview()

    def can_complete(self) -> bool:
        """Check if selection can be completed."""
        return self.selected_image is not None

    @classmethod
    def create_visual_element(cls, config: Dict[str, Any]) -> VisualElement:
        """Create a visual element from configuration."""
        if config.get("type") != "image_element":
            raise ValueError(f"Invalid config type: {config.get('type')}")

        rect_config = config.get("rect", {})

        x = rect_config.get("x", 0)
        y = rect_config.get("y", 0)
        width = rect_config.get("width", 10)
        height = rect_config.get("height", 10)

        return RectangleElement(
            QRect(x, y, width, height),
            color=QColor(0, 120, 215),
            width=2,
            fill_color=QColor(0, 120, 215, 40)
        )

    @classmethod
    def get_config_from_element(cls, element: VisualElement) -> Dict[str, Any]:
        """Get configuration from a visual element."""
        if not isinstance(element, RectangleElement):
            raise ValueError(f"Element is not a RectangleElement: {type(element).__name__}")

        rect = element.rect

        return {
            "type": "image_element",
            "rect": {
                "x": rect.x(),
                "y": rect.y(),
                "width": rect.width(),
                "height": rect.height()
            }
        }

    @classmethod
    def handles_element_type(cls, element: VisualElement) -> bool:
        """Check if this strategy can handle this element type."""
        return isinstance(element, RectangleElement)


class ImageSelectorControlPanel(ControlPanel):
    """Control panel for the image element capture strategy."""

    def __init__(self, strategy: ImageSelector):
        """Initialize the control panel.

        Args:
            strategy: The image element selector
        """
        super().__init__(strategy)
        self.strategy = strategy  # For type checking

        # Add instructions
        instructions = QLabel(
            "Draw a rectangle on the overlay by clicking and dragging. "
            "Release to select the image."
        )
        instructions.setWordWrap(True)
        self.content_layout.addWidget(instructions)

        # Image preview label
        self.preview_label = QLabel("No image selected yet")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(150)
        self.content_layout.addWidget(self.preview_label)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.strategy.reset_selection)
        self.reset_button.setEnabled(False)
        self.content_layout.addWidget(self.reset_button)

        # Initial update
        self.update_image_preview()

    def update_image_preview(self) -> None:
        """Update the image preview with the selected image."""
        if not self.strategy.selected_image:
            self.preview_label.setText("No image selected yet")
            return

        # Create pixmap from image
        pixmap = QPixmap.fromImage(self.strategy.selected_image)

        # Scale for preview if needed
        if pixmap.width() > 300:
            pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)

        # Set the pixmap
        self.preview_label.setPixmap(pixmap)
