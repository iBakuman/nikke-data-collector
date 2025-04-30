"""
Integration example showing how to combine the overlay system with page configuration.

This module demonstrates how to:
1. Capture UI elements using the overlay system
2. Configure those elements as page identifiers or interactive elements
3. Define page transitions for automation
"""
import sys
from typing import Dict, Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                               QPushButton, QToolBar, QVBoxLayout, QWidget)

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from collector.window_manager import WindowManager
from domain.pixel_element import PixelColorElementEntity
from picker.data import get_page_config_path
from picker.overlay.overlay_manager import OverlayManager
from picker.overlay.overlay_widget import OverlayWidget
from picker.picker_page_config import PageConfigDialog
from processor.page_config import PageConfigManager

logger = get_logger(__name__)


class IntegrationExample(QMainWindow):
    """Example application demonstrating overlay and page configuration integration."""
    
    def __init__(self):
        """Initialize the integration example application."""
        super().__init__()
        self.setWindowTitle("Overlay and Page Config Integration")
        self.resize(1000, 700)
        
        # Initialize components
        self._init_components()
        self._init_ui()
        self._connect_signals()

    def _init_components(self):
        """Initialize internal components."""
        # Create window capturer
        self.window_manager = WindowManager("nikke.exe")
        self.window_capturer = WindowCapturer(self.window_manager)
        
        # Create overlay widget
        self.overlay = OverlayWidget(self.window_manager)
        
        # Create overlay manager
        self.overlay_manager = OverlayManager(self.overlay, self.window_capturer)
        
        self.page_config_manager = PageConfigManager(get_page_config_path())
        
        # Storage for captured elements
        self.captured_elements: Dict[str, any] = {}
        self.current_element_id: Optional[str] = None

    def _init_ui(self):
        """Initialize the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Capture action
        capture_menu = toolbar.addAction("Capture")
        capture_menu.setMenu(self._create_capture_menu())

        # Configure action
        configure_action = QAction("Configure Pages", self)
        configure_action.triggered.connect(self._show_page_config)
        toolbar.addAction(configure_action)
        
        # Element capture buttons section
        capture_layout = QHBoxLayout()
        
        # Pixel color capture button
        self.color_capture_button = QPushButton("Capture Pixel Color")
        self.color_capture_button.clicked.connect(self._start_color_capture)
        capture_layout.addWidget(self.color_capture_button)
        
        # Image element capture button
        self.image_capture_button = QPushButton("Capture Image Element")
        self.image_capture_button.clicked.connect(self._start_image_capture)
        capture_layout.addWidget(self.image_capture_button)
        
        # Add to main layout
        main_layout.addLayout(capture_layout)
        
        # Element configuration buttons section
        config_layout = QHBoxLayout()
        
        # Add as page identifier button
        self.add_identifier_button = QPushButton("Add as Page Identifier")
        self.add_identifier_button.clicked.connect(self._add_as_identifier)
        self.add_identifier_button.setEnabled(False)
        config_layout.addWidget(self.add_identifier_button)
        
        # Add as interactive element button
        self.add_interactive_button = QPushButton("Add as Interactive Element")
        self.add_interactive_button.clicked.connect(self._add_as_interactive)
        self.add_interactive_button.setEnabled(False)
        config_layout.addWidget(self.add_interactive_button)
        
        # Define page transition button
        self.add_transition_button = QPushButton("Define Page Transition")
        self.add_transition_button.clicked.connect(self._define_transition)
        self.add_transition_button.setEnabled(False)
        config_layout.addWidget(self.add_transition_button)
        
        # Add to main layout
        main_layout.addLayout(config_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")

    def _create_capture_menu(self):
        """Create capture menu for the toolbar.
        
        Returns:
            QMenu: The capture menu
        """
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        pixel_action = QAction("Capture Pixel Color", self)
        pixel_action.triggered.connect(self._start_color_capture)
        menu.addAction(pixel_action)
        
        image_action = QAction("Capture Image Element", self)
        image_action.triggered.connect(self._start_image_capture)
        menu.addAction(image_action)
        
        return menu

    def _connect_signals(self):
        """Connect signals between components."""
        # Connect overlay manager signals
        self.overlay_manager.capture_completed.connect(self._on_capture_completed)
        self.overlay_manager.capture_cancelled.connect(self._on_capture_cancelled)

    def _start_color_capture(self):
        """Start pixel color capture process."""
        self.statusBar().showMessage("Starting pixel color capture...")
        
        # Get unique element ID
        self.current_element_id = f"pixel_{len(self.captured_elements) + 1}"
        
        # Start capture
        result = self.overlay_manager.start_capture("pixel_color")
        
        # Display overlay
        if not self.overlay.isVisible():
            self.overlay.show()

    def _start_image_capture(self):
        """Start image element capture process."""
        self.statusBar().showMessage("Starting image element capture...")
        
        # Get unique element ID
        self.current_element_id = f"image_{len(self.captured_elements) + 1}"
        
        # Start capture
        result = self.overlay_manager.start_capture("image_element")
        
        # Display overlay
        if not self.overlay.isVisible():
            self.overlay.show()

    def _on_capture_completed(self, strategy_type: str, result: any):
        """Handle capture completion.
        
        Args:
            strategy_type: Type of capture strategy
            result: Capture result
        """
        if not self.current_element_id:
            return
            
        # Store captured element
        self.captured_elements[self.current_element_id] = result
        
        # Update UI
        self.statusBar().showMessage(f"Captured {strategy_type} element: {self.current_element_id}")
        
        # Enable configuration buttons
        self.add_identifier_button.setEnabled(True)
        self.add_interactive_button.setEnabled(True)
        self.add_transition_button.setEnabled(True)

    def _on_capture_cancelled(self):
        """Handle capture cancellation."""
        self.statusBar().showMessage("Capture cancelled")
        self.current_element_id = None
        
        # Disable configuration buttons
        self.add_identifier_button.setEnabled(False)
        self.add_interactive_button.setEnabled(False)
        self.add_transition_button.setEnabled(False)

    def _show_page_config(self):
        """Show the page configuration dialog."""
        dialog = PageConfigDialog(self.page_config_manager, self)
        dialog.exec()

    def _add_as_identifier(self):
        """Add the current element as a page identifier."""
        if not self.current_element_id or self.current_element_id not in self.captured_elements:
            self.statusBar().showMessage("No current element to add")
            return
            
        # Get current element
        element = self.captured_elements[self.current_element_id]
        
        # Get current page ID (hardcoded for example)
        current_page_id = "main_page"
        
        try:
            # Add element to page config
            element_entity = None
            
            # Handle different element types
            if isinstance(element, PixelColorElementEntity):
                element_entity = element
                element.name = f"Identifier_{self.current_element_id}"
                
            if element_entity:
                # Register element with page config
                self.page_config_manager.add_element(current_page_id, element_entity)
                
                # Add as identifier
                self.page_config_manager.add_page_identifier(current_page_id, self.current_element_id)
                
                self.statusBar().showMessage(f"Added {self.current_element_id} as page identifier")
            else:
                self.statusBar().showMessage("Unsupported element type")
                
        except ValueError as e:
            self.statusBar().showMessage(f"Error: {e}")

    def _add_as_interactive(self):
        """Add the current element as an interactive element."""
        if not self.current_element_id or self.current_element_id not in self.captured_elements:
            self.statusBar().showMessage("No current element to add")
            return
            
        # Get current element
        element = self.captured_elements[self.current_element_id]
        
        # Get current page ID (hardcoded for example)
        current_page_id = "main_page"
        
        try:
            # Add element to page config
            element_entity = None
            
            # Handle different element types
            if isinstance(element, PixelColorElementEntity):
                element_entity = element
                element.name = f"Interactive_{self.current_element_id}"
                
            if element_entity:
                # Register element with page config
                self.page_config_manager.add_element(current_page_id, element_entity)
                
                # Add as interactive element
                self.page_config_manager.add_interactive_element(current_page_id, self.current_element_id)
                
                self.statusBar().showMessage(f"Added {self.current_element_id} as interactive element")
            else:
                self.statusBar().showMessage("Unsupported element type")
                
        except ValueError as e:
            self.statusBar().showMessage(f"Error: {e}")

    def _define_transition(self):
        """Define a page transition using the current element."""
        if not self.current_element_id or self.current_element_id not in self.captured_elements:
            self.statusBar().showMessage("No current element to use")
            return
            
        # Get current page ID (hardcoded for example)
        current_page_id = "main_page"
        
        # Get target page ID (hardcoded for example)
        target_page_id = "second_page"
        
        try:
            # Add transition
            self.page_config_manager.add_transition(
                current_page_id, 
                self.current_element_id,
                target_page_id
            )
            
            self.statusBar().showMessage(f"Added transition from {current_page_id} to {target_page_id}")
                
        except ValueError as e:
            self.statusBar().showMessage(f"Error: {e}")

    def closeEvent(self, event):
        """Handle window close event.
        
        Args:
            event: Close event
        """
        # Hide overlay
        if self.overlay and self.overlay.isVisible():
            self.overlay.hide()
            
        # Save page configuration
        try:
            self.page_config_manager.save_config()
        except Exception as e:
            logger.error(f"Failed to save page configuration: {e}")
            
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegrationExample()
    window.show()
    sys.exit(app.exec()) 
