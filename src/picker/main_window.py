"""Main window for the picker application."""

import os
from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QToolBar

from picker.picker_page_config import PageConfigButton


class PickerMainWindow(QMainWindow):
    """Main window for the picker application."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("NIKKE Picker")
        self.resize(1200, 800)
        
        # Initialize UI
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        # Create toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        
        # Add page config button
        config_dir = Path("data") / "configs"
        os.makedirs(config_dir, exist_ok=True)
        config_path = config_dir / "pages.json"
        
        self.page_config_button = PageConfigButton(str(config_path), self)
        self.toolbar.addWidget(self.page_config_button)
