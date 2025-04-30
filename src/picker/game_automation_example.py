"""
Game automation example demonstrating a practical workflow.

This module shows how to use the captured elements and page configuration
to create an automated workflow for a game.
"""

import os
import sys
import time
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, QRect, QSize, Qt, Signal
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
                               QPushButton, QTextEdit, QToolBar, QVBoxLayout,
                               QWidget)

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from domain.pixel_element import PixelColorElementEntity
from domain.regions import Point
from picker.overlay.overlay_manager import OverlayManager
from picker.overlay.overlay_widget import OverlayWidget
from picker.picker_page_config import PageConfigDialog
from processor.page_config import ElementTypeRegistry, PageConfigManager
from processor.page_detector import PageDetector

logger = get_logger(__name__)


class GameAutomator(QObject):
    """Handles game automation based on page configuration."""

    # Signals
    page_detected = Signal(str)  # Page ID
    page_action_performed = Signal(str, str)  # Page ID, Action description
    log_message = Signal(str)  # Log message

    def __init__(self, config_manager: PageConfigManager, window_capturer: WindowCapturer):
        """Initialize the game automator.

        Args:
            config_manager: Page configuration manager
            window_capturer: Window capturer for screenshots
        """
        super().__init__()
        self.config_manager = config_manager
        self.window_capturer = window_capturer
        self.page_detector = PageDetector(config_manager.config)
        self.current_page_id: Optional[str] = None

    def detect_current_page(self):
        """Detect the current page based on captured screenshot.

        Returns:
            bool: True if page detection was successful
        """
        # Capture screenshot
        capture_result = self.window_capturer.capture_window()
        if not capture_result:
            self.log_message.emit("Failed to capture window")
            return False

        # Detect page
        detection_result = self.page_detector.detect_page(capture_result.to_pil())

        if detection_result and detection_result.page_id:
            # Check if page is different from current page
            if self.current_page_id != detection_result.page_id:
                self.current_page_id = detection_result.page_id
                page_name = self.config_manager.config.pages[self.current_page_id].name
                self.log_message.emit(f"Detected page: {page_name} ({self.current_page_id})")
                self.page_detected.emit(self.current_page_id)
            return True
        else:
            self.log_message.emit("No page detected")
            return False

    def perform_action(self, element_id: str):
        """Perform action on the specified element.

        Args:
            element_id: ID of the element to interact with

        Returns:
            bool: True if action was performed successfully
        """
        if not self.current_page_id:
            self.log_message.emit("No current page detected")
            return False

        # Get current page
        page = self.config_manager.config.pages[self.current_page_id]

        # Check if element exists on current page
        if element_id not in page.elements:
            self.log_message.emit(f"Element {element_id} not found on current page")
            return False

        # Get element
        element = page.elements[element_id]

        # Check element type and perform action
        if isinstance(element, PixelColorElementEntity):
            # Simulate click on pixel
            point = element.point
            abs_x = int(point.x * point.total_width)
            abs_y = int(point.y * point.total_height)

            # In a real application, this would use pyautogui or similar to click
            self.log_message.emit(f"Clicking at ({abs_x}, {abs_y})")

            # Simulate action delay
            time.sleep(0.5)

            # Check for transition
            for transition in page.transitions:
                if transition.element_id == element_id:
                    target_page_id = transition.target_page
                    target_page = self.config_manager.config.pages[target_page_id]
                    self.log_message.emit(f"Transitioning to {target_page.name} ({target_page_id})")

            self.page_action_performed.emit(self.current_page_id, f"Clicked {element.name}")
            return True
        else:
            self.log_message.emit(f"Unsupported element type: {element.type}")
            return False

    def execute_workflow(self, workflow: List[str]):
        """Execute a predefined workflow of element interactions.

        Args:
            workflow: List of element IDs to interact with in sequence

        Returns:
            bool: True if workflow completed successfully
        """
        self.log_message.emit("Starting workflow execution")

        for element_id in workflow:
            # Detect current page
            if not self.detect_current_page():
                self.log_message.emit(f"Workflow failed: Could not detect page for element {element_id}")
                return False

            # Perform action
            if not self.perform_action(element_id):
                self.log_message.emit(f"Workflow failed: Could not perform action on element {element_id}")
                return False

            # Wait for page transition
            time.sleep(1.0)

        self.log_message.emit("Workflow completed successfully")
        return True


class GameAutomationExample(QMainWindow):
    """Example application demonstrating game automation with overlay and page config."""

    def __init__(self):
        """Initialize the game automation example application."""
        super().__init__()
        self.setWindowTitle("Game Automation Example")
        self.resize(1200, 800)

        # Initialize components
        self._init_components()
        self._init_ui()
        self._connect_signals()

    def _init_components(self):
        """Initialize internal components."""
        # Create window capturer
        self.window_capturer = WindowCapturer()

        # Create overlay widget
        self.overlay = OverlayWidget()

        # Create overlay manager
        self.overlay_manager = OverlayManager(self.overlay, self.window_capturer)

        # Create page config manager
        config_path = os.path.join(os.path.dirname(__file__), "game_pages.json")
        self.page_config_manager = PageConfigManager(config_path)

        # Create game automator
        self.game_automator = GameAutomator(self.page_config_manager, self.window_capturer)

        # Example workflows
        self.workflows = {
            "Daily Login": ["btn_start", "btn_daily_rewards", "btn_claim", "btn_close"],
            "Mission 1": ["btn_mission", "btn_chapter_1", "btn_1_1", "btn_auto_battle", "btn_start"],
            "Collect Resources": ["btn_home", "btn_shop", "btn_free", "btn_claim_all", "btn_close"]
        }

    def _init_ui(self):
        """Initialize the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)

        # Capture action
        configure_action = QAction("Configure Pages", self)
        configure_action.triggered.connect(self._show_page_config)
        toolbar.addAction(configure_action)

        # Detect page button
        self.detect_button = QPushButton("Detect Current Page")
        self.detect_button.clicked.connect(self._detect_current_page)
        left_layout.addWidget(self.detect_button)

        # Current page label
        self.page_label = QLabel("Current page: Not detected")
        left_layout.addWidget(self.page_label)

        # Workflow section
        left_layout.addWidget(QLabel("Workflows:"))

        # Workflow buttons
        for workflow_name in self.workflows:
            button = QPushButton(workflow_name)
            button.clicked.connect(lambda checked, name=workflow_name: self._run_workflow(name))
            left_layout.addWidget(button)

        # Add actions section
        left_layout.addWidget(QLabel("Page Actions:"))

        # Actions panel (will be populated when page is detected)
        self.actions_layout = QVBoxLayout()
        left_layout.addLayout(self.actions_layout)

        # Right panel - Preview and logs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Screenshot preview
        right_layout.addWidget(QLabel("Screenshot Preview:"))
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(640, 360)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #333;")
        right_layout.addWidget(self.preview_label)

        # Log section
        right_layout.addWidget(QLabel("Action Log:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _connect_signals(self):
        """Connect signals between components."""
        # Connect game automator signals
        self.game_automator.page_detected.connect(self._on_page_detected)
        self.game_automator.page_action_performed.connect(self._on_action_performed)
        self.game_automator.log_message.connect(self._on_log_message)

    def _show_page_config(self):
        """Show the page configuration dialog."""
        dialog = PageConfigDialog(self.page_config_manager, self)
        dialog.exec()

    def _detect_current_page(self):
        """Detect the current page."""
        self.statusBar().showMessage("Detecting current page...")

        # Capture screenshot
        capture_result = self.window_capturer.capture_window()
        if not capture_result:
            self._on_log_message("Failed to capture window")
            return

        # Update preview
        pixmap = QPixmap.fromImage(capture_result.to_qimage())
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

        # Detect page
        self.game_automator.detect_current_page()

    def _run_workflow(self, workflow_name: str):
        """Run the specified workflow.

        Args:
            workflow_name: Name of the workflow to run
        """
        if workflow_name not in self.workflows:
            self._on_log_message(f"Workflow '{workflow_name}' not found")
            return

        workflow = self.workflows[workflow_name]

        self.statusBar().showMessage(f"Running workflow: {workflow_name}")
        self._on_log_message(f"Starting workflow: {workflow_name}")

        # Execute workflow (in a real application, this would be in a separate thread)
        self.game_automator.execute_workflow(workflow)

    def _on_page_detected(self, page_id: str):
        """Handle page detection.

        Args:
            page_id: Detected page ID
        """
        # Update UI
        page = self.page_config_manager.config.pages[page_id]
        self.page_label.setText(f"Current page: {page.name} ({page_id})")

        # Clear actions layout
        self._clear_layout(self.actions_layout)

        # Add action buttons for interactive elements
        for element_id in page.interactive_element_ids:
            if element_id in page.elements:
                element = page.elements[element_id]
                button = QPushButton(f"Interact: {element.name}")
                button.clicked.connect(lambda checked, eid=element_id: self._perform_action(eid))
                self.actions_layout.addWidget(button)

    def _perform_action(self, element_id: str):
        """Perform action on the specified element.

        Args:
            element_id: ID of the element to interact with
        """
        self.statusBar().showMessage(f"Performing action on element: {element_id}")
        self.game_automator.perform_action(element_id)

    def _on_action_performed(self, page_id: str, action_description: str):
        """Handle action performance.

        Args:
            page_id: Page ID where action was performed
            action_description: Description of the action
        """
        self.statusBar().showMessage(f"Action performed: {action_description}")

        # Update preview after action
        self._detect_current_page()

    def _on_log_message(self, message: str):
        """Add message to log.

        Args:
            message: Log message
        """
        current_time = time.strftime("%H:%M:%S")
        log_entry = f"[{current_time}] {message}"
        self.log_text.append(log_entry)

    def _clear_layout(self, layout):
        """Clear all widgets from a layout.

        Args:
            layout: Layout to clear
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

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
    window = GameAutomationExample()
    window.show()
    sys.exit(app.exec())
