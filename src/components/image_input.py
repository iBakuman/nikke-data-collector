import io

from PIL import Image
from PySide6.QtCore import QBuffer, QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent, QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from extractor.character_extractor import pil_to_qimage


class SimplePreviewDialog(QDialog):
    """Simple image preview dialog without complex processing"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Preview")
        self.resize(800, 600)

        # Create layout
        layout = QVBoxLayout(self)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create label for image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setWidget(self.image_label)

        # Add scroll area to layout
        layout.addWidget(scroll_area)

        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def set_image(self, pixmap):
        """Set the image to display"""
        if pixmap and not pixmap.isNull():
            self.image_label.setPixmap(pixmap)
            # Adjust window size based on image dimensions
            img_width = pixmap.width()
            img_height = pixmap.height()
            self.resize(min(img_width + 50, 1200), min(img_height + 50, 800))
        else:
            self.image_label.setText("No image to display")


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
        if not self._image:
            return

        try:
            # Create preview dialog
            dialog = SimplePreviewDialog(self)

            # Convert image and set it
            q_image = pil_to_qimage(self._image)
            pixmap = QPixmap.fromImage(q_image)
            dialog.set_image(pixmap)

            # Show dialog
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not show preview: {str(e)}")

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
                try:
                    # Convert QImage to PIL Image directly
                    buffer = QBuffer()
                    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
                    q_image.save(buffer, "PNG")
                    buffer.seek(0)
                    pil_image = Image.open(io.BytesIO(buffer.data().data()))
                    self._set_image(pil_image, "[Pasted from clipboard]")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to process clipboard image: {str(e)}")
            else:
                QMessageBox.warning(self, "Warning", "Clipboard contains an invalid image")
        else:
            QMessageBox.warning(self, "Warning", "No image found in clipboard")

    def _set_image(self, image, source_path=""):
        """Set the image and update the UI"""
        self._image = image

        # Update the UI
        if image:
            # Update status label
            width, height = image.size
            self.status_label.setText(f"Image: {width}x{height} px")

            # Enable preview button
            self.preview_btn.setEnabled(True)

            # Update path field
            self.path_field.setText(source_path)

            # Emit signal
            self.imageChanged.emit(image)
        else:
            self.status_label.setText("No image selected")
            self.preview_btn.setEnabled(False)
            self.path_field.clear()

    def get_image(self):
        """Get the currently selected image"""
        return self._image

    def clear(self):
        """Clear the currently selected image"""
        self._image = None
        self.status_label.setText("No image selected")
        self.preview_btn.setEnabled(False)
        self.path_field.clear()
