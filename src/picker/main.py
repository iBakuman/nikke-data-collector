import json
import os
import sys
from typing import Dict, List, Optional, Tuple

# Ensure the collector package is discoverable
# This might be needed if running the script directly, adjust as necessary
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to sys.path")

try:
    import win32api
    import win32con
    import win32gui
    from PySide6.QtCore import QPoint, Qt, Signal, Slot
    from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
    from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow,
                                   QMessageBox, QPushButton, QVBoxLayout,
                                   QWidget)

    from collector.logging_config import get_logger
    from collector.ui_def import STANDARD_WINDOW_HEIGHT, STANDARD_WINDOW_WIDTH
    from collector.window_capturer import WindowCapturer
    from collector.window_manager import (WindowManager,
                                          WindowNotFoundException,
                                          get_window_rect)
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure PySide6 and pywin32 are installed (`pip install PySide6 pywin32 psutil mss`) and the project structure is correct.")
    sys.exit(1)

logger = get_logger(__name__)

NIKKE_PROCESS_NAME = "nikke.exe"  # Adjust if your process name is different
OUTPUT_DIR = "output"
SCREENSHOT_FILENAME = os.path.join(OUTPUT_DIR, "screenshot.png")
CLICKS_FILENAME = os.path.join(OUTPUT_DIR, "clicks.json")

PointData = Dict[str, int] # {'x': int, 'y': int, 'r': int, 'g': int, 'b': int}


class OverlayWidget(QWidget):
    """Transparent overlay to capture clicks and display points."""
    clicked = Signal(QMouseEvent)
    points_updated = Signal(list) # Signal to notify when points change

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setCursor(Qt.CrossCursor) # Use crosshair cursor
        self._points: List[Tuple[int, int, Tuple[int, int, int]]] = [] # Store as (x, y, (r, g, b))

    def mousePressEvent(self, event: QMouseEvent):
        """Emit signal when clicked."""
        self.clicked.emit(event)
        super().mousePressEvent(event)

    def set_points(self, points: List[Tuple[int, int, Tuple[int, int, int]]]):
        """Update the points to be drawn."""
        self._points = points
        self.points_updated.emit(self._points) # Emit signal
        self.update() # Trigger repaint

    def paintEvent(self, event):
        """Draw captured points on the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw a thin border around the overlay (optional)
        # painter.setPen(QPen(QColor(0, 255, 0, 150), 1))
        # painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Draw circles at clicked points
        for x, y, (r, g, b) in self._points:
            # Draw outer circle (e.g., white)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPoint(x, y), 5, 5)

            # Draw inner circle with the captured color
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(r, g, b))
            painter.drawEllipse(QPoint(x, y), 3, 3)


class PickerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.wm: Optional[WindowManager] = None
        self.wc: Optional[WindowCapturer] = None
        self.nikke_hwnd: Optional[int] = None
        self.overlay: Optional[OverlayWidget] = None
        self.collected_points: List[Tuple[int, int, Tuple[int, int, int]]] = [] # (x, y, (r, g, b))
        self.status_label: Optional[QLabel] = None # Initialize here
        self.window_check_timer = None # Initialize timer ID

        if not self._initialize_window_manager():
            # Attempt to show message box even if full app init fails
            if 'QMessageBox' not in globals(): # Check if import succeeded
                print("CRITICAL: Cannot show message box, QMessageBox not imported.")
            else:
                 # We need a QApplication instance to show a QMessageBox *before* the main app object is fully ready or runs
                 # This is a bit tricky. For simplicity, we rely on the calling code (main) to handle this.
                 # The message is shown in _initialize_window_manager if QMessageBox is available.
                 pass
            # Ensure we don't proceed if initialization failed
            # We can't fully rely on the PickerApp instance existing if __init__ fails early.
            # The main function already handles exiting if self.wm is None.
            return


        self._initialize_window_capturer()
        self.init_ui()
        # Check if init_ui failed (e.g., couldn't get rect)
        if not self.centralWidget(): # A basic check if UI setup likely failed
             logger.error("UI Initialization seems to have failed. Cannot start window tracking.")
             return
        self._start_tracking_window()

    def _initialize_window_manager(self) -> bool:
        """Initialize the WindowManager and find the target window."""
        try:
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
            return True
        except WindowNotFoundException:
            error_msg = f"'{NIKKE_PROCESS_NAME}' window not found.\nPlease ensure the game is running."
            logger.error(error_msg)
            # Check if QMessageBox was imported before trying to use it
            if 'QMessageBox' in globals():
                 QMessageBox.critical(None, "Error", error_msg)
            else:
                 print(f"CRITICAL ERROR: {error_msg}") # Fallback to console
            return False
        except Exception as e:
            error_msg = f"An unexpected error occurred during WindowManager initialization: {e}"
            logger.exception("An unexpected error occurred during WindowManager initialization.")
            if 'QMessageBox' in globals():
                 QMessageBox.critical(None, "Error", error_msg)
            else:
                print(f"CRITICAL ERROR: {error_msg}") # Fallback to console
            return False

    def _initialize_window_capturer(self):
        """Initialize the WindowCapturer."""
        if self.wm:
            self.wc = WindowCapturer(self.wm)
            logger.info("WindowCapturer initialized.")

    def _start_tracking_window(self):
        """Use a QTimer to periodically check if the window moved or resized."""
        self.window_check_timer = self.startTimer(250) # Check every 250ms

    def timerEvent(self, event):
        """Handle the timer event to check the window state."""
        if event.timerId() == self.window_check_timer:
            self.update_overlay_position()

    def update_overlay_position(self):
        """Check if the Nikke window moved/resized and update the overlay."""
        if not self.wm or not self.nikke_hwnd or not self.overlay:
            return

        try:
            if not win32gui.IsWindow(self.nikke_hwnd):
                 logger.warning("Nikke window handle is no longer valid. Stopping timer.")
                 self.killTimer(self.window_check_timer)
                 QMessageBox.warning(self, "Window Closed", "The Nikke window appears to have been closed.")
                 self.close() # Optionally close the picker
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
                self.overlay.setGeometry(current_rect[0], current_rect[1], current_size[0], current_size[1])
                # Update the main window's position relative to the overlay/game window if needed
                self.move(current_rect[0], current_rect[1] + current_size[1]) # Position controls below

        except Exception as e:
            logger.exception("Error checking/updating window position:")
            self.killTimer(self.window_check_timer) # Stop timer on error


    def init_ui(self):
        """Initialize the main application UI."""
        if not self.wm or not self.nikke_hwnd:
             logger.error("Cannot initialize UI without WindowManager.")
             return

        nikke_rect = self.wm.get_rect()
        if not nikke_rect:
            logger.error("Failed to get initial Nikke window rect for UI setup.")
            QMessageBox.critical(self, "Error", "Could not get Nikke window dimensions.")
            return

        # Create the overlay widget
        self.overlay = OverlayWidget()
        self.overlay.setGeometry(nikke_rect[0], nikke_rect[1], nikke_rect[2] - nikke_rect[0], nikke_rect[3] - nikke_rect[1])
        self.overlay.clicked.connect(self.handle_overlay_click)
        self.overlay.points_updated.connect(self.update_status_label) # Connect signal
        self.overlay.show()

        # --- Main Control Window ---
        self.setWindowTitle("Nikke Data Picker")
        # Make the control window frameless and stay on top initially might be annoying,
        # let's keep it as a normal window that can be interacted with.
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground) # If making controls transparent too

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("Click on the game window overlay to capture points.")
        layout.addWidget(self.status_label)

        save_button = QPushButton("Save Data")
        save_button.clicked.connect(self.save_data)
        layout.addWidget(save_button)

        clear_button = QPushButton("Clear Points")
        clear_button.clicked.connect(self.clear_points)
        layout.addWidget(clear_button)

        # Position the control window below the game window
        control_window_height = 100 # Adjust as needed
        self.setGeometry(
            nikke_rect[0],
            nikke_rect[3], # Place it right below the game window
            nikke_rect[2] - nikke_rect[0], # Match width
            control_window_height
        )
        logger.info(f"Control window geometry set to: {self.geometry()}")
        self.show()


    @Slot(QMouseEvent)
    def handle_overlay_click(self, event: QMouseEvent):
        """Handle clicks on the overlay."""
        if not self.nikke_hwnd:
            logger.warning("Nikke HWND not available, cannot process click.")
            return

        click_pos_overlay = event.pos() # Position relative to the overlay widget
        # Convert overlay position to screen coordinates
        click_pos_screen = self.overlay.mapToGlobal(click_pos_overlay)

        logger.debug(f"Overlay clicked at: {click_pos_overlay}, Screen coords: {click_pos_screen}")

        hwnd_dc = None # Initialize here
        try:
            # Get the Device Context (DC) for the Nikke window
            # Using GetWindowDC includes the frame, GetDC might be client area only? Test this.
            # Let's try GetDC first as we want the client area color.
            # hwnd_dc = win32gui.GetWindowDC(self.nikke_hwnd) # Gets DC for the whole window (incl. frame)
            hwnd_dc = win32gui.GetDC(self.nikke_hwnd) # Gets DC for the client area

            if not hwnd_dc:
                 logger.error("Failed to get Device Context for Nikke window.")
                 return

            # Get the pixel color at the screen coordinates
            # Note: GetPixel expects coordinates relative to the DC's origin.
            # For GetDC(hwnd), origin is the top-left of the client area.
            # For GetWindowDC(hwnd), origin is top-left of the window (incl. frame).
            # We need coords relative to the client area top-left.
            client_rect = win32gui.GetClientRect(self.nikke_hwnd) # (0, 0, width, height)
            screen_top_left = win32gui.ClientToScreen(self.nikke_hwnd, (client_rect[0], client_rect[1]))

            # Calculate click position relative to client area top-left
            click_x_client = click_pos_screen.x() - screen_top_left[0]
            click_y_client = click_pos_screen.y() - screen_top_left[1]

            # Check if click is within the client area bounds
            client_width = client_rect[2] - client_rect[0]
            client_height = client_rect[3] - client_rect[1]
            if not (0 <= click_x_client < client_width and 0 <= click_y_client < client_height):
                 logger.warning(f"Click ({click_x_client}, {click_y_client}) is outside the client area ({client_width}x{client_height}). Skipping.")
                 win32gui.ReleaseDC(self.nikke_hwnd, hwnd_dc)
                 return

            color_ref = win32gui.GetPixel(hwnd_dc, click_x_client, click_y_client)
            win32gui.ReleaseDC(self.nikke_hwnd, hwnd_dc) # Release the DC!

            if color_ref == -1: # Error checking
                logger.error(f"GetPixel failed at screen coordinates {click_pos_screen} (Client: {click_x_client}, {click_y_client}). Is the window obscured?")
                return

            # Convert COLORREF (BGR) to RGB
            r = color_ref & 0xff
            g = (color_ref >> 8) & 0xff
            b = (color_ref >> 16) & 0xff

            # Store the point relative to the overlay/client area top-left
            relative_x = click_pos_overlay.x()
            relative_y = click_pos_overlay.y()
            self.collected_points.append((relative_x, relative_y, (r, g, b)))
            logger.info(f"Point captured: ({relative_x}, {relative_y}) -> RGB({r}, {g}, {b})")

            # Update the overlay to draw the new point
            self.overlay.set_points(self.collected_points)

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
        self.collected_points = []
        if self.overlay:
            self.overlay.set_points(self.collected_points)
        # self.update_status_label([]) # Called by set_points -> points_updated signal

    @Slot()
    def save_data(self):
        """Save collected points to JSON and capture a screenshot."""
        if not self.collected_points:
            logger.warning("No points collected to save.")
            QMessageBox.information(self, "No Data", "No points have been captured yet.")
            return

        if not self.wc:
             logger.error("WindowCapturer not available, cannot save screenshot.")
             QMessageBox.warning(self, "Error", "Screenshot capture is not available.")
             # Decide whether to proceed with saving JSON only
             # return

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 1. Save screenshot
        screenshot_saved = False
        if self.wc:
            try:
                logger.info(f"Capturing screenshot of Nikke window to {SCREENSHOT_FILENAME}...")
                capture_result = self.wc.capture_window()
                if capture_result:
                    capture_result.save(SCREENSHOT_FILENAME)
                    logger.info(f"Screenshot saved successfully to {SCREENSHOT_FILENAME}")
                    screenshot_saved = True
                else:
                    logger.error("Failed to capture screenshot.")
            except Exception as e:
                logger.exception("Error capturing or saving screenshot:")
                error_msg = f"Could not save screenshot:\n{e}"
                QMessageBox.warning(self, "Screenshot Error", error_msg)

        # 2. Save points to JSON
        json_data = [
            {"x": x, "y": y, "r": r, "g": g, "b": b}
            for x, y, (r, g, b) in self.collected_points
        ]
        try:
            logger.info(f"Saving {len(json_data)} points to {CLICKS_FILENAME}...")
            with open(CLICKS_FILENAME, 'w') as f:
                json.dump(json_data, f, indent=4)
            logger.info(f"Points saved successfully to {CLICKS_FILENAME}")

            # Show success message
            message = f"Data saved successfully!\nPoints: {CLICKS_FILENAME}"
            if screenshot_saved:
                message += f"\nScreenshot: {SCREENSHOT_FILENAME}"
            elif self.wc: # Only mention screenshot failure if wc was available
                message += "\n(Screenshot capture failed)"

            QMessageBox.information(self, "Save Successful", message)

        except Exception as e:
            logger.exception("Error saving points to JSON:")
            # Format the error message for the dialog
            error_message = f"Could not save points data:\n{e}"
            QMessageBox.critical(self, "JSON Save Error", error_message)


    def closeEvent(self, event):
        """Ensure overlay is closed when main window closes."""
        logger.info("Closing application...")
        if self.overlay:
            self.overlay.close()
        # Stop the timer if it's running
        if hasattr(self, 'window_check_timer') and self.window_check_timer:
             self.killTimer(self.window_check_timer)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    picker = PickerApp()
    if picker.wm: # Only run if initialization was successful
        sys.exit(app.exec())
    else:
        logger.info("Exiting application due to initialization failure.")
        sys.exit(1) # Exit with error code if WM failed

if __name__ == "__main__":
    main()
