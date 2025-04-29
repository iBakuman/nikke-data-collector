"""
Tests for the page configuration functionality.
"""
import io
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from domain.regions import Region
from processor.elements import ImageElement, PixelColorElement
from processor.page_config import (ElementType, ElementTypeRegistry,
                                   GameConfig, ImageElementHandler,
                                   PageConfigManager, PixelColorElementHandler)


class TestPageConfig(unittest.TestCase):
    """Tests for the page configuration functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_config.json"
        self.config_manager = PageConfigManager(self.config_path)
        
        # Create a test image
        self.test_image = Image.new("RGB", (100, 100), color=(255, 0, 0))
        
        # Create a test region
        self.test_region = Region(
            name="Test Region",
            start_x=10,
            start_y=10,
            width=80,
            height=80,
            total_width=100,
            total_height=100
        )
    
    def tearDown(self):
        """Clean up after the test."""
        self.temp_dir.cleanup()
    
    def test_element_type_registry(self):
        """Test the element type registry."""
        # Check that the registry contains the expected handlers
        handlers = ElementTypeRegistry.get_all_handlers()
        self.assertIn(ElementType.IMAGE.value, handlers)
        self.assertIn(ElementType.PIXEL_COLOR.value, handlers)
        
        # Get handlers and check they're the right type
        image_handler = ElementTypeRegistry.get_handler(ElementType.IMAGE.value)
        self.assertEqual(image_handler, ImageElementHandler)
        
        pixel_handler = ElementTypeRegistry.get_handler(ElementType.PIXEL_COLOR.value)
        self.assertEqual(pixel_handler, PixelColorElementHandler)
    
    def test_add_page(self):
        """Test adding a page to the configuration."""
        # Add a page
        self.config_manager.add_page("test_page", "Test Page")
        
        # Check that the page was added
        self.assertIn("test_page", self.config_manager.config.pages)
        self.assertEqual(self.config_manager.config.pages["test_page"].name, "Test Page")
    
    def test_add_element(self):
        """Test adding an element to a page."""
        # Add a page
        self.config_manager.add_page("test_page", "Test Page")
        
        # Create an image element
        image_element = ImageElement(
            name="Test Element",
            region=self.test_region,
            target_image=self.test_image,
            threshold=0.8
        )
        
        # Add the element to the page
        element_id = self.config_manager.add_element("test_page", image_element)
        
        # Check that the element was added
        self.assertIn(element_id, self.config_manager.config.pages["test_page"].elements)
        self.assertEqual(
            self.config_manager.config.pages["test_page"].elements[element_id].name,
            "Test Element"
        )
    
    def test_add_page_identifier(self):
        """Test adding an identifier element to a page."""
        # Add a page
        self.config_manager.add_page("test_page", "Test Page")
        
        # Create an image element
        image_element = ImageElement(
            name="Test Identifier",
            region=self.test_region,
            target_image=self.test_image,
            threshold=0.8
        )
        
        # Add the element to the page
        element_id = self.config_manager.add_element("test_page", image_element)
        
        # Add the element as an identifier
        self.config_manager.add_page_identifier("test_page", element_id)
        
        # Check that the element was added as an identifier
        self.assertIn(
            element_id,
            self.config_manager.config.pages["test_page"].identifier_element_ids
        )
    
    def test_add_interactive_element(self):
        """Test adding an interactive element to a page."""
        # Add a page
        self.config_manager.add_page("test_page", "Test Page")
        
        # Create an image element
        image_element = ImageElement(
            name="Test Interactive",
            region=self.test_region,
            target_image=self.test_image,
            threshold=0.8
        )
        
        # Add the element to the page
        element_id = self.config_manager.add_element("test_page", image_element)
        
        # Add the element as an interactive element
        self.config_manager.add_interactive_element("test_page", element_id)
        
        # Check that the element was added as an interactive element
        self.assertIn(
            element_id,
            self.config_manager.config.pages["test_page"].interactive_element_ids
        )
    
    def test_add_transition(self):
        """Test adding a transition between pages."""
        # Add two pages
        self.config_manager.add_page("page1", "Page 1")
        self.config_manager.add_page("page2", "Page 2")
        
        # Create an image element
        image_element = ImageElement(
            name="Test Button",
            region=self.test_region,
            target_image=self.test_image,
            threshold=0.8
        )
        
        # Add the element to page1
        element_id = self.config_manager.add_element("page1", image_element)
        
        # Create a confirmation element
        conf_element = ImageElement(
            name="Confirmation Element",
            region=self.test_region,
            target_image=self.test_image,
            threshold=0.8
        )
        
        # Add the confirmation element to page2
        conf_id = self.config_manager.add_element("page2", conf_element)
        
        # Add a transition from page1 to page2
        self.config_manager.add_transition(
            "page1", element_id, "page2", [conf_id]
        )
        
        # Check that the transition was added
        transitions = self.config_manager.config.pages["page1"].transitions
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0].element_id, element_id)
        self.assertEqual(transitions[0].target_page, "page2")
        self.assertEqual(transitions[0].confirmation_element_ids, [conf_id])
    
    def test_save_load_config(self):
        """Test saving and loading the configuration."""
        # Add a page
        self.config_manager.add_page("test_page", "Test Page")
        
        # Create an image element
        image_element = ImageElement(
            name="Test Element",
            region=self.test_region,
            target_image=self.test_image,
            threshold=0.8
        )
        
        # Add the element to the page
        element_id = self.config_manager.add_element("test_page", image_element)
        
        # Save the configuration
        self.config_manager.save_config()
        
        # Create a new config manager and load the configuration
        new_manager = PageConfigManager(self.config_path)
        
        # Check that the configuration was loaded correctly
        self.assertIn("test_page", new_manager.config.pages)
        self.assertEqual(new_manager.config.pages["test_page"].name, "Test Page")
        self.assertIn(element_id, new_manager.config.pages["test_page"].elements)
        self.assertEqual(
            new_manager.config.pages["test_page"].elements[element_id].name,
            "Test Element"
        )


if __name__ == "__main__":
    unittest.main() 
