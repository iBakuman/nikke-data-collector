import io
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

import win32gui
from PIL import ImageDraw
from PySide6.QtCore import QObject, QPoint, QRect, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import (QComboBox, QFrame, QInputDialog, QLabel,
                               QMessageBox, QPushButton, QToolBar, QVBoxLayout,
                               QWidget)
from dataclass_wizard.serial_json import JSONPyWizard, JSONWizard

from collector.logging_config import get_logger
from collector.ui_def import STANDARD_WINDOW_HEIGHT, STANDARD_WINDOW_WIDTH
from collector.window_capturer import WindowCapturer
from collector.window_manager import WindowManager, get_window_rect
from domain.image_element import ImageElementEntity
from mixin.json import JSONSerializableMixin

logger = get_logger(__name__)

NIKKE_PROCESS_NAME = "nikke.exe"  # Adjust if your process name is different
OUTPUT_DIR = "output"
SCREENSHOT_FILENAME = os.path.join(OUTPUT_DIR, "screenshot.png")
CLICKS_FILENAME = os.path.join(OUTPUT_DIR, "clicks.json")
IMAGE_ELEMENTS_DIR = os.path.join(OUTPUT_DIR, "image_elements")


class SelectionMode(Enum):
    POINT = "Point Selection"
    REGION = "Region Selection"


class CoordinateTooltip(QFrame):
    """Tooltip that shows coordinates, color, and a magnified view of pixels around cursor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Style the tooltip
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border-radius: 4px;
                padding: 2px;
            }
            QLabel {
                color: white;
                font-size: 10px;
                padding: 0px;
            }
        """)

        # Create layout and labels
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)

        # Pixel magnifier area (will be drawn in paintEvent)
        self.magnifier_widget = QWidget()
        self.magnifier_widget.setFixedSize(150, 100)

        # Info labels
        self.pos_label = QLabel("X: 0, Y: 0")
        self.color_label = QLabel("RGB: 0, 0, 0")

        self.layout.addWidget(self.magnifier_widget)
        self.layout.addWidget(self.pos_label)
        self.layout.addWidget(self.color_label)

        # Magnification settings
        self.magnification = 5  # Each pixel becomes 5x5
        self.area_size = 20     # Extract 20x20 pixels around cursor

        # Pixel data
        self.pixel_data = None
        self.cursor_pos = (0, 0)
        self.pixel_color = (0, 0, 0)

        # Size of the tooltip
        self.setFixedSize(170, 140)
        self.hide()

    def update_info(self, x: int, y: int, color: Tuple[int, int, int], pixels=None):
        """Update tooltip with new coordinates, color and pixel data."""
        self.cursor_pos = (x, y)
        self.pixel_color = color
        self.pixel_data = pixels

        self.pos_label.setText(f"X: {x}, Y: {y}")
        self.color_label.setText(f"RGB: {color[0]}, {color[1]}, {color[2]}")

        # Update the magnifier widget
        self.magnifier_widget.update()

    def paintEvent(self, event):
        """Draw the tooltip background and border."""
        super().paintEvent(event)

        # Draw magnified pixels if available
        if self.pixel_data is not None:
            painter = QPainter(self)

            # Get drawing area
            area_rect = self.magnifier_widget.geometry()

            # Draw the background for the magnifier area
            painter.fillRect(area_rect, QColor(30, 30, 30))

            # Calculate pixel size and center position
            pixel_size = self.magnification
            center_x = area_rect.width() // 2
            center_y = area_rect.height() // 2

            # Draw the magnified pixels
            for y, row in enumerate(self.pixel_data):
                for x, color in enumerate(row):
                    # Convert to QColor
                    qcolor = QColor(*color)

                    # Calculate position (centered on cursor)
                    px = area_rect.x() + center_x + (x - self.area_size//2) * pixel_size
                    py = area_rect.y() + center_y + (y - self.area_size//2) * pixel_size

                    # Draw the magnified pixel
                    painter.fillRect(px, py, pixel_size, pixel_size, qcolor)

            # Draw crosshair lines
            painter.setPen(QPen(QColor(255, 255, 0), 1, Qt.PenStyle.DashLine))

            # Horizontal line at cursor position
            painter.drawLine(
                area_rect.x(), area_rect.y() + center_y,
                area_rect.x() + area_rect.width(), area_rect.y() + center_y
            )

            # Vertical line at cursor position
            painter.drawLine(
                area_rect.x() + center_x, area_rect.y(),
                area_rect.x() + center_x, area_rect.y() + area_rect.height()
            )

            # Draw border around magnifier area
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawRect(area_rect)


class OverlayWidget(QWidget):
    """Transparent overlay to capture clicks and display points."""
    clicked = Signal(QMouseEvent)
    points_updated = Signal(list)  # Signal to notify when points change
    region_selected = Signal(QRect, QRect)  # Signal for region selection (template, detection_region)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool |
                            Qt.WindowType.BypassWindowManagerHint)  # Add bypass hint
        self.setMouseTracking(True)  # Enable mouse tracking
        self._points: List[Tuple[int, int, Tuple[int, int, int]]] = []  # Store as (x, y, (r, g, b))

        # Region selection variables
        self.selection_mode = SelectionMode.POINT
        self.is_selecting = False
        self.selection_start = QPoint()
        self.current_selection = QRect()
        self.template_region = None  # First selection (image template)
        self.region_selection_step = 0  # 0: no selection, 1: template selected, 2: both regions selected

        # Create coordinate tooltip
        self.coord_tooltip = CoordinateTooltip()

        # Store the last captured screenshot for color sampling
        self.current_screenshot = None

        # Window capturer reference (will be set from PickerApp)
        self.window_capturer = None

    def set_window_capturer(self, capturer):
        """Set the window capturer for color sampling."""
        self.window_capturer = capturer
        # Capture initial screenshot
        self.update_screenshot()

    def update_screenshot(self):
        """Update the current screenshot for color sampling."""
        if self.window_capturer:
            capture_result = self.window_capturer.capture_window()
            if capture_result:
                self.current_screenshot = capture_result.to_pil()
                return True
        return False

    def set_selection_mode(self, mode: SelectionMode):
        """Change the selection mode."""
        self.selection_mode = mode
        self.region_selection_step = 0
        self.template_region = None
        self.current_selection = QRect()
        self.update()

        # Update screenshot when changing to region mode
        if mode == SelectionMode.REGION:
            self.update_screenshot()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events based on selection mode."""
        if self.selection_mode == SelectionMode.POINT:
            logger.info(f"OverlayWidget received point selection at {event.position()}")
            self.clicked.emit(event)
        else:  # Region mode
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_selecting = True
                self.selection_start = event.position().toPoint()
                self.current_selection = QRect()
                self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Update selection rectangle during mouse movement."""
        current_pos = event.position().toPoint()

        if self.selection_mode == SelectionMode.REGION:
            # Update tooltip with position and color info
            if self.current_screenshot:
                x, y = current_pos.x(), current_pos.y()

                # Only sample colors if coordinates are in bounds
                if (0 <= x < self.current_screenshot.width and
                    0 <= y < self.current_screenshot.height):
                    try:
                        # Get the central pixel color
                        r, g, b = self.current_screenshot.getpixel((x, y))

                        # Extract a region of pixels around the cursor
                        area_size = 20  # 20x20 pixel area
                        half_size = area_size // 2

                        # Calculate boundaries to prevent sampling outside the image
                        start_x = max(0, x - half_size)
                        start_y = max(0, y - half_size)
                        end_x = min(self.current_screenshot.width, x + half_size + 1)
                        end_y = min(self.current_screenshot.height, y + half_size + 1)

                        # Extract pixel data
                        pixel_array = []
                        for py in range(start_y, end_y):
                            row = []
                            for px in range(start_x, end_x):
                                row.append(self.current_screenshot.getpixel((px, py)))
                            pixel_array.append(row)

                        # Update tooltip with all information
                        self.coord_tooltip.update_info(x, y, (r, g, b), pixel_array)

                        # Position tooltip below and to the right of cursor
                        tooltip_pos = self.mapToGlobal(current_pos + QPoint(15, 15))
                        self.coord_tooltip.move(tooltip_pos)
                        self.coord_tooltip.show()
                    except Exception as e:
                        # Handle any issues accessing pixel data
                        logger.warning(f"Error sampling pixel: {e}")
                        self.coord_tooltip.hide()
                else:
                    self.coord_tooltip.hide()

            # Update selection rectangle during dragging
            if self.is_selecting:
                self.current_selection = QRect(
                    self.selection_start,
                    current_pos
                ).normalized()  # Normalized ensures width/height are positive
                self.update()
        else:
            # Hide tooltip in point mode
            self.coord_tooltip.hide()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Hide tooltip when mouse leaves overlay."""
        self.coord_tooltip.hide()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Finalize selection on mouse release."""
        if self.selection_mode == SelectionMode.REGION and self.is_selecting:
            self.is_selecting = False
            current_pos = event.position().toPoint()
            final_selection = QRect(
                self.selection_start,
                current_pos
            ).normalized()

            # Ignore very small selections (might be accidental clicks)
            if final_selection.width() < 10 or final_selection.height() < 10:
                logger.info("Selection too small, ignoring")
                return

            # First selection: template region
            if self.region_selection_step == 0:
                self.template_region = final_selection
                self.region_selection_step = 1
                logger.info(f"Template region selected: {final_selection}")
                # Prompt user for next step
                QMessageBox.information(self, "Template Selected",
                                      "Template image area selected. Now select the detection region (the larger area where this template should be found).")

            # Second selection: detection region
            elif self.region_selection_step == 1:
                logger.info(f"Detection region selected: {final_selection}")
                # Emit signal with both regions
                self.region_selected.emit(self.template_region, final_selection)
                self.region_selection_step = 0
                self.template_region = None

            self.current_selection = QRect()
            self.update()
        super().mouseReleaseEvent(event)

        # Hide tooltip on mouse release
        self.coord_tooltip.hide()

    def set_points(self, points: List[Tuple[int, int, Tuple[int, int, int]]]):
        """Update the points to be drawn."""
        self._points = points
        self.points_updated.emit(self._points)  # Emit signal
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw captured points or selection regions on the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Do NOT fill background to keep it completely transparent
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        # Draw based on mode
        if self.selection_mode == SelectionMode.POINT:
            # Draw circles at clicked points
            for x, y, (r, g, b) in self._points:
                # Draw outer circle (e.g., white)
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPoint(x, y), 5, 5)

                # Draw inner circle with the captured color
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(r, g, b))
                painter.drawEllipse(QPoint(x, y), 3, 3)
        else:  # Region mode
            # Draw template region if it exists
            if self.template_region and self.template_region.isValid():
                painter.setPen(QPen(QColor(0, 255, 0), 2))  # Green for template
                painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill
                painter.drawRect(self.template_region)

            # Draw current selection rectangle
            if self.is_selecting and self.current_selection.isValid():
                painter.setPen(QPen(QColor(255, 0, 0), 2))  # Red for current selection
                painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill
                painter.drawRect(self.current_selection)


@dataclass
class Coordinate(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    x: float
    y: float
    color: Tuple[int, int, int]

    def to_tuple(self) -> Tuple[int, int, Tuple[int, int, int]]:
        return int(self.x), int(self.y), self.color


@dataclass
class Coordinates(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    coordinates: List[Coordinate] = field(default_factory=list)

    def add(self, coordinate: Coordinate):
        self.coordinates.append(coordinate)

    def to_list(self) -> List[Tuple[int, int, Tuple[int, int, int]]]:
        return [coordinate.to_tuple() for coordinate in self.coordinates]

    def __len__(self) -> int:
        return len(self.coordinates)


# noinspection PyBroadException
class PickerApp(QObject):
    def __init__(self):
        super().__init__()
        self.nikke_hwnd: Optional[int] = None
        self.overlay: Optional[OverlayWidget] = None
        self.toolbar: Optional[QToolBar] = None
        self.collected_points: Coordinates = Coordinates()
        self.status_label: Optional[QLabel] = None
        self.mode_selector: Optional[QComboBox] = None
        self.selection_mode = SelectionMode.POINT
        self.window_check_timer = None
        self.wm: Optional[WindowManager] = None
        self._initialize_window_manager()
        self.wc = WindowCapturer(self.wm)
        self.init_ui()
        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.update_overlay_position)
        self.timer.start()

        # Ensure output directories exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(IMAGE_ELEMENTS_DIR, exist_ok=True)

    def _initialize_window_manager(self):
        """Initialize the WindowManager and find the target window."""
        logger.info(f"Attempting to find window for process: {NIKKE_PROCESS_NAME}")
        # Use provided standard dimensions or fallback
        self.wm = WindowManager(
            NIKKE_PROCESS_NAME,
            standard_width=STANDARD_WINDOW_WIDTH,
            standard_height=STANDARD_WINDOW_HEIGHT,
            exact_match=True
        )
        self.nikke_hwnd = self.wm.get_hwnd()
        logger.info(f"Found Nikke window. HWND: {self.nikke_hwnd}")

    def update_overlay_position(self):
        """Check if the Nikke window moved/resized and update the overlay."""
        if not self.wm or not self.nikke_hwnd or not self.overlay:
            return

        try:
            if not win32gui.IsWindow(self.nikke_hwnd):
                logger.warning("Nikke window handle is no longer valid. Stopping timer.")
                self.toolbar.killTimer(self.window_check_timer)
                QMessageBox.warning(self.toolbar, "Window Closed", "The Nikke window appears to have been closed.")
                self.overlay.close()  # Optionally close the picker
                return

            current_rect = get_window_rect(self.nikke_hwnd)
            if not current_rect:
                logger.warning("Could not get current Nikke window rect.")
                return

            current_pos = QPoint(current_rect.left, current_rect.top)
            current_size = (current_rect.width, current_rect.height)

            overlay_pos = self.overlay.pos()
            overlay_size = (self.overlay.width(), self.overlay.height())

            if current_pos != overlay_pos or current_size != overlay_size:
                logger.info(f"Nikke window changed. Updating overlay geometry to {current_rect}")
                self.overlay.setGeometry(current_rect.left, current_rect.top, current_rect.width, current_rect.height)
                self.toolbar.setGeometry(current_rect.left, current_rect.top + current_rect.height + 20, current_rect.width, 20)
        except Exception:
            logger.exception("Error checking/updating window position:")

    def init_ui(self):
        """Initialize the main application UI."""
        logger.info("--- Initializing UI ---")  # DEBUG
        if not self.wm or not self.nikke_hwnd:
            logger.error("Cannot initialize UI without WindowManager.")
            return
        self.init_overlay()
        self.init_toolbar()

    def init_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # Add mode selector dropdown
        self.mode_selector = QComboBox()
        self.mode_selector.addItem(SelectionMode.POINT.value)
        self.mode_selector.addItem(SelectionMode.REGION.value)
        self.mode_selector.currentTextChanged.connect(self.change_selection_mode)
        self.toolbar.addWidget(QLabel("Mode: "))
        self.toolbar.addWidget(self.mode_selector)

        # Status label
        self.status_label = QLabel("Click on the game window overlay to capture points.")
        self.toolbar.addWidget(self.status_label)

        # Buttons
        save_button = QPushButton("Save Data")
        save_button.clicked.connect(self.save_data)
        self.toolbar.addWidget(save_button)

        clear_button = QPushButton("Clear Points")
        clear_button.clicked.connect(self.clear_points)
        self.toolbar.addWidget(clear_button)

        self.toolbar.setGeometry(self.wm.start_x, self.wm.start_y + self.wm.height + 20, self.wm.width, 40)  # Taller toolbar
        self.toolbar.show()

    def init_overlay(self):
        self.overlay = OverlayWidget()
        self.overlay.clicked.connect(self.handle_overlay_click)
        self.overlay.points_updated.connect(self.update_status_label)
        self.overlay.region_selected.connect(self.handle_region_selection)
        self.overlay.setGeometry(self.wm.start_x, self.wm.start_y, self.wm.width, self.wm.height)
        # Set the window capturer for color sampling
        self.overlay.set_window_capturer(self.wc)
        logger.info("--- Overlay window.show() called ---")
        self.overlay.show()

    @Slot(str)
    def change_selection_mode(self, mode_text: str):
        """Handle selection mode change."""
        try:
            self.selection_mode = SelectionMode(mode_text)
            self.overlay.set_selection_mode(self.selection_mode)

            if self.selection_mode == SelectionMode.POINT:
                self.status_label.setText("Click on the game window overlay to capture points.")
            else:
                # Update screenshot when switching to region mode
                self.overlay.update_screenshot()
                self.status_label.setText("First select the template image area, then select the detection region.")

            logger.info(f"Selection mode changed to: {self.selection_mode}")
        except ValueError:
            logger.error(f"Invalid selection mode: {mode_text}")

    @Slot(QMouseEvent)
    def handle_overlay_click(self, event: QMouseEvent):
        """Handle clicks on the overlay."""
        logger.info("--- handle_overlay_click called --- ")
        if not self.nikke_hwnd:
            logger.warning("Nikke HWND not available, cannot process click.")
            return

        # Get click position relative to the overlay
        click_pos_overlay = event.position()
        logger.debug(f"Overlay clicked at: {click_pos_overlay}")

        # Convert overlay coordinates to window coordinates
        x = int(click_pos_overlay.x())
        y = int(click_pos_overlay.y())

        try:
            # Use WindowCapturer to capture the window directly
            # This bypasses Qt's screenshot mechanism which might capture the overlay
            capture_result = self.wc.capture_window()

            if not capture_result:
                logger.error("Failed to capture window content.")
                return
            # Get pixel color from the captured image
            # The capture result coordinates are relative to the window
            pil_image = capture_result.to_pil()
            r, g, b = pil_image.getpixel((x, y))

            # Store the captured point
            self.collected_points.add(Coordinate(x=x, y=y, color=(r, g, b)))
            logger.info(f"Point captured: ({x}, {y}) -> RGB({r}, {g}, {b})")
            # Update the overlay to draw the new point
            self.overlay.set_points(self.collected_points.to_list())

        except Exception as e:
            logger.exception(f"Error capturing pixel color: {e}")

    @Slot(QRect, QRect)
    def handle_region_selection(self, template_region: QRect, detection_region: QRect):
        """Handle region selection for ImageElement creation."""
        logger.info(f"Region selection complete - Template: {template_region}, Detection: {detection_region}")

        try:
            # Capture the current screen
            capture_result = self.wc.capture_window()
            if not capture_result:
                logger.error("Failed to capture window for region selection.")
                QMessageBox.critical(self.toolbar, "Capture Failed", "Failed to capture window content.")
                return

            pil_image = capture_result.to_pil()

            # Adjust regions to exclude borders (borders are 2px wide, so adjust by 1px on each side)
            # For template region
            template_x = template_region.x() + 1
            template_y = template_region.y() + 1
            template_w = template_region.width() - 2
            template_h = template_region.height() - 2

            # For detection region
            detection_x = detection_region.x() + 1
            detection_y = detection_region.y() + 1
            detection_w = detection_region.width() - 2
            detection_h = detection_region.height() - 2

            # Extract the template image (excluding border)
            template_image = pil_image.crop((template_x, template_y,
                                           template_x + template_w,
                                           template_y + template_h))

            # Get name for the image element
            element_name, ok = QInputDialog.getText(
                self.toolbar, "Image Element Name",
                "Enter a name for this image element:",
                text="element_" + datetime.now().strftime("%Y%m%d%H%M%S")
            )

            if not ok or not element_name:
                logger.info("User cancelled image element creation")
                return

            # Create ImageElementEntity with adjusted coordinates (excluding border)
            image_element = ImageElementEntity(
                name=element_name,
                region_x=detection_x,
                region_y=detection_y,
                region_width=detection_w,
                region_height=detection_h,
                region_total_width=pil_image.width,
                region_total_height=pil_image.height,
                threshold=0.8  # Default threshold
            )

            # Convert template image to bytes for storage
            img_byte_arr = io.BytesIO()
            template_image.save(img_byte_arr, format='PNG')
            image_element.image_data = img_byte_arr.getvalue()

            # Save template image to file for preview
            template_path = os.path.join(IMAGE_ELEMENTS_DIR, f"{element_name}_template.png")
            template_image.save(template_path)

            # Save element to JSON
            element_path = os.path.join(IMAGE_ELEMENTS_DIR, f"{element_name}.json")
            image_element.save_as_json(element_path)

            # Draw visualization of detection region on full screenshot
            screenshot_with_regions = pil_image.copy()
            draw = ImageDraw.Draw(screenshot_with_regions)

            # Draw detection region (red) - using original regions for visualization
            draw.rectangle(
                (detection_region.x(), detection_region.y(),
                detection_region.x() + detection_region.width(),
                detection_region.y() + detection_region.height()),
                outline=(255, 0, 0), width=2, fill=None
            )

            # Draw template region (green) - using original regions for visualization
            draw.rectangle(
                (template_region.x(), template_region.y(),
                template_region.x() + template_region.width(),
                template_region.y() + template_region.height()),
                outline=(0, 255, 0), width=2, fill=None
            )

            # Draw actual crop regions (blue for template, yellow for detection) to show what was actually captured
            # Template actual region
            draw.rectangle(
                (template_x, template_y,
                template_x + template_w,
                template_y + template_h),
                outline=(0, 0, 255), width=1, fill=None
            )

            # Detection actual region
            draw.rectangle(
                (detection_x, detection_y,
                detection_x + detection_w,
                detection_y + detection_h),
                outline=(255, 255, 0), width=1, fill=None
            )

            # Save visualization
            screenshot_path = os.path.join(IMAGE_ELEMENTS_DIR, f"{element_name}_regions.png")
            screenshot_with_regions.save(screenshot_path)

            QMessageBox.information(
                self.toolbar, "Image Element Created",
                f"Created image element '{element_name}'.\nFiles saved to {IMAGE_ELEMENTS_DIR}"
            )

            logger.info(f"Image element '{element_name}' created and saved successfully")

        except Exception as e:
            logger.exception(f"Error processing region selection: {e}")
            QMessageBox.critical(
                self.toolbar, "Error",
                f"Failed to create image element: {str(e)}"
            )

    @Slot(list)
    def update_status_label(self, points):
        """Update the status label with the number of points."""
        if self.selection_mode == SelectionMode.POINT:
            self.status_label.setText(f"Captured {len(points)} points. Click 'Save Data' to save.")

    @Slot()
    def clear_points(self):
        """Clear all collected points."""
        logger.info("Clearing all collected points.")
        self.collected_points = Coordinates()
        if self.overlay:
            self.overlay.set_points(self.collected_points.to_list())

    @Slot()
    def save_data(self):
        """Save collected points to JSON and capture a screenshot."""
        if self.selection_mode == SelectionMode.POINT:
            self._save_point_data()
        else:
            QMessageBox.information(
                self.toolbar, "Region Mode",
                "In Region Mode, image elements are saved automatically after selection."
            )

    def _save_point_data(self):
        """Save collected point data."""
        if not self.collected_points or len(self.collected_points) == 0:
            logger.warning("No points collected to save.")
            QMessageBox.information(self.toolbar, "No Data", "No points have been captured yet.")
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # 1. Save screenshot
        screenshot_saved = False
        logger.info(f"Capturing screenshot of Nikke window to {SCREENSHOT_FILENAME}...")
        capture_result = self.wc.capture_window()
        if capture_result:
            capture_result.save(SCREENSHOT_FILENAME)
            logger.info(f"Screenshot saved successfully to {SCREENSHOT_FILENAME}")
            screenshot_saved = True
        else:
            logger.error("Failed to capture screenshot.")

        try:
            self.collected_points.save_as_json(CLICKS_FILENAME)
            logger.info(f"Points saved successfully to {CLICKS_FILENAME}")
            message = f"Data saved successfully!\nPoints: {CLICKS_FILENAME}"
            if screenshot_saved:
                message += f"\nScreenshot: {SCREENSHOT_FILENAME}"
            elif self.wc:  # Only mention screenshot failure if wc was available
                message += "\n(Screenshot capture failed)"
            QMessageBox.information(self.toolbar, "Save Successful", message)
        except Exception as e:
            logger.exception("Error saving points to JSON:")
            error_message = f"Could not save points data:\n{e}"
            QMessageBox.critical(self.toolbar, "JSON Save Error", error_message)

    # def closeEvent(self, event):
    #     """Ensure overlay is closed when main window closes."""
    #     logger.info("Closing application...")
    #     if self.overlay:
    #         self.overlay.close()
    #     # Stop the timer if it's running
    #     if hasattr(self, 'window_check_timer') and self.window_check_timer:
    #         self.kill_timer(self.window_check_timer)
    #     super().closeEvent(event)
