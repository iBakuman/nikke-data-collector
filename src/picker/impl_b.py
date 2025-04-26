import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageGrab
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QMessageBox, QPushButton, QVBoxLayout, QWidget)

# Import WindowManager
sys.path.append(str(Path(__file__).parent.parent))
from collector.window_manager import WindowManager, WindowNotFoundException


class OverlayButton(QPushButton):
    """Custom button for the floating control panel"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "background-color: rgba(40, 40, 40, 200); "
            "color: white; "
            "border: 1px solid rgba(255, 255, 255, 100); "
            "border-radius: 4px; "
            "padding: 5px 10px;"
        )


class FloatingControls(QWidget):
    """Floating controls panel"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Create layout
        layout = QVBoxLayout(self)

        # Status label
        self.status_label = QLabel("Ready to capture clicks")
        self.status_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 180); "
            "color: white; "
            "padding: 5px; "
            "border-radius: 3px;"
        )

        # Button layout
        button_layout = QHBoxLayout()

        # Save button
        self.save_button = OverlayButton("Save")

        # Close button
        self.close_button = OverlayButton("Close")

        # Add widgets to layouts
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)

        layout.addWidget(self.status_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)


class TransparentOverlay(QWidget):
    """Transparent overlay that covers the client area of the target application"""
    def __init__(self):
        super().__init__()
        self.window_manager = None
        self.client_rect = None
        self.clicks = []
        self.click_markers = []

        # Set up completely transparent overlay
        self.setWindowTitle("Nikke Overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Create floating controls
        self.controls = FloatingControls()
        self.controls.save_button.clicked.connect(self.save_data)
        self.controls.close_button.clicked.connect(self.close_app)

        # Set up a timer to refresh position
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_position)

        # Find and attach to Nikke
        if self.find_and_attach_to_nikke():
            # Show controls and start refresh timer
            self.controls.show()
            self.refresh_timer.start(1000)  # Refresh position every 1 second

    def close_app(self):
        """Close the application"""
        self.controls.close()
        self.close()
        QApplication.quit()

    def refresh_position(self):
        """Refresh the overlay position to match the game window"""
        try:
            if not self.window_manager:
                return

            # Update the client rect
            self.client_rect = self.window_manager.get_rect()

            # Update overlay position
            self.setGeometry(
                self.client_rect[0],  # left
                self.client_rect[1],  # top
                self.client_rect[2] - self.client_rect[0],  # width
                self.client_rect[3] - self.client_rect[1]   # height
            )

            # Update controls position (top-right corner of client area)
            self.controls.setGeometry(
                self.client_rect[2] - self.controls.width() - 10,  # right edge of client - control width - margin
                self.client_rect[1] + 10,  # top of client + margin
                self.controls.width(),
                self.controls.height()
            )

            # Ensure proper visibility
            self.raise_()
            self.controls.raise_()

        except Exception as e:
            print(f"Error refreshing position: {e}")

    def find_and_attach_to_nikke(self):
        """Find the Nikke.exe window and position our overlay on top of it"""
        try:
            # Create WindowManager instance for Nikke.exe
            self.window_manager = WindowManager("nikke.exe", exact_match=False)

            # Get window information specifically for the client area
            self.client_rect = self.window_manager.get_rect()

            # Calculate width and height of client area
            width = self.client_rect[2] - self.client_rect[0]
            height = self.client_rect[3] - self.client_rect[1]

            # Set the overlay geometry to exactly match the client area
            self.setGeometry(
                self.client_rect[0],  # left
                self.client_rect[1],  # top
                width,
                height
            )

            # Position controls
            self.controls.adjustSize()  # Make sure controls size is known
            self.controls.move(
                self.client_rect[2] - self.controls.width() - 10,
                self.client_rect[1] + 10
            )

            self.controls.status_label.setText(f"Client area: {width}x{height}")
            return True

        except WindowNotFoundException:
            QMessageBox.warning(None, "Error", "Nikke game window not found. Please make sure the game is running.")
            return False
        except Exception as e:
            QMessageBox.warning(None, "Error", f"Failed to attach to Nikke window: {str(e)}")
            return False

    def get_pixel_color(self, x, y):
        """Get pixel color at the specified absolute screen coordinates"""
        try:
            screenshot = ImageGrab.grab(bbox=(x, y, x+1, y+1))
            color = screenshot.getpixel((0, 0))
            return color
        except Exception as e:
            print(f"Error getting pixel color: {e}")
            return (0, 0, 0)  # Return black in case of error

    def mousePressEvent(self, event: QMouseEvent):
        """Record click positions and colors"""
        if not self.window_manager or not self.client_rect:
            return

        # Get relative coordinates within our overlay
        x = int(event.position().x())
        y = int(event.position().y())

        # Calculate absolute screen coordinates for color sampling
        screen_x = x + self.client_rect[0]
        screen_y = y + self.client_rect[1]

        # Get color from the game window
        color = self.get_pixel_color(screen_x, screen_y)

        # Store coordinates (relative to client area) and color
        self.clicks.append({"x": x, "y": y, "color": color})

        # Update status
        self.controls.status_label.setText(
            f"Clicked at ({x}, {y}), color: {color} - Total: {len(self.clicks)}"
        )

        # Show marker
        self.show_click_marker(x, y)

    def show_click_marker(self, x, y):
        """Display a marker at the clicked position"""
        # Create marker
        marker = QLabel(self)
        marker.setStyleSheet("background-color: rgba(255, 0, 0, 150); border-radius: 5px;")
        marker.setGeometry(x-5, y-5, 10, 10)
        marker.show()

        # Add to list for cleanup
        self.click_markers.append(marker)

        # Remove marker after a delay
        QTimer.singleShot(1000, lambda: self.remove_marker(marker))

    def remove_marker(self, marker):
        """Remove a click marker"""
        if marker in self.click_markers:
            self.click_markers.remove(marker)
        marker.deleteLater()

    def save_data(self):
        """Save screenshot and click data"""
        if not self.window_manager or not self.clicks or not self.client_rect:
            QMessageBox.warning(None, "Warning", "No data to save or target window not found")
            return

        # Ask for save location
        file_dialog = QFileDialog()
        base_path, _ = file_dialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")

        if not base_path:
            return

        # Remove extension if present
        if base_path.endswith('.json'):
            base_path = base_path[:-5]

        try:
            # Capture screenshot of client area
            screenshot = ImageGrab.grab(bbox=self.client_rect)

            # Save screenshot
            screenshot_path = f"{base_path}.png"
            screenshot.save(screenshot_path)

            # Save click data
            json_path = f"{base_path}.json"
            with open(json_path, "w") as f:
                json.dump(self.clicks, f, indent=4)

            self.controls.status_label.setText(f"Saved data to {json_path}")

        except Exception as e:
            QMessageBox.warning(None, "Error", f"Failed to save data: {str(e)}")

def main():
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

