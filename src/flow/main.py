from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (QColor, QCursor, QGuiApplication, QPainter, QPen)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                               QVBoxLayout, QWidget)

# Configurable magnification factor and region size
DISPLAY_SIZE = 200      # Size of the display window in pixels
MAGNIFICATION = 4       # Default magnification factor
CROSSHAIR_COLOR = QColor(255, 0, 0)  # Crosshair color (default: red)
CROSSHAIR_THICKNESS = 1   # Crosshair thickness in pixels
UPDATE_INTERVAL_MS = 30   # Update interval in milliseconds

class Magnifier(QWidget):
    def __init__(self):
        super().__init__()
        # Main window logic: set window properties
        self.setWindowTitle("Magnifier")  # Optional window title
        # Always on top, frameless, tool window so it doesn't appear in taskbar
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # Make window transparent to mouse events so mouse can interact with applications underneath
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Initialize display size and magnification
        self.display_size = DISPLAY_SIZE  # Fixed display window size
        self.magnification = MAGNIFICATION

        # Create label for magnified image
        self.image_label = QLabel(self)
        # Fix label size to the display size
        self.image_label.setFixedSize(self.display_size, self.display_size)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create color patch and RGB text labels
        self.color_patch = QFrame(self)
        self.color_patch.setFixedSize(20, 20)
        self.color_patch.setFrameShape(QFrame.Shape.Box)  # Box frame for aesthetics
        # Initial color patch style
        self.color_patch.setStyleSheet("background-color: black; border: 1px solid #333;")
        self.color_text = QLabel(self)
        self.color_text.setText("R:0 G:0 B:0")

        # Make the font a bit smaller for the color text
        font = self.color_text.font()
        font.setPointSize(8)
        self.color_text.setFont(font)

        # Layout setup
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(5, 0, 5, 5)   # Margins around color info
        info_layout.setSpacing(5)
        info_layout.addWidget(self.color_patch)
        info_layout.addWidget(self.color_text)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)   # Smaller margins for the main layout
        main_layout.setSpacing(0)
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(info_layout)

        # Mouse tracking in real-time via QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_magnifier)
        self.timer.start(UPDATE_INTERVAL_MS)  # Update interval

    def update_magnifier(self):
        # Get current global mouse cursor position
        cursor_pos = QCursor.pos()

        # Find which screen the cursor is on
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen is None:
            # Fall back to primary screen if cursor position doesn't map to any screen
            screen = QGuiApplication.primaryScreen()

            # If we still don't have a valid screen, try to use any available screen
            if screen is None:
                screens = QGuiApplication.screens()
                if screens:
                    screen = screens[0]
                else:
                    # No screens available, can't proceed
                    return

        screen_geom = screen.geometry()

        # Get virtual desktop information
        virtual_desktop = QGuiApplication.primaryScreen().virtualGeometry()

        # Calculate the capture size based on the magnification
        # For higher magnification, we capture a smaller region
        capture_size = int(self.display_size / self.magnification)

        # Ensure we capture an odd size so the center pixel is exactly at the center
        if capture_size % 2 == 0:
            capture_size += 1

        # Half the capture size with exact precision
        half_capture = capture_size / 2

        # Calculate capture region coordinates, keeping cursor exactly at center
        capture_x = int(cursor_pos.x() - half_capture)
        capture_y = int(cursor_pos.y() - half_capture)

        # Clamp capture region to screen boundaries
        if capture_x < screen_geom.x():
            capture_x = screen_geom.x()
        if capture_x + capture_size > screen_geom.x() + screen_geom.width():
            capture_x = screen_geom.x() + screen_geom.width() - capture_size
        if capture_y < screen_geom.y():
            capture_y = screen_geom.y()
        if capture_y + capture_size > screen_geom.y() + screen_geom.height():
            capture_y = screen_geom.y() + screen_geom.height() - capture_size

        # Calculate relative coordinates for the screen capture
        rel_x = capture_x - screen_geom.x()
        rel_y = capture_y - screen_geom.y()

        # Capture the screen region
        pixmap = screen.grabWindow(0, rel_x, rel_y, capture_size, capture_size)

        # Scale the captured image to fill the display window
        scaled_pixmap = pixmap.scaled(
            self.display_size,
            self.display_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Draw a crosshair at the exact center of the display
        center_x = self.display_size / 2
        center_y = self.display_size / 2

        # Convert center coordinates to integers for drawing
        center_x_int = int(center_x)
        center_y_int = int(center_y)

        # Create a QPainter to draw on the scaled pixmap
        painter = QPainter(scaled_pixmap)
        pen = QPen(CROSSHAIR_COLOR, CROSSHAIR_THICKNESS)
        painter.setPen(pen)

        # Draw horizontal and vertical lines crossing at the center
        painter.drawLine(0, center_y_int, scaled_pixmap.width(), center_y_int)
        painter.drawLine(center_x_int, 0, center_x_int, scaled_pixmap.height())
        painter.end()

        # Display the magnified image with crosshair
        self.image_label.setPixmap(scaled_pixmap)

        # Position the magnifier window to avoid covering the cursor
        win_w = self.width()
        win_h = self.height()

        # Default position: bottom-right of cursor
        offset = 20  # Fixed offset from cursor
        pos_x = cursor_pos.x() + offset
        pos_y = cursor_pos.y() + offset

        # Adjust to left of cursor if hitting right edge
        if pos_x + win_w > virtual_desktop.x() + virtual_desktop.width():
            pos_x = cursor_pos.x() - offset - win_w
        # Adjust above cursor if hitting bottom edge
        if pos_y + win_h > virtual_desktop.y() + virtual_desktop.height():
            pos_y = cursor_pos.y() - offset - win_h

        # Clamp position within virtual desktop bounds
        if pos_x < virtual_desktop.x():
            pos_x = virtual_desktop.x()
        if pos_y < virtual_desktop.y():
            pos_y = virtual_desktop.y()

        # Move the window to the new position
        self.move(pos_x, pos_y)

        # Get the color of the pixel precisely at the cursor position
        pixel_color = screen.grabWindow(
            0,
            cursor_pos.x() - screen_geom.x(),
            cursor_pos.y() - screen_geom.y(),
            1, 1
        ).toImage().pixelColor(0, 0)

        # Update color patch and RGB text
        self.color_patch.setStyleSheet(
            f"background-color: rgb({pixel_color.red()},{pixel_color.green()},{pixel_color.blue()}); border: 1px solid #000;"
        )
        self.color_text.setText(f"R:{pixel_color.red()} G:{pixel_color.green()} B:{pixel_color.blue()}")

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Floor)

if __name__ == "__main__":
    app = QApplication([])
    magnifier = Magnifier()
    magnifier.show()
    app.exec()
