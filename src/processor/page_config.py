"""
Page Configuration Module for NIKKE data collection system.

This module provides classes and utilities for storing and loading
page configurations from JSON files. Each page contains identifiers,
interactive elements, and transitions to other pages.
"""
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from dataclass_wizard import JSONWizard
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QVBoxLayout)

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from domain.image_element import ImageElementEntity
from domain.pixel_element import PixelColorElementEntity
from domain.regions import Region
from processor.elements import ImageElement, PixelColorElement, UIElement

logger = get_logger(__name__)


class ElementType(Enum):
    """Type of element for serialization purposes."""
    IMAGE = "image"
    PIXEL_COLOR = "pixel_color"


@dataclass
class ElementConfig(JSONWizard):
    """Configuration for a UI element that can be serialized to/from JSON."""
    id: str
    name: str
    type: str  # ElementType as string
    data: Dict[str, Any]  # Element-specific data


@dataclass
class TransitionConfig(JSONWizard):
    """Configuration for a transition between pages."""
    element_id: str  # ID of the element to click
    target_page: str  # ID of the target page
    confirmation_element_ids: List[str] = field(default_factory=list)  # Elements that should appear on target page


@dataclass
class PageConfig(JSONWizard):
    """Configuration for a page in the game UI."""
    id: str
    name: str
    # Elements owned by this page
    elements: Dict[str, ElementConfig] = field(default_factory=dict)
    identifier_element_ids: List[str] = field(default_factory=list)  # Elements that identify this page
    interactive_element_ids: List[str] = field(default_factory=list)  # Elements that can be interacted with
    transitions: List[TransitionConfig] = field(default_factory=list)  # Transitions to other pages


@dataclass
class GameConfig(JSONWizard):
    """Root configuration for the game UI."""
    pages: Dict[str, PageConfig] = field(default_factory=dict)


class ElementTypeHandler:
    """Base interface for element type handlers."""

    @classmethod
    def get_type_id(cls) -> str:
        """Get the unique type identifier for this element type.

        Returns:
            String identifier for this element type
        """
        raise NotImplementedError("Subclasses must implement get_type_id")

    @classmethod
    def create_element_ui(cls, parent=None) -> Optional[UIElement]:
        """Show UI for creating a new element of this type.

        Args:
            parent: Optional parent widget for UI

        Returns:
            Created element or None if cancelled
        """
        raise NotImplementedError("Subclasses must implement create_element_ui")

    @classmethod
    def to_config(cls, element: UIElement, element_id: str) -> ElementConfig:
        """Convert an element to configuration for storage.

        Args:
            element: The element to convert
            element_id: ID for the element

        Returns:
            Element configuration
        """
        raise NotImplementedError("Subclasses must implement to_config")

    @classmethod
    def from_config(cls, config: ElementConfig) -> UIElement:
        """Create an element instance from configuration.

        Args:
            config: The element configuration

        Returns:
            Element instance
        """
        raise NotImplementedError("Subclasses must implement from_config")


class ImageCaptureDialog(QDialog):
    """Dialog for capturing an image element."""

    def __init__(self, capturer: WindowCapturer, parent=None):
        """Initialize the image capture dialog."""
        super().__init__(parent)
        self.setWindowTitle("Capture Image Element")
        self.resize(400, 200)
        self.capturer = capturer
        self.region = None
        self.image = None

        self._init_ui()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "This dialog will help you capture an image element.\n\n"
            "1. Make sure the game window is visible\n"
            "2. Click 'Select Region' to capture a screenshot\n"
            "3. Select the region of the screen containing the element"
        )
        layout.addWidget(instructions)

        # Buttons
        button_layout = QHBoxLayout()

        self.select_button = QPushButton("Select Region")
        self.select_button.clicked.connect(self._select_region)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _select_region(self):
        """Select a region of the screen."""
        capture_result = self.capturer.capture_window()

        if not capture_result:
            QMessageBox.critical(self, "Error", f"Failed to capture window")
            return

        # For demonstration purposes, just use a small region in the center of the screen
        # In a real implementation, you would let the user select a region
        screenshot = capture_result.to_pil()
        width, height = screenshot.size

        # Use 10% of the screen in the center
        region_width = width // 10
        region_height = height // 10
        region_x = (width - region_width) // 2
        region_y = (height - region_height) // 2

        self.region = Region(
            name="Captured Region",
            start_x=region_x,
            start_y=region_y,
            width=region_width,
            height=region_height,
            total_width=width,
            total_height=height
        )

        # Extract the image
        self.image = screenshot.crop((region_x, region_y, region_x + region_width, region_y + region_height))

        # Show the captured region
        QMessageBox.information(
            self,
            "Region Captured",
            f"Captured region at ({region_x}, {region_y}) with size {region_width}x{region_height}"
        )

        self.accept()


class ImageElementHandler(ElementTypeHandler):
    """Handler for image elements."""

    @classmethod
    def get_type_id(cls) -> str:
        return ElementType.IMAGE.value

    @classmethod
    def create_element_ui(cls, parent=None) -> Optional[ImageElement]:
        """Show UI for creating a new image element.

        This involves taking a screenshot and selecting a region.

        Args:
            parent: Optional parent widget for UI

        Returns:
            Created image element or None if cancelled
        """
        dialog = ImageCaptureDialog(parent)
        if dialog.exec():
            if dialog.region and dialog.image:
                # Create element
                return ImageElement(
                    name="Temp Name",  # Will be overwritten by caller
                    region=dialog.region,
                    target_image=dialog.image,
                    threshold=0.8  # Default threshold
                )

        return None

    @classmethod
    def to_config(cls, element: ImageElement, element_id: str) -> ElementConfig:
        """Convert an image element to configuration.

        Args:
            element: The image element to convert
            element_id: ID for the element

        Returns:
            Element configuration
        """
        # Convert to entity for serialization
        entity = element.to_entity()
        data = entity.to_dict()

        return ElementConfig(
            id=element_id,
            name=element.name,
            type=ElementType.IMAGE.value,
            data=data
        )

    @classmethod
    def from_config(cls, config: ElementConfig) -> ImageElement:
        """Create an image element from configuration.

        Args:
            config: The element configuration

        Returns:
            Image element instance
        """
        entity = ImageElementEntity.from_dict(config.data)
        return ImageElement.from_entity(entity)


class PixelColorElementHandler(ElementTypeHandler):
    """Handler for pixel color elements."""

    @classmethod
    def get_type_id(cls) -> str:
        return ElementType.PIXEL_COLOR.value

    @classmethod
    def create_element_ui(cls, parent=None) -> Optional[PixelColorElement]:
        """Show UI for creating a new pixel color element.

        This involves selecting pixels and their colors using an overlay approach.

        Args:
            parent: Optional parent widget for UI

        Returns:
            Created pixel color element or None if cancelled
        """
        # TODO
        # if points_colors and len(points_colors) > 0:
        #     # Create element
        #     return PixelColorElement(
        #         name="Temp Name",  # Will be overwritten by caller
        #         points_colors=points_colors,
        #         match_all=True  # Default to match all points
        #     )


    @classmethod
    def to_config(cls, element: PixelColorElement, element_id: str) -> ElementConfig:
        """Convert a pixel color element to configuration.

        Args:
            element: The pixel color element to convert
            element_id: ID for the element

        Returns:
            Element configuration
        """
        entity = element.to_entity()
        data = entity.to_dict()

        return ElementConfig(
            id=element_id,
            name=element.name,
            type=ElementType.PIXEL_COLOR.value,
            data=data,
        )

    @classmethod
    def from_config(cls, config: ElementConfig) -> PixelColorElement:
        entity = PixelColorElementEntity.from_dict(config.data)
        return PixelColorElement.from_entity(entity)


class ElementTypeRegistry:
    """Registry for element type handlers."""

    _handlers: Dict[str, Type[ElementTypeHandler]] = {}

    @classmethod
    def register_handler(cls, handler_class: Type[ElementTypeHandler]) -> None:
        """Register a handler for an element type.

        Args:
            handler_class: Handler class for the element type
        """
        type_id = handler_class.get_type_id()
        cls._handlers[type_id] = handler_class

    @classmethod
    def get_handler(cls, type_id: str) -> Optional[Type[ElementTypeHandler]]:
        """Get the handler for an element type.

        Args:
            type_id: Type identifier

        Returns:
            Handler class for the element type or None if not found
        """
        return cls._handlers.get(type_id)

    @classmethod
    def get_all_handlers(cls) -> Dict[str, Type[ElementTypeHandler]]:
        """Get all registered handlers.

        Returns:
            Dictionary of type IDs to handler classes
        """
        return cls._handlers.copy()


# Register built-in handlers
ElementTypeRegistry.register_handler(ImageElementHandler)
ElementTypeRegistry.register_handler(PixelColorElementHandler)

class PageConfigManager:
    """Manager for loading, saving, and using page configurations."""

    def __init__(self, config_path: Union[str, Path]):
        """Initialize the page config manager.
        Args:
            config_path: Path to the JSON configuration file
        """
        self.config_path = Path(config_path)
        self.config = GameConfig()
        self._element_cache: Dict[str, Dict[str, UIElement]] = {}  # page_id -> {element_id -> element}

        # Load config if it exists
        if self.config_path.exists():
            self.load_config()

    def load_config(self) -> None:
        """Load the configuration from the JSON file."""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, 'r') as f:
                json_data = json.load(f)

            self.config = GameConfig.from_dict(json_data)
            # Clear cache when loading new config
            self._element_cache.clear()
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def save_config(self) -> None:
        """Save the configuration to the JSON file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        try:
            json_data = self.config.to_dict()
            with open(self.config_path, 'w') as f:
                json.dump(json_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save configuration: {e}")

    def add_element(self, page_id: str, element: UIElement) -> str:
        """Add an element to a page.

        Args:
            page_id: ID of the page to add the element to
            element: The UI element to add

        Returns:
            The ID of the added element
        """
        # Check if page exists
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")

        # Get the page
        page = self.config.pages[page_id]

        # Generate a unique numeric element ID
        element_id = self._generate_element_id(page_id)

        # Determine element type
        if isinstance(element, ImageElement):
            handler = ElementTypeRegistry.get_handler(ElementType.IMAGE.value)
        elif isinstance(element, PixelColorElement):
            handler = ElementTypeRegistry.get_handler(ElementType.PIXEL_COLOR.value)
        else:
            raise TypeError(f"Unsupported element type: {type(element)}")

        if not handler:
            raise ValueError(f"No handler found for element type: {type(element)}")

        # Create element config
        element_config = handler.to_config(element, element_id)

        # Add to page
        page.elements[element_id] = element_config

        # Add to cache
        if page_id not in self._element_cache:
            self._element_cache[page_id] = {}
        self._element_cache[page_id][element_id] = element

        return element_id

    def _generate_element_id(self, page_id: str) -> str:
        """Generate a unique numeric element ID for a page.

        Args:
            page_id: ID of the page

        Returns:
            A unique element ID
        """
        # Get the page
        page = self.config.pages[page_id]

        # If no elements exist, start with 1
        if not page.elements:
            return "1"

        # Find the highest existing numeric ID
        numeric_ids = []
        for element_id in page.elements.keys():
            if element_id.isdigit():
                numeric_ids.append(int(element_id))

        # If no numeric IDs exist, start with 1
        if not numeric_ids:
            return "1"

        # Return the next available ID
        return str(max(numeric_ids) + 1)

    def add_page(self, page_name: str) -> str:
        """Add a page to the configuration.

        Args:
            page_name: Human-readable name for the page

        Returns:
            The ID of the added page
        """
        # Generate a numeric ID
        page_id = self._generate_page_id()

        self.config.pages[page_id] = PageConfig(
            id=page_id,
            name=page_name
        )

        return page_id

    def _generate_page_id(self) -> str:
        """Generate a unique numeric page ID.

        Returns:
            A unique page ID
        """
        # If no pages exist, start with 1
        if not self.config.pages:
            return "1"

        # Find the highest existing numeric ID
        numeric_ids = []
        for page_id in self.config.pages.keys():
            if page_id.isdigit():
                numeric_ids.append(int(page_id))

        # If no numeric IDs exist, start with 1
        if not numeric_ids:
            return "1"

        # Return the next available ID
        return str(max(numeric_ids) + 1)

    def add_page_identifier(self, page_id: str, element_id: str) -> None:
        """Add an identifier element to a page.

        Args:
            page_id: ID of the page
            element_id: ID of the element to add as identifier
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")

        page = self.config.pages[page_id]

        if element_id not in page.elements:
            raise ValueError(f"Element with ID {element_id} does not exist in page {page_id}")

        if element_id not in page.identifier_element_ids:
            page.identifier_element_ids.append(element_id)

    def add_interactive_element(self, page_id: str, element_id: str) -> None:
        """Add an interactive element to a page.

        Args:
            page_id: ID of the page
            element_id: ID of the interactive element to add
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")

        page = self.config.pages[page_id]

        if element_id not in page.elements:
            raise ValueError(f"Element with ID {element_id} does not exist in page {page_id}")

        if element_id not in page.interactive_element_ids:
            page.interactive_element_ids.append(element_id)

    def add_transition(self, page_id: str, element_id: str, target_page_id: str,
                       confirmation_element_ids: Optional[List[str]] = None) -> None:
        """Add a transition between pages.

        Args:
            page_id: ID of the source page
            element_id: ID of the element to click
            target_page_id: ID of the target page
            confirmation_element_ids: Optional list of element IDs that confirm arrival at target page
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")

        if target_page_id not in self.config.pages:
            raise ValueError(f"Target page with ID {target_page_id} does not exist")

        page = self.config.pages[page_id]

        if element_id not in page.elements:
            raise ValueError(f"Element with ID {element_id} does not exist in page {page_id}")

        # Validate confirmation elements if provided
        if confirmation_element_ids:
            target_page = self.config.pages[target_page_id]
            for conf_id in confirmation_element_ids:
                if conf_id not in target_page.elements:
                    raise ValueError(f"Confirmation element with ID {conf_id} does not exist in target page {target_page_id}")

        # Create transition
        transition = TransitionConfig(
            element_id=element_id,
            target_page=target_page_id,
            confirmation_element_ids=confirmation_element_ids or []
        )

        # Add to page
        page.transitions.append(transition)

    def get_element(self, page_id: str, element_id: str) -> UIElement:
        """Get an element by ID from a page.

        Args:
            page_id: ID of the page
            element_id: ID of the element to get

        Returns:
            The element instance
        """
        # Check if page exists
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")

        page = self.config.pages[page_id]

        # Check if element exists in page
        if element_id not in page.elements:
            raise ValueError(f"Element with ID {element_id} does not exist in page {page_id}")

        # Check cache first
        if page_id in self._element_cache and element_id in self._element_cache[page_id]:
            return self._element_cache[page_id][element_id]

        # Not in cache, create from config
        element_config = page.elements[element_id]

        # Get handler for element type
        handler = ElementTypeRegistry.get_handler(element_config.type)
        if not handler:
            raise ValueError(f"No handler found for element type: {element_config.type}")

        # Create element from config
        element = handler.from_config(element_config)

        # Add to cache
        if page_id not in self._element_cache:
            self._element_cache[page_id] = {}
        self._element_cache[page_id][element_id] = element

        return element

    def get_page_identifiers(self, page_id: str) -> List[UIElement]:
        """Get all identifier elements for a page.

        Args:
            page_id: ID of the page

        Returns:
            List of identifier elements
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")

        page = self.config.pages[page_id]

        return [self.get_element(page_id, element_id)
                for element_id in page.identifier_element_ids]

    def get_page_interactive_elements(self, page_id: str) -> List[UIElement]:
        """Get all interactive elements for a page.

        Args:
            page_id: ID of the page

        Returns:
            List of interactive elements
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")

        page = self.config.pages[page_id]

        return [self.get_element(page_id, element_id)
                for element_id in page.interactive_element_ids]

    def get_transition_element(self, from_page_id: str, to_page_id: str) -> Optional[UIElement]:
        """Get the element to click to transition from one page to another.

        Args:
            from_page_id: ID of the source page
            to_page_id: ID of the target page

        Returns:
            The element to click or None if no direct transition exists
        """
        if from_page_id not in self.config.pages:
            raise ValueError(f"Page with ID {from_page_id} does not exist")

        if to_page_id not in self.config.pages:
            raise ValueError(f"Page with ID {to_page_id} does not exist")

        page = self.config.pages[from_page_id]

        # Find transition
        for transition in page.transitions:
            if transition.target_page == to_page_id:
                return self.get_element(from_page_id, transition.element_id)

        return None

    def get_confirmation_elements(self, from_page_id: str, to_page_id: str) -> List[UIElement]:
        """Get the elements that confirm a transition has completed.

        Args:
            from_page_id: ID of the source page
            to_page_id: ID of the target page

        Returns:
            List of elements that should be present on the target page
        """
        if from_page_id not in self.config.pages:
            raise ValueError(f"Page with ID {from_page_id} does not exist")

        if to_page_id not in self.config.pages:
            raise ValueError(f"Page with ID {to_page_id} does not exist")

        from_page = self.config.pages[from_page_id]

        # Find transition
        for transition in from_page.transitions:
            if transition.target_page == to_page_id:
                return [self.get_element(to_page_id, element_id)
                        for element_id in transition.confirmation_element_ids]

        # If no specific confirmation elements, use target page identifiers
        return self.get_page_identifiers(to_page_id)
