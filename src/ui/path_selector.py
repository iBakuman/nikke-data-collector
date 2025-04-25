import os
import subprocess

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLineEdit,
                               QPushButton, QVBoxLayout, QWidget)

from collector.logging_config import get_logger

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

        # Normalize path to ensure correct path separators
        self._path = os.path.normpath(default_path)

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Path display field with system font (first row)
        self.path_field = QLineEdit(self)
        self.path_field.setText(self._path)
        self.path_field.setReadOnly(True)  # Make read-only to prevent direct editing
        main_layout.addWidget(self.path_field)

        # Buttons layout (second row)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(buttons_layout)

        # Browse button
        self.browse_btn = QPushButton("Browse", self)
        self.browse_btn.clicked.connect(self._on_browse)
        buttons_layout.addWidget(self.browse_btn)

        # Show in Explorer button
        self.explore_btn = QPushButton("Show in Explorer", self)
        self.explore_btn.clicked.connect(self._on_show_in_explorer)
        buttons_layout.addWidget(self.explore_btn)

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
            # Normalize path to ensure correct path separators for Windows
            normalized_path = os.path.normpath(self._path)

            # Use subprocess to open the path in Explorer
            subprocess.Popen(f'explorer "{normalized_path}"')
            logger.info(f"Opened explorer for path: {normalized_path}")
        except Exception as e:
            logger.error(f"Error opening explorer: {e}")

    def get_path(self):
        """Get the currently selected path."""
        return self._path

    def set_path(self, path):
        """Set the path programmatically."""
        # Normalize path to ensure correct path separators
        normalized_path = os.path.normpath(path)

        if os.path.isdir(normalized_path):
            self._path = normalized_path
            self.path_field.setText(normalized_path)
            self._update_button_state()
            self.pathChanged.emit(normalized_path)
