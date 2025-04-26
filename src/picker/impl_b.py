import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageGrab
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QMessageBox, QPushButton, QVBoxLayout, QWidget)

# Import WindowManager
sys.path.append(str(Path(__file__).parent.parent))
from collector.window_manager import WindowManager, WindowNotFoundException


class TransparentOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.window_manager = None
        self.clicks = []

        # Set up transparent window
        self.setWindowTitle("Nikke Overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Save button at the bottom
        self.save_button = QPushButton("Save Clicks")
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet("background-color: rgba(0, 120, 215, 180); color: white; padding: 10px;")

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet("background-color: rgba(215, 0, 0, 180); color: white; padding: 10px;")

        # Status label
        self.status_label = QLabel("Click to record positions")
        self.status_label.setStyleSheet("background-color: rgba(0, 0, 0, 150); color: white; padding: 5px;")

        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.status_label)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Find Nikke window and position overlay
        self.find_and_attach_to_nikke()

    def find_and_attach_to_nikke(self):
        """Find the Nikke.exe window and position our overlay on top of it"""
        try:
            # Create WindowManager instance for Nikke.exe
            self.window_manager = WindowManager("nikke.exe", exact_match=False)

            # Get window information
            window_info = self.window_manager.get_window_info()
            rect = window_info.rect

            # Set our overlay window position and size to match the game window
            self.setGeometry(
                rect[0],  # left
                rect[1],  # top
                rect[2] - rect[0],  # width
                rect[3] - rect[1]   # height
            )

            self.status_label.setText(f"Overlay active - Client area: {rect[2]-rect[0]}x{rect[3]-rect[1]}")
            return True

        except WindowNotFoundException:
            QMessageBox.warning(None, "Error", "Nikke game window not found. Please make sure the game is running.")
            return False
        except Exception as e:
            QMessageBox.warning(None, "Error", f"Failed to attach to Nikke window: {str(e)}")
            return False

    def get_pixel_color(self, x, y):
        """Get pixel color at the specified coordinates"""
        screenshot = ImageGrab.grab(bbox=(
            x, y, x+1, y+1
        ))
        return screenshot.getpixel((0, 0))  # Return RGB color tuple

    def mousePressEvent(self, event: QMouseEvent):
        """Record click positions and colors from target window"""
        if not self.window_manager:
            return

        x = int(event.position().x())
        y = int(event.position().y())

        # Get global coordinates
        global_x = x + self.geometry().left()
        global_y = y + self.geometry().top()

        # Get color from screen at clicked position
        color = self.get_pixel_color(global_x, global_y)

        # Save coordinates relative to window
        self.clicks.append({"x": x, "y": y, "color": color})
        self.status_label.setText(f"Clicked at ({x}, {y}), color: {color} - Total clicks: {len(self.clicks)}")

        # Visualize click with temporary overlay
        self.show_click_marker(x, y)

    def show_click_marker(self, x, y):
        """Show a temporary marker where the user clicked"""
        marker = QLabel(self)
        marker.setStyleSheet("background-color: rgba(255, 0, 0, 150); border-radius: 5px;")
        marker.setGeometry(x-5, y-5, 10, 10)
        marker.show()

        # Schedule marker to disappear
        QApplication.processEvents()
        time.sleep(0.2)  # Show marker briefly
        marker.deleteLater()

    def save_data(self):
        """Save screenshot and click data"""
        if not self.window_manager or not self.clicks:
            QMessageBox.warning(self, "Warning", "No data to save or target window not found")
            return

        # Ask for save location
        file_dialog = QFileDialog()
        base_path, _ = file_dialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")

        if not base_path:
            return

        # Remove extension if present
        if base_path.endswith('.json'):
            base_path = base_path[:-5]

        # Get window rect
        rect = self.window_manager.get_rect()

        # Capture screenshot of client area
        screenshot = ImageGrab.grab(bbox=rect)

        # Save screenshot
        screenshot_path = f"{base_path}.png"
        screenshot.save(screenshot_path)

        # Save click data
        json_path = f"{base_path}.json"
        with open(json_path, "w") as f:
            json.dump(self.clicks, f, indent=4)

        self.status_label.setText(f"Saved screenshot to {screenshot_path} and click data to {json_path}")

def main():
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    overlay.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

