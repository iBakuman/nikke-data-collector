import json
import sys

from PIL import Image
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QMouseEvent, QPainter, QColor
from PySide6.QtWidgets import (
    QApplication, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QWidget, QScrollArea
)


class ImageClickRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Click Recorder")
        self.resize(1600, 900)  # 限制初始窗口大小

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.image_label.mousePressEvent = self.record_click

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)

        self.save_button = QPushButton("Save Clicks to JSON")
        self.save_button.clicked.connect(self.save_clicks)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        self.clicks = []
        self.display_pixmap = None
        self.image = None

        self.load_image()

    def load_image(self):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if image_path:
            self.image = Image.open(image_path)
            self.display_pixmap = QPixmap(image_path)
            self.image_label.setPixmap(self.display_pixmap)

    def record_click(self, event: QMouseEvent):
        if self.image is None:
            return

        x = int(event.position().x())
        y = int(event.position().y())

        if x < 0 or y < 0 or x >= self.image.width or y >= self.image.height:
            return

        color = self.image.getpixel((x, y))
        print(f"Clicked at ({x}, {y}), color: {color}")
        self.clicks.append({"x": x, "y": y, "color": color})

        self.update_display(x, y)

    def update_display(self, x, y):
        if self.display_pixmap is None:
            return

        pixmap_copy = self.display_pixmap.copy()
        painter = QPainter(pixmap_copy)
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(x, y), 5, 5)
        painter.end()

        self.image_label.setPixmap(pixmap_copy)

    def save_clicks(self):
        if not self.clicks:
            return

        file_dialog = QFileDialog()
        save_path, _ = file_dialog.getSaveFileName(self, "Save JSON", "", "JSON Files (*.json)")
        if save_path:
            with open(save_path, "w") as f:
                json.dump(self.clicks, f, indent=4)
            print(f"Saved to {save_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageClickRecorder()
    window.show()
    sys.exit(app.exec())
