"""
Example of integrating page configuration into the picker application.

This demonstrates how to add the page configuration button to a picker application.
"""
import os
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QToolBar,
                               QVBoxLayout, QWidget)

from picker.picker_page_config import PageConfigButton


class SimplePickerApp(QMainWindow):
    """Simple picker application with page configuration."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        self.setWindowTitle("Simple Picker with Page Config")
        self.resize(800, 600)
        
        # Initialize UI
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Add a label
        label = QLabel("Simple Picker with Page Configuration")
        layout.addWidget(label)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)
        
        # Add page config button
        config_dir = Path("data") / "configs"
        os.makedirs(config_dir, exist_ok=True)
        config_path = config_dir / "pages.json"
        
        self.page_config_button = PageConfigButton(str(config_path), self)
        self.toolbar.addWidget(self.page_config_button)

if __name__ == "__main__":
    """Run the simple picker application."""
    import sys

    QGuiApplication.setAttribute()
    app = QApplication(sys.argv)
    screen = QGuiApplication.primaryScreen()
    ratio = screen.devicePixelRatio()
    print(ratio)

    picker = SimplePickerApp()
    picker.show()
    
    sys.exit(app.exec()) 
