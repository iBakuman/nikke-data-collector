import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import win32gui
from PySide6.QtCore import QPoint, Qt, Signal, Slot, QObject, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QLabel, QMessageBox, QPushButton, QWidget, QToolBar)
from dataclass_wizard.serial_json import JSONWizard, JSONPyWizard

from collector.logging_config import get_logger
from collector.mixin import JSONSerializableMixin
from collector.ui_def import STANDARD_WINDOW_HEIGHT, STANDARD_WINDOW_WIDTH
from collector.window_capturer import WindowCapturer
from collector.window_manager import (WindowManager,
                                      get_window_rect)

logger = get_logger(__name__)

NIKKE_PROCESS_NAME = "nikke.exe"  # Adjust if your process name is different
OUTPUT_DIR = "output"
SCREENSHOT_FILENAME = os.path.join(OUTPUT_DIR, "screenshot.png")
CLICKS_FILENAME = os.path.join(OUTPUT_DIR, "clicks.json")


class OverlayWidget(QWidget):
    """Transparent overlay to capture clicks and display points."""
    clicked = Signal(QMouseEvent)
    points_updated = Signal(list)  # Signal to notify when points change

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        # self.setCursor(Qt.CursorShape.CrossCursor)  # Use crosshair cursor
        self._points: List[Tuple[int, int, Tuple[int, int, int]]] = []  # Store as (x, y, (r, g, b))

    def mousePressEvent(self, event: QMouseEvent):
        """Emit signal when clicked."""
        self.clicked.emit(event)
        super().mousePressEvent(event)

    def set_points(self, points: List[Tuple[int, int, Tuple[int, int, int]]]):
        """Update the points to be drawn."""
        self._points = points
        self.points_updated.emit(self._points)  # Emit signal
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw captured points on the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # DEBUG: Make overlay background slightly visible
        painter.fillRect(self.rect(), QColor(0, 255, 0, 30))  # Semi-transparent green

        # Draw a thin border around the overlay (optional)
        # painter.setPen(QPen(QColor(0, 255, 0, 150), 1))
        # painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Draw circles at clicked points
        for x, y, (r, g, b) in self._points:
            # Draw outer circle (e.g., white)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPoint(x, y), 5, 5)

            # Draw inner circle with the captured color
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(r, g, b))
            painter.drawEllipse(QPoint(x, y), 3, 3)


@dataclass
class Coordinate(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    x: float
    y: float
    color: Tuple[int, int, int]

    def to_tuple(self) -> Tuple[int, int, Tuple[int, int, int]]:
        return int(self.x), int(self.y), self.color

class Coordinates(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    coordinates: List[Coordinate] = []

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
        self.status_label: Optional[QLabel] = None  # Initialize here
        self.window_check_timer = None  # Initialize timer ID
        self.wm: Optional[WindowManager] = None
        self._initialize_window_manager()
        self.wc = WindowCapturer(self.wm)
        self.init_ui()
        self.timer = QTimer()
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.update_overlay_position)
        self.timer.start()

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
        self.status_label = QLabel("Click on the game window overlay to capture points.")
        self.toolbar.addWidget(self.status_label)
        save_button = QPushButton("Save Data")
        save_button.clicked.connect(self.save_data)
        self.toolbar.addWidget(save_button)

        clear_button = QPushButton("Clear Points")
        clear_button.clicked.connect(self.clear_points)
        self.toolbar.addWidget(clear_button)
        self.toolbar.setGeometry(self.wm.start_x, self.wm.start_y + self.wm.height + 20, self.wm.width, 20)
        self.toolbar.show()

    def init_overlay(self):
        self.overlay = OverlayWidget()
        self.overlay.clicked.connect(self.handle_overlay_click)
        self.overlay.points_updated.connect(self.update_status_label)  # Connect signal
        self.overlay.setGeometry(self.wm.start_x, self.wm.start_y, self.wm.width, self.wm.height)
        logger.info("--- Overlay window.show() called ---")  # DEBUG
        self.overlay.show()

    @Slot(QMouseEvent)
    def handle_overlay_click(self, event: QMouseEvent):
        """Handle clicks on the overlay."""
        logger.info("--- handle_overlay_click called --- ")  # DEBUG
        if not self.nikke_hwnd:
            logger.warning("Nikke HWND not available, cannot process click.")
            return

        click_pos_overlay = event.position()  # Position relative to the overlay widget
        # Convert overlay position to screen coordinates
        click_pos_screen = self.overlay.mapToGlobal(click_pos_overlay)

        logger.debug(f"Overlay clicked at: {click_pos_overlay}, Screen coords: {click_pos_screen}")

        hwnd_dc = None  # Initialize here
        try:
            # Get the Device Context (DC) for the Nikke window
            # Using GetWindowDC includes the frame, GetDC might be client area only? Test this.
            # Let's try GetDC first as we want the client area color.
            # hwnd_dc = win32gui.GetWindowDC(self.nikke_hwnd) # Gets DC for the whole window (incl. frame)
            hwnd_dc = win32gui.GetDC(self.nikke_hwnd)  # Gets DC for the client area

            if not hwnd_dc:
                logger.error("Failed to get Device Context for Nikke window.")
                return

            # Get the pixel color at the screen coordinates
            # Note: GetPixel expects coordinates relative to the DC's origin.
            # For GetDC(hwnd), origin is the top-left of the client area.
            # For GetWindowDC(hwnd), origin is top-left of the window (incl. frame).
            # We need coords relative to the client area top-left.
            client_rect = win32gui.GetClientRect(self.nikke_hwnd)  # (0, 0, width, height)
            screen_top_left = win32gui.ClientToScreen(self.nikke_hwnd, (client_rect[0], client_rect[1]))

            # Calculate click position relative to client area top-left
            click_x_client = int(click_pos_screen.x() - screen_top_left[0])
            click_y_client = int(click_pos_screen.y() - screen_top_left[1])

            # Check if click is within the client area bounds
            client_width = client_rect[2] - client_rect[0]
            client_height = client_rect[3] - client_rect[1]
            if not (0 <= click_x_client < client_width and 0 <= click_y_client < client_height):
                logger.warning(
                    f"Click ({click_x_client}, {click_y_client}) is outside the client area ({client_width}x{client_height}). Skipping.")
                win32gui.ReleaseDC(self.nikke_hwnd, hwnd_dc)
                return

            color_ref = win32gui.GetPixel(hwnd_dc, click_x_client, click_y_client)
            win32gui.ReleaseDC(self.nikke_hwnd, hwnd_dc)  # Release the DC!

            if color_ref == -1:  # Error checking
                logger.error(
                    f"GetPixel failed at screen coordinates {click_pos_screen} (Client: {click_x_client}, {click_y_client}). Is the window obscured?")
                return

            # Convert COLORREF (BGR) to RGB
            r = color_ref & 0xff
            g = (color_ref >> 8) & 0xff
            b = (color_ref >> 16) & 0xff

            # Store the point relative to the overlay/client area top-left
            relative_x = click_pos_overlay.x()
            relative_y = click_pos_overlay.y()
            self.collected_points.add(Coordinate(x=relative_x, y=relative_y, color=(r, g, b)))
            logger.info(f"Point captured: ({relative_x}, {relative_y}) -> RGB({r}, {g}, {b})")
            # Update the overlay to draw the new point
            self.overlay.set_points(self.collected_points.to_list())

        except Exception as e:
            logger.exception(f"Error getting pixel color at {click_pos_screen}:")
            # Ensure DC is released even if error occurs after getting it
            if 'hwnd_dc' in locals() and hwnd_dc:
                try:
                    win32gui.ReleaseDC(self.nikke_hwnd, hwnd_dc)
                except Exception as release_e:
                    logger.error(f"Error releasing DC: {release_e}")

    @Slot(list)
    def update_status_label(self, points):
        """Update the status label with the number of points."""
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


def main():
    app = QApplication(sys.argv)
    picker = PickerApp()
    if picker.wm:  # Only run if initialization was successful
        sys.exit(app.exec())
    else:
        logger.info("Exiting application due to initialization failure.")
        sys.exit(1)  # Exit with error code if WM failed


os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

if __name__ == "__main__":
    main()
