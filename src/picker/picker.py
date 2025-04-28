import io
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

import win32gui
from dataclass_wizard.serial_json import JSONPyWizard, JSONWizard
from PIL import ImageDraw
from PySide6.QtCore import QObject, QPoint, QRect, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import (QComboBox, QInputDialog, QLabel, QMessageBox,
                               QPushButton, QToolBar, QWidget)

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

    def set_selection_mode(self, mode: SelectionMode):
        """Change the selection mode."""
        self.selection_mode = mode
        self.region_selection_step = 0
        self.template_region = None
        self.current_selection = QRect()
        self.update()

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
        if self.selection_mode == SelectionMode.REGION and self.is_selecting:
            current_pos = event.position().toPoint()
            self.current_selection = QRect(
                self.selection_start,
                current_pos
            ).normalized()  # Normalized ensures width/height are positive
            self.update()
        super().mouseMoveEvent(event)

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
                painter.setBrush(QColor(0, 255, 0, 40))  # Transparent green fill
                painter.drawRect(self.template_region)

            # Draw current selection rectangle
            if self.is_selecting and self.current_selection.isValid():
                painter.setPen(QPen(QColor(255, 0, 0), 2))  # Red for current selection
                painter.setBrush(QColor(255, 0, 0, 40))  # Transparent red fill
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

            current_pos = QPoint(current_rect[0], current_rect[1])
            current_size = (current_rect[2] - current_rect[0], current_rect[3] - current_rect[1])

            overlay_pos = self.overlay.pos()
            overlay_size = (self.overlay.width(), self.overlay.height())

            if current_pos != overlay_pos or current_size != overlay_size:
                logger.info(f"Nikke window changed. Updating overlay geometry to {current_rect}")
                self.toolbar.setGeometry(self.wm.start_x, self.wm.start_y + self.wm.height + 20, self.wm.width, 20)
                self.overlay.setGeometry(self.wm.start_x, self.wm.start_y, self.wm.width, self.wm.height)
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

            # Extract the template image
            template_x, template_y = template_region.x(), template_region.y()
            template_w, template_h = template_region.width(), template_region.height()

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

            # Create ImageElementEntity
            image_element = ImageElementEntity(
                name=element_name,
                region_x=detection_region.x(),
                region_y=detection_region.y(),
                region_width=detection_region.width(),
                region_height=detection_region.height(),
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
            with open(element_path, 'w') as f:
                json.dump(image_element.to_dict(), f, indent=2)

            # Draw visualization of detection region on full screenshot
            screenshot_with_regions = pil_image.copy()
            draw = ImageDraw.Draw(screenshot_with_regions)

            # Draw detection region (red)
            draw.rectangle(
                (detection_region.x(), detection_region.y(),
                detection_region.x() + detection_region.width(),
                detection_region.y() + detection_region.height()),
                outline=(255, 0, 0), width=2
            )

            # Draw template region (green)
            draw.rectangle(
                (template_region.x(), template_region.y(),
                template_region.x() + template_region.width(),
                template_region.y() + template_region.height()),
                outline=(0, 255, 0), width=2
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
