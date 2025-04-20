import os

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLineEdit,
                               QPushButton, QWidget)


class PathSelector(QWidget):
    """
    Widget for selecting a directory path.
    Contains a text field showing the selected path and a browse button.
    """
    pathChanged = Signal(str)

    def __init__(self, default_path="", parent=None):
        """Initialize with default path and parent widget."""
        super().__init__(parent)

        # Default to user's documents folder if not specified
        if not default_path:
            default_path = os.path.expanduser("~")

        self._path = default_path

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Path display field with system font
        self.path_field = QLineEdit(self)
        self.path_field.setText(self._path)
        self.path_field.setReadOnly(True)  # Make read-only to prevent direct editing
        layout.addWidget(self.path_field)

        # Browse button with system font
        self.browse_btn = QPushButton("Browse...", self)
        self.browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self.browse_btn)

    def _on_browse(self):
        """Open directory selection dialog when browse button is clicked."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Data Storage Directory",
            self._path,
            QFileDialog.Option.ShowDirsOnly
        )

        # Update path if user selected a directory (not canceled)
        if path:
            self.set_path(path)

    def get_path(self):
        """Get the currently selected path."""
        return self._path

    def set_path(self, path):
        """Set the path programmatically."""
        if os.path.isdir(path):
            self._path = path
            self.path_field.setText(path)
            self.pathChanged.emit(path)
