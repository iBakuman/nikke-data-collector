import os
import subprocess

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLineEdit,
                               QPushButton, QWidget)

from nikke_arena.logging_config import get_logger

logger = get_logger(__name__)

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

        # Show in Explorer button
        self.explore_btn = QPushButton("Show in Explorer", self)
        self.explore_btn.clicked.connect(self._on_show_in_explorer)
        layout.addWidget(self.explore_btn)

        # Update initial button state
        self._update_button_state()

    def _update_button_state(self):
        """Update the state of the Show in Explorer button based on path validity"""
        path_exists = self._path and os.path.exists(self._path)
        self.explore_btn.setEnabled(path_exists)

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

    def _on_show_in_explorer(self):
        """Open the currently selected path in Windows Explorer."""
        if not self._path or not os.path.exists(self._path):
            logger.warning(f"Cannot open explorer: Path does not exist - {self._path}")
            return

        try:
            # Use subprocess to open the path in Explorer
            subprocess.Popen(f'explorer "{self._path}"')
            logger.info(f"Opened explorer for path: {self._path}")
        except Exception as e:
            logger.error(f"Error opening explorer: {e}")

    def get_path(self):
        """Get the currently selected path."""
        return self._path

    def set_path(self, path):
        """Set the path programmatically."""
        if os.path.isdir(path):
            self._path = path
            self.path_field.setText(path)
            self._update_button_state()
            self.pathChanged.emit(path)
