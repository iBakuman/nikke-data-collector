from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)


class PreviewDialog(QDialog):
    """Simple image preview dialog without complex processing"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Preview")
        layout = QVBoxLayout(self)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def set_image(self, pixmap):
        """Set the image to display"""
        if pixmap and not pixmap.isNull():
            # Set the pixmap to the label
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("No image to display")


class ImageInputWidget(QWidget):
    """Widget for selecting an image, supporting both file selection and clipboard paste"""

    imageChanged = Signal(object)  # Signal emitting the PIL Image

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QImage()
        self._setup_ui()
        shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        shortcut.activated.connect(self._on_paste)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top section: Status label and preview button
        top_layout = QHBoxLayout()

        self.status_label = QLabel("No image selected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.status_label)

        self.preview_btn = QPushButton("Preview Image")
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self._show_preview)
        top_layout.addWidget(self.preview_btn)

        main_layout.addLayout(top_layout)

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

    def _show_preview(self):
        """Show image preview in a dialog"""
        if not self.image:
            return

        try:
            dialog = PreviewDialog(self)
            pixmap = QPixmap.fromImage(self.image)
            dialog.set_image(pixmap)
            dialog.show()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not show preview: {str(e)}")

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
                self._set_image(ImageQt(file_path), file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")

    def _on_paste(self):
        """Handle paste from clipboard"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasImage():
            # Get image from clipboard
            q_image = clipboard.image()
            _format = q_image.format()
            print(_format)
            if not q_image.isNull():
                self._set_image(q_image, "[Pasted from clipboard]")
            else:
                QMessageBox.warning(self, "Warning", "Clipboard contains an invalid image")
        else:
            QMessageBox.warning(self, "Warning", "No image found in clipboard")

    def _set_image(self, image: QImage, source_path: str=""):
        """Set the image and update the UI"""
        self.image = image

        # Update the UI
        if image:
            # Update status label
            self.status_label.setText(f"Image: {image.width()}x{image.height()} px")
            self.preview_btn.setEnabled(True)
            self.path_field.setText(source_path)
            self.imageChanged.emit(image)
        else:
            self.status_label.setText("No image selected")
            self.preview_btn.setEnabled(False)
            self.path_field.clear()

    def clear(self):
        """Clear the currently selected image"""
        self.image = None
        self.status_label.setText("No image selected")
        self.preview_btn.setEnabled(False)
        self.path_field.clear()
