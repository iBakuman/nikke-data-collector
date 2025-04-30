"""
Picker extension for page configuration.

This module extends the original picker UI to support designating elements
as page identifiers or interactive elements, and to define transitions between pages.
"""

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QInputDialog,
                               QLabel, QListView, QMainWindow, QMessageBox,
                               QPushButton, QVBoxLayout)

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from picker.designer.main import Ui_MainWindow
from picker.overlay.overlay_manager import OverlayManager
from picker.overlay.overlay_widget import OverlayWidget
from processor.elements import ImageElement, PixelColorElement
from processor.page_config import PageConfigManager

logger = get_logger(__name__)


def _create_dialog_buttons(dialog, ok_button_text="OK", ok_callback=None, cancel_callback=None):
    """Create standard dialog buttons.

    Args:
        dialog: The dialog to add buttons to
        ok_button_text: Text for the OK button
        ok_callback: Callback for the OK button
        cancel_callback: Callback for the Cancel button

    Returns:
        QHBoxLayout: The button layout
    """
    button_layout = QHBoxLayout()

    ok_button = QPushButton(ok_button_text)
    if ok_callback:
        ok_button.clicked.connect(ok_callback)

    cancel_button = QPushButton("Cancel")
    if cancel_callback:
        cancel_button.clicked.connect(cancel_callback)
    else:
        cancel_button.clicked.connect(dialog.reject)

    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)

    return button_layout, ok_button, cancel_button


def _create_item_from_element(element, element_id, display_suffix=""):
    """Create a standard item from an element.

    Args:
        element: The element to create an item from
        element_id: The ID of the element
        display_suffix: Optional suffix to add to the display name

    Returns:
        QStandardItem: The created item
    """
    display_name = element.name
    if display_suffix:
        display_name = f"{display_name} {display_suffix}"

    item = QStandardItem(display_name)
    item.setData(element_id, Qt.ItemDataRole.UserRole)
    return item


class MainWindow(QMainWindow):
    """Main window for managing page configurations."""

    def __init__(
            self, config_manager: PageConfigManager,
            window_capturer: WindowCapturer
    ):
        """Initialize the page config window.

        Args:
            config_manager: The page configuration manager
            window_capturer: Window capturer for screenshots
        """
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.config_manager = config_manager
        self.window_capturer = window_capturer
        # Set window properties
        self.setWindowTitle("NIKKE Page Configuration")
        self.resize(1200, 800)
        # Set up overlay manager
        self.overlay_widget = OverlayWidget(window_capturer.window_manager)
        self.overlay_manager = OverlayManager(self.overlay_widget, self.window_capturer)
        # Connect overlay signals
        self.overlay_manager.capture_completed.connect(self._on_capture_completed)
        self.overlay_manager.capture_cancelled.connect(self._on_capture_cancelled)
        # Track current element creation
        self.current_element_name: Optional[str] = None
        self.current_page_id: Optional[str] = None

        # Initialize UI
        self._init_ui()
        self._load_pages()
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    def _init_ui(self):
        """Initialize the dialog UI."""
        # Create central widget
        self.page_model = QStandardItemModel()
        self.page_model.setHorizontalHeaderLabels(["Page"])
        self.ui.page_tree.setModel(self.page_model)
        self.ui.page_tree.selectionModel().selectionChanged.connect(self._on_page_selected)

        self.ui.btnAddPage.clicked.connect(self._add_page)
        self.identifier_model = QStandardItemModel()
        self.ui.identifier_list = QListView()
        self.ui.identifier_list.setModel(self.identifier_model)

        self.ui.btnAddIdentifer.clicked.connect(self._add_identifier)
        self.ui.btnRemoveIdentifier.clicked.connect(self._remove_identifier)

        self.interactive_model = QStandardItemModel()
        self.ui.interactive_list.setModel(self.interactive_model)

        # Interactive buttons
        self.ui.btnAddInteractive.clicked.connect(self._add_interactive)
        self.ui.btnRemoveInteractive.clicked.connect(self._remove_interactive)
        # Transitions
        self.transition_model = QStandardItemModel()
        self.transition_model.setHorizontalHeaderLabels(["Element", "Target Page"])
        self.ui.transition_tree.setModel(self.transition_model)

        self.ui.btnAddTransition.clicked.connect(self._add_transition)
        self.ui.btnRemoveTransition.clicked.connect(self._remove_transition)

        self.element_model = QStandardItemModel()
        self.element_model.setHorizontalHeaderLabels(["ID", "Name", "Type"])
        self.ui.element_tree.setModel(self.element_model)

        self.ui.btnNewElement.clicked.connect(self._add_element)

        self.ui.btnSave.clicked.connect(self._save_config)
        self.ui.btnCancel.clicked.connect(self.close)
        # Create status bar
        self.status_bar = self.statusBar()
        # Disable page detail controls initially
        self._set_detail_controls_enabled(False)
        self.ui.btnNewElement.setEnabled(False)

    def _set_detail_controls_enabled(self, enabled: bool):
        """Enable or disable page detail controls.

        Args:
            enabled: Whether to enable the controls
        """
        self.ui.btnAddIdentifer.setEnabled(enabled)
        self.ui.btnRemoveIdentifier.setEnabled(enabled)
        self.ui.btnAddInteractive.setEnabled(enabled)
        self.ui.btnRemoveInteractive.setEnabled(enabled)
        self.ui.btnAddTransition.setEnabled(enabled)
        self.ui.btnRemoveTransition.setEnabled(enabled)
        self.ui.btnNewElement.setEnabled(enabled)

    def _load_pages(self):
        """Load pages from configuration into the tree view."""
        self.page_model.clear()
        self.page_model.setHorizontalHeaderLabels(["Page"])

        for page_id, page in self.config_manager.config.pages.items():
            item = QStandardItem(page.name)
            item.setData(page_id, Qt.ItemDataRole.UserRole)
            self.page_model.appendRow(item)

    def _load_page_elements(self, page_id: str):
        """Load elements for a page into the tree view.

        Args:
            page_id: ID of the page to load elements for
        """
        self.element_model.clear()
        self.element_model.setHorizontalHeaderLabels(["ID", "Name", "Type"])

        page = self.config_manager.config.pages[page_id]

        for element_id, element in page.elements.items():
            id_item = QStandardItem(element_id)
            name_item = QStandardItem(element.name)
            type_item = QStandardItem(element.type)

            self.element_model.appendRow([id_item, name_item, type_item])

    def _on_page_selected(self):
        """Handle page selection changes."""
        indexes = self.ui.page_tree.selectedIndexes()
        if not indexes:
            self._set_detail_controls_enabled(False)
            return

        # Enable controls
        self._set_detail_controls_enabled(True)

        # Get selected page
        page_item = self.page_model.itemFromIndex(indexes[0])
        page_id = page_item.data(Qt.ItemDataRole.UserRole)

        # Load page details
        self._load_page_details(page_id)

        # Load page elements
        self._load_page_elements(page_id)

    def _load_page_details(self, page_id: str):
        """Load details for a page.

        Args:
            page_id: ID of the page to load
        """
        page = self.config_manager.config.pages[page_id]

        # Load identifiers
        self.identifier_model.clear()
        for element_id in page.identifier_element_ids:
            if element_id in page.elements:
                element = page.elements[element_id]
                item = _create_item_from_element(element, element_id)
                self.identifier_model.appendRow(item)

        # Load interactive elements
        self.interactive_model.clear()
        for element_id in page.interactive_element_ids:
            if element_id in page.elements:
                element = page.elements[element_id]
                item = _create_item_from_element(element, element_id)
                self.interactive_model.appendRow(item)

        # Load transitions
        self.transition_model.clear()
        self.transition_model.setHorizontalHeaderLabels(["Element", "Target Page"])
        for transition in page.transitions:
            if transition.element_id in page.elements and transition.target_page in self.config_manager.config.pages:
                element = page.elements[transition.element_id]
                target_page = self.config_manager.config.pages[transition.target_page]

                element_item = _create_item_from_element(element, transition.element_id)
                target_item = QStandardItem(target_page.name)
                target_item.setData(transition.target_page, Qt.ItemDataRole.UserRole)

                self.transition_model.appendRow([element_item, target_item])

    def _get_selected_page_id(self):
        """Get the ID of the selected page.

        Returns:
            str or None: The selected page ID, or None if no page is selected
        """
        indexes = self.ui.page_tree.selectedIndexes()
        if not indexes:
            return None

        page_item = self.page_model.itemFromIndex(indexes[0])
        return page_item.data(Qt.ItemDataRole.UserRole)

    def _get_selected_element_id(self):
        """Get the ID of the selected element.

        Returns:
            str or None: The selected element ID, or None if no element is selected
        """
        indexes = self.ui.element_tree.selectedIndexes()
        if not indexes:
            return None

        return self.element_model.item(indexes[0].row(), 0).text()

    def _add_page(self):
        """Add a new page to the configuration."""
        # Prompt for page ID and name
        page_id, ok = QInputDialog.getText(self, "Add Page", "Page ID:")
        if not ok or not page_id:
            return

        page_name, ok = QInputDialog.getText(self, "Add Page", "Page Name:")
        if not ok or not page_name:
            return

        # Add page to config
        try:
            self.config_manager.add_page(page_id, page_name)

            # Add to tree view
            item = QStandardItem(page_name)
            item.setData(page_id, Qt.ItemDataRole.UserRole)
            self.page_model.appendRow(item)

            # Show status message
            self.status_bar.showMessage(f"Added page: {page_name}", 3000)

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _add_element(self):
        """Add a new element to the current page using overlay capture."""
        # Check if a page is selected
        page_id = self._get_selected_page_id()
        if not page_id:
            QMessageBox.warning(self, "Warning", "Please select a page first")
            return

        # Get available strategy types
        strategy_infos = self.overlay_manager.get_strategy_infos()
        if not strategy_infos:
            QMessageBox.warning(self, "Warning", "No element types available")
            return

        # Prepare display items for selection dialog
        display_names = [info.display_name for info in strategy_infos]

        # Show strategy selection dialog
        selected_index, ok = QInputDialog.getItem(
            self, "Select Element Type",
            "Select the type of element to create:",
            display_names,
            0,  # Default to first item
            False  # Not editable
        )

        if not ok:
            return

        # Find selected strategy info
        selected_index_pos = display_names.index(selected_index)
        if selected_index_pos < 0 or selected_index_pos >= len(strategy_infos):
            QMessageBox.critical(self, "Error", "Invalid element type selection")
            return

        strategy_info = strategy_infos[selected_index_pos]

        # Get element name
        element_name, ok = QInputDialog.getText(
            self, "Add Element", "Element Name:"
        )
        if not ok or not element_name:
            return

        # Try to capture target window
        capture_result = self.window_capturer.capture_window()
        if not capture_result:
            QMessageBox.critical(self, "Error", "Failed to capture target window")
            return

        # Store current element creation context
        self.current_element_name = element_name
        self.current_page_id = page_id

        # Update status
        self.status_bar.showMessage(f"Capturing {strategy_info.display_name}...")

        # Start capture process
        try:
            result = self.overlay_manager.start_capture(strategy_info.type_id)
            if result is None:
                # Capture was cancelled
                self.status_bar.showMessage("Element capture cancelled", 3000)
                self.current_element_name = None
                self.current_page_id = None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start capture: {e}")
            self.current_element_name = None
            self.current_page_id = None

    def _on_capture_completed(self, strategy_type: str, capture_data: Any):
        """Handle element capture completion.

        Args:
            strategy_type: Type of the capture strategy
            capture_data: Captured element data
        """
        # Check if we have a valid capture context
        if not self.current_element_name or not self.current_page_id:
            logger.warning("Received capture completion but no active element creation context")
            return

        # Check if capture data is valid
        if not capture_data:
            QMessageBox.critical(self, "Error", "No capture data received")
            self.current_element_name = None
            self.current_page_id = None
            return

        try:
            # Create element based on strategy type
            element = None

            if strategy_type == "pixel_color":
                # Check for required data
                if "points_colors" not in capture_data:
                    raise ValueError("Missing points_colors in capture data")

                # Create pixel color element
                element = PixelColorElement(
                    name=self.current_element_name,
                    points_colors=capture_data["points_colors"],
                    match_all=capture_data.get("match_all", True)
                )

            elif strategy_type == "image_element":
                # Check for required data
                if "region" not in capture_data:
                    raise ValueError("Missing region in capture data")
                if "image" not in capture_data:
                    raise ValueError("Missing image in capture data")

                # Create image element
                element = ImageElement(
                    name=self.current_element_name,
                    region=capture_data["region"],
                    target_image=capture_data["image"],
                    threshold=capture_data.get("threshold", 0.8)
                )
            else:
                raise ValueError(f"Unsupported strategy type: {strategy_type}")

            if element:
                # Add element to configuration
                element_id = self.config_manager.add_element(
                    self.current_page_id, element
                )

                # Update UI
                self._load_page_elements(self.current_page_id)
                self.status_bar.showMessage(
                    f"Added {element.name} to page", 3000
                )
            else:
                raise ValueError("Failed to create element")

        except Exception as e:
            logger.exception("Failed to create element")
            QMessageBox.critical(self, "Error", f"Failed to create element: {e}")

        # Clear current element creation context
        self.current_element_name = None
        self.current_page_id = None

    def _on_capture_cancelled(self):
        """Handle element capture cancellation."""
        self.status_bar.showMessage("Element capture cancelled", 3000)
        self.current_element_name = None
        self.current_page_id = None

    def _add_identifier(self):
        """Add an identifier element to the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected element
        element_id = self._get_selected_element_id()
        if not element_id:
            QMessageBox.warning(self, "Warning", "Please select an element first")
            return

        # Add to page
        try:
            self.config_manager.add_page_identifier(page_id, element_id)

            # Refresh page details
            self._load_page_details(page_id)

            # Show status message
            self.status_bar.showMessage(f"Added element as page identifier", 3000)

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _remove_identifier(self):
        """Remove an identifier element from the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected identifier
        id_indexes = self.ui.identifier_list.selectedIndexes()
        if not id_indexes:
            QMessageBox.warning(self, "Warning", "Please select an identifier first")
            return

        id_item = self.identifier_model.itemFromIndex(id_indexes[0])
        element_id = id_item.data(Qt.ItemDataRole.UserRole)

        # Remove from page
        page = self.config_manager.config.pages[page_id]
        page.identifier_element_ids.remove(element_id)

        # Refresh page details
        self._load_page_details(page_id)

        # Show status message
        self.status_bar.showMessage(f"Removed element from page identifiers", 3000)

    def _add_interactive(self):
        """Add an interactive element to the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected element
        element_id = self._get_selected_element_id()
        if not element_id:
            QMessageBox.warning(self, "Warning", "Please select an element first")
            return

        # Add to page
        try:
            self.config_manager.add_interactive_element(page_id, element_id)

            # Refresh page details
            self._load_page_details(page_id)

            # Show status message
            self.status_bar.showMessage(f"Added element as interactive element", 3000)

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _remove_interactive(self):
        """Remove an interactive element from the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected interactive element
        int_indexes = self.ui.interactive_list.selectedIndexes()
        if not int_indexes:
            QMessageBox.warning(self, "Warning", "Please select an interactive element first")
            return

        int_item = self.interactive_model.itemFromIndex(int_indexes[0])
        element_id = int_item.data(Qt.ItemDataRole.UserRole)

        # Remove from page
        page = self.config_manager.config.pages[page_id]
        page.interactive_element_ids.remove(element_id)

        # Refresh page details
        self._load_page_details(page_id)

        # Show status message
        self.status_bar.showMessage(f"Removed element from interactive elements", 3000)

    def _add_transition(self):
        """Add a transition to the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected element
        element_id = self._get_selected_element_id()
        if not element_id:
            QMessageBox.warning(self, "Warning", "Please select an element first")
            return

        # Get target page
        target_dialog = TargetPageDialog(self.config_manager, self)
        if target_dialog.exec():
            target_page_id = target_dialog.selected_page_id
            confirmation_ids = target_dialog.confirmation_element_ids

            # Add to page
            try:
                self.config_manager.add_transition(
                    page_id, element_id, target_page_id, confirmation_ids
                )

                # Refresh page details
                self._load_page_details(page_id)

                # Show status message
                target_page = self.config_manager.config.pages[target_page_id]
                self.status_bar.showMessage(
                    f"Added transition to {target_page.name}", 3000
                )

            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _remove_transition(self):
        """Remove a transition from the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected transition
        trans_indexes = self.ui.transition_tree.selectedIndexes()
        if not trans_indexes:
            QMessageBox.warning(self, "Warning", "Please select a transition first")
            return

        element_item = self.transition_model.item(trans_indexes[0].row(), 0)
        target_item = self.transition_model.item(trans_indexes[0].row(), 1)

        element_id = element_item.data(Qt.ItemDataRole.UserRole)
        target_page_id = target_item.data(Qt.ItemDataRole.UserRole)

        # Remove from page
        page = self.config_manager.config.pages[page_id]

        # Find and remove matching transition
        for i, transition in enumerate(page.transitions):
            if transition.element_id == element_id and transition.target_page == target_page_id:
                del page.transitions[i]
                break

        # Refresh page details
        self._load_page_details(page_id)

        # Show status message
        self.status_bar.showMessage(f"Removed transition", 3000)

    def _save_config(self):
        """Save the configuration."""
        try:
            self.config_manager.save_config()
            self.status_bar.showMessage("Configuration saved successfully", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def closeEvent(self, event):
        """Handle window close event.

        Args:
            event: Close event
        """
        # Ask for confirmation if there are unsaved changes
        # TODO: Track changes to detect unsaved modifications

        reply = QMessageBox.question(
            self, "Save Changes?",
            "Do you want to save changes before closing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Save:
            try:
                self.config_manager.save_config()
                event.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")
                event.ignore()
        elif reply == QMessageBox.StandardButton.Cancel:
            event.ignore()
        else:
            event.accept()


class TargetPageDialog(QDialog):
    """Dialog for selecting a target page for a transition."""

    def __init__(self, config_manager: PageConfigManager, parent=None):
        """Initialize the target page dialog.

        Args:
            config_manager: The page configuration manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.selected_page_id = None
        self.confirmation_element_ids = []

        self.setWindowTitle("Select Target Page")
        self.resize(400, 500)

        self._init_ui()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Target page selection
        layout.addWidget(QLabel("Target Page:"))

        self.page_combo = QComboBox()
        for page_id, page in self.config_manager.config.pages.items():
            self.page_combo.addItem(page.name, page_id)
        layout.addWidget(self.page_combo)

        # Confirmation elements
        layout.addWidget(QLabel("Confirmation Elements (Optional):"))

        self.element_model = QStandardItemModel()
        self.element_list = QListView()
        self.element_list.setModel(self.element_model)
        self.element_list.setSelectionMode(QListView.SelectionMode.MultiSelection)
        layout.addWidget(self.element_list)

        # Update elements when page selection changes
        self.page_combo.currentIndexChanged.connect(self._update_elements)
        self._update_elements()

        # Buttons
        button_layout, self.ok_button, self.cancel_button = _create_dialog_buttons(
            self, "OK", self._on_ok
        )
        layout.addLayout(button_layout)

    def _update_elements(self):
        """Update the element list based on the selected page."""
        self.element_model.clear()

        # Get selected page
        page_id = self.page_combo.currentData()
        if not page_id:
            return

        # Add elements from the page
        page = self.config_manager.config.pages[page_id]

        # Add identifier elements
        for element_id in page.identifier_element_ids:
            if element_id in page.elements:
                element = page.elements[element_id]
                item = _create_item_from_element(element, element_id, "(Identifier)")
                self.element_model.appendRow(item)

    def _on_ok(self):
        """Handle OK button click."""
        # Get selected page
        self.selected_page_id = self.page_combo.currentData()

        # Get selected confirmation elements
        self.confirmation_element_ids = []
        for index in self.element_list.selectedIndexes():
            item = self.element_model.itemFromIndex(index)
            element_id = item.data(Qt.ItemDataRole.UserRole)
            self.confirmation_element_ids.append(element_id)

        self.accept()


def run_config_window(config_path, window_capturer):
    """Run the page configuration window.

    Args:
        config_path: Path to configuration file
        window_capturer: Window capturer instance

    Returns:
        int: Application exit code
    """
    import sys

    from PySide6.QtWidgets import QApplication

    # Create config manager
    config_manager = PageConfigManager(config_path)

    # Create application
    app = QApplication.instance() or QApplication(sys.argv)

    # Create and show window
    window = MainWindow(config_manager, window_capturer)
    window.show()

    # Run application
    return app.exec()
