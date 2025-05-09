from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QVBoxLayout,
                               QWidget)

# Configurable magnification factor and region size
REGION_SIZE = 100       # Default sampled square region size in pixels
MAGNIFICATION = 2       # Default magnification factor

class Magnifier(QWidget):
    def __init__(self):
        super().__init__()
        # Main window logic: set window properties
        self.setWindowTitle("Magnifier")  # Optional window title
        # Always on top, frameless, tool window so it doesn't appear in taskbar
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # Make window transparent to mouse events so mouse can interact with applications underneath
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Initialize region size and magnification
        self.region_size = REGION_SIZE
        self.magnification = MAGNIFICATION
        # Calculate magnified display size
        self.display_size = self.region_size * self.magnification

        # Create label for magnified image
        self.image_label = QLabel(self)
        # Fix label size to the magnified image size
        self.image_label.setFixedSize(self.display_size, self.display_size)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create color patch and RGB text labels
        self.color_patch = QLabel(self)
        self.color_patch.setFixedSize(20, 20)
        # Initial color patch style
        self.color_patch.setStyleSheet("background-color: black; border: 1px solid #333;")
        self.color_text = QLabel(self)
        self.color_text.setText("R:0 G:0 B:0")

        # Layout setup
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(5, 0, 5, 5)   # Margins around color info
        info_layout.setSpacing(5)
        info_layout.addWidget(self.color_patch)
        info_layout.addWidget(self.color_text)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)   # No margin around main layout
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(info_layout)

        # Mouse tracking in real-time via QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateMagnifier)
        self.timer.start(30)  # Update every 30 ms

    def updateMagnifier(self):
        # Get current global mouse cursor position
        cursor_pos = QCursor.pos()
        # Find which screen the cursor is on
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        screen_geom = screen.geometry()

        # Safe window positioning to avoid covering cursor or going off-screen
        win_w = self.width()
        win_h = self.height()
        # Default position: bottom-right of cursor
        margin = (self.region_size + 1) // 2   # Offset to avoid overlapping captured region
        pos_x = cursor_pos.x() + margin
        pos_y = cursor_pos.y() + margin
        # Adjust to left of cursor if hitting right edge
        if pos_x + win_w > screen_geom.x() + screen_geom.width():
            pos_x = cursor_pos.x() - margin - win_w
        # Adjust above cursor if hitting bottom edge
        if pos_y + win_h > screen_geom.y() + screen_geom.height():
            pos_y = cursor_pos.y() - margin - win_h
        # Clamp position within screen bounds
        if pos_x < screen_geom.x():
            pos_x = screen_geom.x()
        if pos_y < screen_geom.y():
            pos_y = screen_geom.y()
        # Move the window to the new position
        self.move(pos_x, pos_y)

        # Screen capture of region around cursor and magnify it
        region_w = self.region_size
        region_h = self.region_size
        # Calculate top-left of capture region
        reg_x = cursor_pos.x() - region_w // 2
        reg_y = cursor_pos.y() - region_h // 2
        # Clamp capture region within screen bounds
        if reg_x < screen_geom.x():
            reg_x = screen_geom.x()
        if reg_x + region_w > screen_geom.x() + screen_geom.width():
            reg_x = screen_geom.x() + screen_geom.width() - region_w
        if reg_y < screen_geom.y():
            reg_y = screen_geom.y()
        if reg_y + region_h > screen_geom.y() + screen_geom.height():
            reg_y = screen_geom.y() + screen_geom.height() - region_h

        # Grab the specified screen region as an image
        screenshot = screen.grabWindow(0, reg_x, reg_y, region_w, region_h).toImage()
        # Get the color of the pixel under the cursor
        local_x = cursor_pos.x() - reg_x
        local_y = cursor_pos.y() - reg_y
        pixel_color = QColor(screenshot.pixel(int(local_x), int(local_y)))
        # Update color patch and RGB text
        self.color_patch.setStyleSheet(f"background-color: {pixel_color.name()}; border: 1px solid #000;")
        self.color_text.setText(f"R:{pixel_color.red()} G:{pixel_color.green()} B:{pixel_color.blue()}")

        # Scale the screenshot by the magnification factor
        if self.magnification != 1:
            scaled_img = screenshot.scaled(region_w * self.magnification,
                                           region_h * self.magnification,
                                           Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
            display_pixmap = QPixmap.fromImage(scaled_img)
        else:
            display_pixmap = QPixmap.fromImage(screenshot)
        # Display the magnified image in the label
        self.image_label.setPixmap(display_pixmap)

        # Adjust window size if needed
        # Usually not needed if layout is fixed
        # self.adjustSize()

if __name__ == "__main__":
    app = QApplication([])
    magnifier = Magnifier()
    magnifier.show()
    app.exec()
