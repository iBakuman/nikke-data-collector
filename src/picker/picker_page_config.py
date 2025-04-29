"""
Picker extension for page configuration.

This module extends the original picker UI to support designating elements
as page identifiers or interactive elements, and to define transitions between pages.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QInputDialog,
                               QLabel, QLineEdit, QListView, QMessageBox,
                               QPushButton, QTreeView, QVBoxLayout)

from collector.logging_config import get_logger
from processor.page_config import ElementTypeRegistry, PageConfigManager

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


class ElementCreationDialog(QDialog):
    """Dialog for creating a new element."""

    def __init__(self, page_id: str, parent=None):
        """Initialize the element creation dialog.

        Args:
            page_id: ID of the page to add the element to
            parent: Parent widget
        """
        super().__init__(parent)
        self.page_id = page_id
        self.element = None

        self.setWindowTitle("Create Element")
        self.resize(400, 300)

        self._init_ui()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Element type selection
        layout.addWidget(QLabel("Element Type:"))

        self.type_combo = QComboBox()
        for type_id, handler in ElementTypeRegistry.get_all_handlers().items():
            self.type_combo.addItem(type_id, type_id)
        layout.addWidget(self.type_combo)

        # Element name input
        layout.addWidget(QLabel("Element Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Buttons
        button_layout, self.create_button, self.cancel_button = _create_dialog_buttons(
            self, "Create", self._on_create
        )
        layout.addLayout(button_layout)

    def _on_create(self):
        """Handle create button click."""
        element_type = self.type_combo.currentData()
        element_name = self.name_input.text()

        if not element_name:
            QMessageBox.warning(self, "Warning", "Please enter an element name")
            return

        # Get handler for element type
        handler = ElementTypeRegistry.get_handler(element_type)
        if not handler:
            QMessageBox.critical(self, "Error", f"No handler found for element type: {element_type}")
            return

        # Create element
        self.element = handler.create_element_ui(self)

        if self.element:
            # Set element name
            self.element.name = element_name
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Element creation cancelled or failed")


class PageConfigDialog(QDialog):
    """Dialog for managing page configurations."""

    def __init__(self, config_manager: PageConfigManager, parent=None):
        """Initialize the page config dialog.

        Args:
            config_manager: The page configuration manager
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Page Configuration")
        self.resize(800, 600)

        self._init_ui()
        self._load_pages()

    def _init_ui(self):
        """Initialize the dialog UI."""
        # Main layout
        main_layout = QHBoxLayout(self)

        # Left side - Pages
        page_layout = QVBoxLayout()
        page_layout.addWidget(QLabel("Pages:"))

        # Page tree view
        self.page_model = QStandardItemModel()
        self.page_model.setHorizontalHeaderLabels(["Page"])
        self.page_tree = QTreeView()
        self.page_tree.setModel(self.page_model)
        self.page_tree.selectionModel().selectionChanged.connect(self._on_page_selected)
        page_layout.addWidget(self.page_tree)

        # Page buttons
        page_button_layout = QHBoxLayout()
        self.add_page_button = QPushButton("Add Page")
        self.add_page_button.clicked.connect(self._add_page)
        page_button_layout.addWidget(self.add_page_button)

        page_layout.addLayout(page_button_layout)

        # Middle - Page details
        detail_layout = QVBoxLayout()

        # Page identifiers
        detail_layout.addWidget(QLabel("Page Identifiers:"))
        self.identifier_model = QStandardItemModel()
        self.identifier_list = QListView()
        self.identifier_list.setModel(self.identifier_model)
        detail_layout.addWidget(self.identifier_list)

        # Identifier buttons
        id_button_layout = QHBoxLayout()
        self.add_identifier_button = QPushButton("Add Identifier")
        self.add_identifier_button.clicked.connect(self._add_identifier)
        self.remove_identifier_button = QPushButton("Remove Identifier")
        self.remove_identifier_button.clicked.connect(self._remove_identifier)
        id_button_layout.addWidget(self.add_identifier_button)
        id_button_layout.addWidget(self.remove_identifier_button)
        detail_layout.addLayout(id_button_layout)

        # Interactive elements
        detail_layout.addWidget(QLabel("Interactive Elements:"))
        self.interactive_model = QStandardItemModel()
        self.interactive_list = QListView()
        self.interactive_list.setModel(self.interactive_model)
        detail_layout.addWidget(self.interactive_list)

        # Interactive buttons
        interact_button_layout = QHBoxLayout()
        self.add_interactive_button = QPushButton("Add Interactive")
        self.add_interactive_button.clicked.connect(self._add_interactive)
        self.remove_interactive_button = QPushButton("Remove Interactive")
        self.remove_interactive_button.clicked.connect(self._remove_interactive)
        interact_button_layout.addWidget(self.add_interactive_button)
        interact_button_layout.addWidget(self.remove_interactive_button)
        detail_layout.addLayout(interact_button_layout)

        # Transitions
        detail_layout.addWidget(QLabel("Transitions:"))
        self.transition_model = QStandardItemModel()
        self.transition_model.setHorizontalHeaderLabels(["Element", "Target Page"])
        self.transition_tree = QTreeView()
        self.transition_tree.setModel(self.transition_model)
        detail_layout.addWidget(self.transition_tree)

        # Transition buttons
        transition_button_layout = QHBoxLayout()
        self.add_transition_button = QPushButton("Add Transition")
        self.add_transition_button.clicked.connect(self._add_transition)
        self.remove_transition_button = QPushButton("Remove Transition")
        self.remove_transition_button.clicked.connect(self._remove_transition)
        transition_button_layout.addWidget(self.add_transition_button)
        transition_button_layout.addWidget(self.remove_transition_button)
        detail_layout.addLayout(transition_button_layout)

        # Right side - Elements for current page
        element_layout = QVBoxLayout()
        element_layout.addWidget(QLabel("Page Elements:"))

        # Element tree view
        self.element_model = QStandardItemModel()
        self.element_model.setHorizontalHeaderLabels(["ID", "Name", "Type"])
        self.element_tree = QTreeView()
        self.element_tree.setModel(self.element_model)
        element_layout.addWidget(self.element_tree)

        # Element buttons
        element_button_layout = QHBoxLayout()
        self.add_element_button = QPushButton("New Element")
        self.add_element_button.clicked.connect(self._add_element)
        element_button_layout.addWidget(self.add_element_button)
        element_layout.addLayout(element_button_layout)

        # Dialog buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_config)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        # Add layouts to main layout
        main_layout.addLayout(page_layout, 1)
        main_layout.addLayout(detail_layout, 2)
        main_layout.addLayout(element_layout, 1)

        # Add button layout at the bottom
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_layout)
        outer_layout.addLayout(button_layout)
        self.setLayout(outer_layout)

        # Disable page detail controls initially
        self._set_detail_controls_enabled(False)
        self.add_element_button.setEnabled(False)

    def _set_detail_controls_enabled(self, enabled: bool):
        """Enable or disable page detail controls.

        Args:
            enabled: Whether to enable the controls
        """
        self.add_identifier_button.setEnabled(enabled)
        self.remove_identifier_button.setEnabled(enabled)
        self.add_interactive_button.setEnabled(enabled)
        self.remove_interactive_button.setEnabled(enabled)
        self.add_transition_button.setEnabled(enabled)
        self.remove_transition_button.setEnabled(enabled)
        self.add_element_button.setEnabled(enabled)

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
        indexes = self.page_tree.selectedIndexes()
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
        indexes = self.page_tree.selectedIndexes()
        if not indexes:
            return None

        page_item = self.page_model.itemFromIndex(indexes[0])
        return page_item.data(Qt.ItemDataRole.UserRole)

    def _get_selected_element_id(self):
        """Get the ID of the selected element.

        Returns:
            str or None: The selected element ID, or None if no element is selected
        """
        indexes = self.element_tree.selectedIndexes()
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

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _add_element(self):
        """Add a new element to the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Show element creation dialog
        dialog = ElementCreationDialog(page_id, self)
        if dialog.exec():
            element = dialog.element
            if element:
                try:
                    # Add element to page
                    element_id = self.config_manager.add_element(page_id, element)

                    # Refresh page elements
                    self._load_page_elements(page_id)

                except ValueError as e:
                    QMessageBox.critical(self, "Error", str(e))

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

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _remove_identifier(self):
        """Remove an identifier element from the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected identifier
        id_indexes = self.identifier_list.selectedIndexes()
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

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _remove_interactive(self):
        """Remove an interactive element from the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected interactive element
        int_indexes = self.interactive_list.selectedIndexes()
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

            except ValueError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _remove_transition(self):
        """Remove a transition from the current page."""
        # Get selected page
        page_id = self._get_selected_page_id()
        if not page_id:
            return

        # Get selected transition
        trans_indexes = self.transition_tree.selectedIndexes()
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

    def _save_config(self):
        """Save the configuration and close the dialog."""
        try:
            self.config_manager.save_config()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")


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


# Button to add to the PickerApp
class PageConfigButton(QPushButton):
    """Button for showing the page configuration dialog."""

    def __init__(self, config_path: str, parent=None):
        """Initialize the page config button.

        Args:
            config_path: Path to the JSON configuration file
            parent: Parent widget
        """
        super().__init__("Page Config", parent)
        self.config_manager = PageConfigManager(config_path)
        self.clicked.connect(self._show_page_config_dialog)

    def _show_page_config_dialog(self):
        """Show the page configuration dialog."""
        dialog = PageConfigDialog(self.config_manager, self.parent())
        dialog.exec()
