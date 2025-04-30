"""
Capture strategies for different element types.

This module provides strategies for capturing different types of elements
using the overlay system. Each strategy defines the interaction flow for
a specific type of element capture.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from PySide6.QtCore import QObject, QPoint, QRect, Signal
from PySide6.QtGui import QColor, QMouseEvent

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from domain.color import Color
from domain.pixel_element import PixelColorElementEntity
from domain.regions import Point, Region
from picker.overlay.overlay_widget import OverlayWidget
from picker.overlay.visual_elements import (PointElement, RectangleElement,
                                            TextElement)

logger = get_logger(__name__)


# Fix for metaclass conflict
class ABCQObjectMeta(type(QObject), type(ABC)):
    """Metaclass that resolves conflict between QObject and ABC metaclasses."""
    pass


class CaptureStrategy(QObject, ABC, metaclass=ABCQObjectMeta):
    """Base abstract class for all element capture strategies."""

    # Signals
    capture_started = Signal()
    capture_step_completed = Signal(int, object)  # Step index and step data
    capture_completed = Signal(object)  # Final result
    capture_cancelled = Signal()

    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the capture strategy.

        Args:
            overlay: The overlay widget used for capturing
            window_capturer: The window capturer for screenshots
        """
        super().__init__()
        self.overlay = overlay
        self.window_capturer = window_capturer
        self.current_step = 0
        self.result_data: Any = None

    @abstractmethod
    def start_capture(self) -> None:
        """Start the element capture process."""
        self.current_step = 0
        self.result_data = None
        self._connect_signals()
        self._initialize_visuals()
        self.capture_started.emit()

    def _connect_signals(self) -> None:
        """Connect to overlay signals."""
        self.overlay.mouse_pressed.connect(self.handle_press)
        self.overlay.mouse_moved.connect(self.handle_move)
        self.overlay.mouse_released.connect(self.handle_release)
        self.overlay.mouse_dragged.connect(self.handle_drag)

    def _disconnect_signals(self) -> None:
        """Disconnect from overlay signals."""
        self.overlay.mouse_pressed.disconnect(self.handle_press)
        self.overlay.mouse_moved.disconnect(self.handle_move)
        self.overlay.mouse_released.disconnect(self.handle_release)
        self.overlay.mouse_dragged.disconnect(self.handle_drag)

    @abstractmethod
    def _initialize_visuals(self) -> None:
        """Initialize visual elements for the current step."""
        self.overlay.clear_visual_elements()

        # Add instructions based on current step
        instructions = self.get_instructions()
        self.overlay.add_visual_element(TextElement(instructions, 10, 10))

    @abstractmethod
    def handle_press(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse press event
        """
        pass

    @abstractmethod
    def handle_move(self, event: QMouseEvent) -> None:
        """Handle mouse move events.

        Args:
            event: The mouse move event
        """
        pass

    @abstractmethod
    def handle_release(self, event: QMouseEvent) -> None:
        """Handle mouse release events.

        Args:
            event: The mouse release event
        """
        pass

    @abstractmethod
    def handle_drag(self, start_point: QPoint, current_point: QPoint) -> None:
        """Handle mouse drag events.

        Args:
            start_point: Drag start point
            current_point: Current drag point
        """
        pass

    @abstractmethod
    def get_instructions(self) -> str:
        """Get instructions for the current step.

        Returns:
            Instructions as a string
        """
        pass

    def cancel_capture(self) -> None:
        """Cancel the current capture process."""
        self._disconnect_signals()
        self.capture_cancelled.emit()

    def complete_capture(self) -> None:
        """Complete the capture process and emit result."""
        self._disconnect_signals()
        self.capture_completed.emit(self.result_data)


class PixelColorCaptureStrategy(CaptureStrategy):
    """Strategy for capturing pixel color elements."""

    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the pixel color capture strategy.

        Args:
            overlay: The overlay widget used for capturing
            window_capturer: The window capturer for screenshots
        """
        super().__init__(overlay, window_capturer)
        self.captured_points: List[PixelColorElementEntity] = []

    def start_capture(self) -> None:
        """Start the pixel color capture process."""
        self.captured_points = []
        super().start_capture()

    def _initialize_visuals(self) -> None:
        """Initialize visual elements for pixel color capture."""
        super()._initialize_visuals()

    def handle_press(self, event: QMouseEvent) -> None:
        """Handle pixel color capture on mouse press.

        Args:
            event: The mouse press event
        """
        x = int(event.position().x())
        y = int(event.position().y())

        try:
            # Capture window screenshot
            capture_result = self.window_capturer.capture_window()
            if not capture_result:
                logger.error("Failed to capture window during pixel color capture")
                return

            # Get pixel color from screenshot
            pil_image = capture_result.to_pil()
            pixel_color = pil_image.getpixel((x, y))

            # Process color (handle both RGB and RGBA)
            if len(pixel_color) == 4:  # RGBA
                r, g, b, _ = pixel_color
            else:  # RGB
                r, g, b = pixel_color

            # Create point and color objects
            point = Point(
                x=x,
                y=y,
                total_width=pil_image.width,
                total_height=pil_image.height
            )
            color = Color(r, g, b)

            # Create pixel color element
            pixel_element = PixelColorElementEntity.from_point_color(
                point=point,
                color=color,
            )

            # Add to captured points
            self.captured_points.append(pixel_element)

            # Update result data
            self.result_data = self.captured_points

            # Add visual feedback
            self.overlay.add_visual_element(
                PointElement(x, y, color.to_q_color())
            )

            # Signal step completion
            self.capture_step_completed.emit(
                len(self.captured_points),
                pixel_element
            )

            logger.info(f"Captured pixel at ({x}, {y}) with color RGB({r}, {g}, {b})")

        except Exception as e:
            logger.exception(f"Error capturing pixel color: {e}")

    def handle_move(self, event: QMouseEvent) -> None:
        """Handle mouse move events.

        Args:
            event: The mouse move event
        """
        # Mouse move handling for pixel capture
        # Could implement hover effects or color preview
        pass

    def handle_release(self, event: QMouseEvent) -> None:
        """Handle mouse release events.

        Args:
            event: The mouse release event
        """
        # Pixel capture doesn't require special release handling
        pass

    def handle_drag(self, start_point: QPoint, current_point: QPoint) -> None:
        """Handle mouse drag events.

        Args:
            start_point: Drag start point
            current_point: Current drag point
        """
        # Pixel capture doesn't use dragging
        pass

    def get_instructions(self) -> str:
        """Get instructions for pixel color capture.

        Returns:
            Instructions as a string
        """
        if not self.captured_points:
            return "Click on points to capture pixel colors"
        else:
            count = len(self.captured_points)
            return f"Captured {count} point(s). Click more points or finish capture."


class ImageElementCaptureStrategy(CaptureStrategy):
    """Strategy for capturing image elements with template and detection regions."""

    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the image element capture strategy.

        Args:
            overlay: The overlay widget used for capturing
            window_capturer: The window capturer for screenshots
        """
        super().__init__(overlay, window_capturer)
        self.template_region: Optional[QRect] = None
        self.detection_region: Optional[QRect] = None
        self.current_selection: Optional[QRect] = None
        self.capture_image = None

    def start_capture(self) -> None:
        """Start the image element capture process."""
        self.template_region = None
        self.detection_region = None
        self.current_selection = None

        # Capture initial screenshot
        try:
            capture_result = self.window_capturer.capture_window()
            if capture_result:
                self.capture_image = capture_result.to_pil()
            else:
                logger.error("Failed to capture initial screenshot for image element")
        except Exception as e:
            logger.exception(f"Error during initial screenshot capture: {e}")

        super().start_capture()

    def _initialize_visuals(self) -> None:
        """Initialize visual elements for image element capture."""
        super()._initialize_visuals()

        # Show already captured regions if any
        if self.template_region:
            self.overlay.add_visual_element(
                RectangleElement(
                    self.template_region,
                    QColor(0, 255, 0)  # Green for template
                )
            )

    def handle_press(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event: The mouse press event
        """
        # Start of region selection handled by drag logic
        pass

    def handle_move(self, event: QMouseEvent) -> None:
        """Handle mouse move events.

        Args:
            event: The mouse move event
        """
        # Mouse move could show coordinates or other info
        pass

    def handle_drag(self, start_point: QPoint, current_point: QPoint) -> None:
        """Handle region selection dragging.

        Args:
            start_point: Drag start point
            current_point: Current drag point
        """
        # Create selection rectangle
        selection = QRect(start_point, current_point).normalized()
        self.current_selection = selection

        # Update visual feedback
        self.overlay.clear_visual_elements()
        self._initialize_visuals()

        # Add current selection rectangle
        self.overlay.add_visual_element(
            RectangleElement(
                selection,
                QColor(255, 0, 0) if self.current_step == 1 else QColor(0, 255, 0),
                1,
                QColor(128, 128, 128, 40)  # Semi-transparent fill
            )
        )

    def handle_release(self, event: QMouseEvent) -> None:
        """Complete region selection on mouse release.

        Args:
            event: The mouse release event
        """
        if not self.current_selection:
            return

        # Ignore too small selections
        if (self.current_selection.width() < 10 or
                self.current_selection.height() < 10):
            logger.info("Selection too small, ignoring")
            return

        if self.current_step == 0:
            # Completed template region selection
            self.template_region = self.current_selection
            self.current_step = 1

            # Update visuals
            self.overlay.clear_visual_elements()
            self._initialize_visuals()

            # Signal step completion
            self.capture_step_completed.emit(0, self.template_region)

            logger.info(f"Template region selected: {self.template_region}")

        elif self.current_step == 1:
            # Completed detection region selection
            self.detection_region = self.current_selection

            # Prepare result data
            if self.capture_image and self.template_region and self.detection_region:
                # Convert QRect to Region objects
                template_region = Region(
                    name="Template",
                    start_x=self.template_region.x(),
                    start_y=self.template_region.y(),
                    width=self.template_region.width(),
                    height=self.template_region.height(),
                    total_width=self.capture_image.width,
                    total_height=self.capture_image.height
                )

                detection_region = Region(
                    name="Detection",
                    start_x=self.detection_region.x(),
                    start_y=self.detection_region.y(),
                    width=self.detection_region.width(),
                    height=self.detection_region.height(),
                    total_width=self.capture_image.width,
                    total_height=self.capture_image.height
                )

                # Extract template image
                template_image = self.capture_image.crop((
                    template_region.start_x,
                    template_region.start_y,
                    template_region.start_x + template_region.width,
                    template_region.start_y + template_region.height
                ))

                # Set result data
                self.result_data = (template_image, template_region, detection_region)

                logger.info(f"Detection region selected: {self.detection_region}")

                # Complete capture
                self.complete_capture()

    def get_instructions(self) -> str:
        """Get instructions for the current capture step.

        Returns:
            Instructions as a string
        """
        if self.current_step == 0:
            return "Select template region by dragging"
        else:
            return "Now select detection region (larger area containing the template)"
