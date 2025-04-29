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
from typing import Any, Dict, List, Optional, Union

from dataclass_wizard import JSONWizard

from domain.image_element import ImageElementEntity
from domain.pixel_element import PixelColorElementEntity
from processor.elements import ImageElement, PixelColorElement


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
    identifier_element_ids: List[str] = field(default_factory=list)  # Elements that identify this page
    interactive_element_ids: List[str] = field(default_factory=list)  # Elements that can be interacted with
    transitions: List[TransitionConfig] = field(default_factory=list)  # Transitions to other pages


@dataclass
class GameConfig(JSONWizard):
    """Root configuration for the game UI."""
    pages: Dict[str, PageConfig] = field(default_factory=dict)
    elements: Dict[str, ElementConfig] = field(default_factory=dict)


class PageConfigManager:
    """Manager for loading, saving, and using page configurations."""

    def __init__(self, config_path: Union[str, Path]):
        """Initialize the page config manager.
        
        Args:
            config_path: Path to the JSON configuration file
        """
        self.config_path = Path(config_path)
        self.config = GameConfig()
        self._element_cache: Dict[str, Union[ImageElement, PixelColorElement]] = {}
        
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

    def add_element(self, element: Union[ImageElement, PixelColorElement], element_id: Optional[str] = None) -> str:
        """Add an element to the configuration.
        
        Args:
            element: The UI element to add
            element_id: Optional custom ID for the element
            
        Returns:
            The ID of the added element
        """
        # Generate ID if not provided
        if not element_id:
            element_id = f"{element.name.lower().replace(' ', '_')}_{len(self.config.elements)}"
            
        # Check if element with this ID already exists
        if element_id in self.config.elements:
            raise ValueError(f"Element with ID {element_id} already exists")
            
        # Create element config based on type
        if isinstance(element, ImageElement):
            # Convert to entity for serialization
            entity = element.to_dto()
            
            element_config = ElementConfig(
                id=element_id,
                name=element.name,
                type=ElementType.IMAGE.value,
                data={
                    "region_x": entity.region_x,
                    "region_y": entity.region_y,
                    "region_width": entity.region_width,
                    "region_height": entity.region_height,
                    "region_total_width": entity.region_total_width,
                    "region_total_height": entity.region_total_height,
                    "image_data": entity.image_data,
                    "threshold": entity.threshold
                }
            )
        elif isinstance(element, PixelColorElement):
            # Convert to entity for serialization
            entity = element.to_dto()
            
            element_config = ElementConfig(
                id=element_id,
                name=element.name,
                type=ElementType.PIXEL_COLOR.value,
                data={
                    "points_colors": [
                        {
                            "point": {
                                "x": pc.point.x,
                                "y": pc.point.y,
                                "total_width": pc.point.total_width,
                                "total_height": pc.point.total_height
                            },
                            "color": {
                                "r": pc.color.r,
                                "g": pc.color.g,
                                "b": pc.color.b
                            },
                            "tolerance": pc.tolerance
                        } for pc in entity.points_colors
                    ],
                    "match_all": entity.match_all
                }
            )
        else:
            raise TypeError(f"Unsupported element type: {type(element)}")
            
        # Add to config
        self.config.elements[element_id] = element_config
        
        # Add to cache
        self._element_cache[element_id] = element
        
        return element_id

    def add_page(self, page_id: str, page_name: str) -> None:
        """Add a page to the configuration.
        
        Args:
            page_id: Unique identifier for the page
            page_name: Human-readable name for the page
        """
        if page_id in self.config.pages:
            raise ValueError(f"Page with ID {page_id} already exists")
            
        self.config.pages[page_id] = PageConfig(
            id=page_id,
            name=page_name
        )

    def add_page_identifier(self, page_id: str, element_id: str) -> None:
        """Add an identifier element to a page.
        
        Args:
            page_id: ID of the page
            element_id: ID of the element to add as identifier
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")
            
        if element_id not in self.config.elements:
            raise ValueError(f"Element with ID {element_id} does not exist")
            
        if element_id not in self.config.pages[page_id].identifier_element_ids:
            self.config.pages[page_id].identifier_element_ids.append(element_id)

    def add_interactive_element(self, page_id: str, element_id: str) -> None:
        """Add an interactive element to a page.
        
        Args:
            page_id: ID of the page
            element_id: ID of the interactive element to add
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")
            
        if element_id not in self.config.elements:
            raise ValueError(f"Element with ID {element_id} does not exist")
            
        if element_id not in self.config.pages[page_id].interactive_element_ids:
            self.config.pages[page_id].interactive_element_ids.append(element_id)

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
            
        if element_id not in self.config.elements:
            raise ValueError(f"Element with ID {element_id} does not exist")
            
        # Validate confirmation elements
        if confirmation_element_ids:
            for conf_id in confirmation_element_ids:
                if conf_id not in self.config.elements:
                    raise ValueError(f"Confirmation element with ID {conf_id} does not exist")
        
        # Create transition
        transition = TransitionConfig(
            element_id=element_id,
            target_page=target_page_id,
            confirmation_element_ids=confirmation_element_ids or []
        )
        
        # Add to page
        self.config.pages[page_id].transitions.append(transition)

    def get_element(self, element_id: str) -> Union[ImageElement, PixelColorElement]:
        """Get an element by ID.
        
        Args:
            element_id: ID of the element to get
            
        Returns:
            The element instance
        """
        # Check cache first
        if element_id in self._element_cache:
            return self._element_cache[element_id]
            
        # Not in cache, create from config
        if element_id not in self.config.elements:
            raise ValueError(f"Element with ID {element_id} does not exist")
            
        element_config = self.config.elements[element_id]
        
        # Create appropriate element type
        if element_config.type == ElementType.IMAGE.value:
            # Convert JSON data to entity
            entity = ImageElementEntity(
                name=element_config.name,
                region_x=element_config.data["region_x"],
                region_y=element_config.data["region_y"],
                region_width=element_config.data["region_width"],
                region_height=element_config.data["region_height"],
                region_total_width=element_config.data["region_total_width"],
                region_total_height=element_config.data["region_total_height"],
                image_data=element_config.data["image_data"],
                threshold=element_config.data["threshold"]
            )
            
            # Create element from entity
            element = ImageElement.from_entity(entity)
            
        elif element_config.type == ElementType.PIXEL_COLOR.value:
            # Convert JSON data to entity
            from domain.color import Color
            from domain.pixel_element import PointColorPair
            from domain.regions import Point
            
            points_colors = []
            for pc_data in element_config.data["points_colors"]:
                point = Point(
                    x=pc_data["point"]["x"],
                    y=pc_data["point"]["y"],
                    total_width=pc_data["point"]["total_width"],
                    total_height=pc_data["point"]["total_height"]
                )
                
                color = Color(
                    r=pc_data["color"]["r"],
                    g=pc_data["color"]["g"],
                    b=pc_data["color"]["b"]
                )
                
                tolerance = pc_data.get("tolerance", 10)
                
                points_colors.append(PointColorPair(point=point, color=color, tolerance=tolerance))
            
            entity = PixelColorElementEntity(
                name=element_config.name,
                points_colors=points_colors,
                match_all=element_config.data["match_all"]
            )
            
            # Create element from entity
            element = PixelColorElement.from_entity(entity)
            
        else:
            raise ValueError(f"Unknown element type: {element_config.type}")
            
        # Add to cache
        self._element_cache[element_id] = element
        
        return element

    def get_page_identifiers(self, page_id: str) -> List[Union[ImageElement, PixelColorElement]]:
        """Get all identifier elements for a page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            List of identifier elements
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")
            
        return [self.get_element(element_id) 
                for element_id in self.config.pages[page_id].identifier_element_ids]

    def get_page_interactive_elements(self, page_id: str) -> List[Union[ImageElement, PixelColorElement]]:
        """Get all interactive elements for a page.
        
        Args:
            page_id: ID of the page
            
        Returns:
            List of interactive elements
        """
        if page_id not in self.config.pages:
            raise ValueError(f"Page with ID {page_id} does not exist")
            
        return [self.get_element(element_id) 
                for element_id in self.config.pages[page_id].interactive_element_ids]

    def get_transition_element(self, from_page_id: str, to_page_id: str) -> Optional[Union[ImageElement, PixelColorElement]]:
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
            
        # Find transition
        for transition in self.config.pages[from_page_id].transitions:
            if transition.target_page == to_page_id:
                return self.get_element(transition.element_id)
                
        return None

    def get_confirmation_elements(self, from_page_id: str, to_page_id: str) -> List[Union[ImageElement, PixelColorElement]]:
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
            
        # Find transition
        for transition in self.config.pages[from_page_id].transitions:
            if transition.target_page == to_page_id:
                return [self.get_element(element_id) 
                        for element_id in transition.confirmation_element_ids]
                
        # If no specific confirmation elements, use target page identifiers
        return self.get_page_identifiers(to_page_id) 
