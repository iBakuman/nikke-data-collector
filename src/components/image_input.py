import io

from PIL import Image
from PySide6.QtCore import QBuffer, QEvent, Qt, Signal
from PySide6.QtGui import QPixmap, QKeyEvent
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

from extractor.character_extractor import pil_to_qimage


class ImageInputWidget(QWidget):
    """Widget for selecting an image, supporting both file selection and clipboard paste"""

    imageChanged = Signal(object)  # Signal emitting the PIL Image

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top section: Image preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(200, 150)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd;")
        self.preview_label.setScaledContents(False)
        main_layout.addWidget(self.preview_label)

        # Bottom section: File path and buttons
        path_layout = QHBoxLayout()

        # Path field
        self.path_field = QLineEdit()
        self.path_field.setReadOnly(True)
        self.path_field.setPlaceholderText("No image selected or use Ctrl+V to paste from clipboard")
        path_layout.addWidget(self.path_field)

        # Browse button
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(self.browse_btn)

        # Paste button
        self.paste_btn = QPushButton("Paste")
        self.paste_btn.clicked.connect(self._on_paste)
        path_layout.addWidget(self.paste_btn)

        main_layout.addLayout(path_layout)

        # Install event filter for keyboard shortcuts
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Filter events to capture keyboard shortcuts"""
        # Handle Ctrl+V keyboard shortcut
        if isinstance(event, QKeyEvent):
            if (event.type() == QEvent.Type.KeyPress and
                    event.key() == Qt.Key.Key_V and
                    (event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
                self._on_paste()
                return True
        return super().eventFilter(obj, event)

    def _on_browse(self):
        """Open file selection dialog when browse button is clicked"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image File",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*.*)"
        )

        if file_path:
            try:
                # Load the image
                image = Image.open(file_path)
                self._set_image(image, file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")

    def _on_paste(self):
        """Handle paste from clipboard"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasImage():
            # Get image from clipboard
            q_image = clipboard.image()
            if not q_image.isNull():
                # Convert QImage to PIL Image
                buffer = QBuffer()
                buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                q_image.save(buffer, "PNG")
                buffer.seek(0)
                pil_image = Image.open(io.BytesIO(buffer.data().data()))
                self._set_image(pil_image, "[Pasted from clipboard]")
            else:
                QMessageBox.warning(self, "Warning", "Clipboard contains an invalid image")
        else:
            QMessageBox.warning(self, "Warning", "No image found in clipboard")

    def _set_image(self, image, source_path=""):
        """Set the image and update the UI"""
        self._image = image

        # Update the preview
        if image:
            q_image = pil_to_qimage(image)
            pixmap = QPixmap.fromImage(q_image)

            # Scale pixmap to fit in preview, maintaining aspect ratio
            preview_size = self.preview_label.size()
            scaled_pixmap = pixmap.scaled(
                preview_size.width(),
                preview_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.preview_label.setPixmap(scaled_pixmap)
            self.path_field.setText(source_path)

            # Emit signal
            self.imageChanged.emit(image)
        else:
            self.preview_label.clear()
            self.path_field.clear()

    def get_image(self):
        """Get the currently selected image"""
        return self._image

    def clear(self):
        """Clear the currently selected image"""
        self._image = None
        self.preview_label.clear()
        self.path_field.clear()
