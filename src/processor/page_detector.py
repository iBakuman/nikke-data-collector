"""
Page Detection Module for NIKKE data collection system.

This module provides functionality for detecting the current page based on
identifier elements and handling transitions between pages.
"""
import time
from typing import Dict, List, Optional, Tuple, Union

from PIL import Image

from processor.elements import ImageElement, PixelColorElement, UIElement
from processor.page_config import PageConfigManager


class PageDetectionResult:
    """Result of a page detection operation."""
    
    def __init__(self, page_id: Optional[str] = None, 
                 confidence: float = 0.0, 
                 elements_found: Optional[List[str]] = None):
        """Initialize a page detection result.
        
        Args:
            page_id: ID of the detected page or None if no page detected
            confidence: Confidence level of the detection (0.0-1.0)
            elements_found: Names of the elements that were found
        """
        self.page_id = page_id
        self.confidence = confidence
        self.elements_found = elements_found or []
        
    @property
    def is_detected(self) -> bool:
        """Check if a page was detected.
        
        Returns:
            True if a page was detected, False otherwise
        """
        return self.page_id is not None


class PageDetector:
    """Detector for identifying the current page based on UI elements."""
    
    def __init__(self, config_manager: PageConfigManager):
        """Initialize a page detector.
        
        Args:
            config_manager: Page configuration manager
        """
        self.config_manager = config_manager
        
    def detect_page(self, screenshot: Image.Image) -> PageDetectionResult:
        """Detect the current page based on identifier elements.
        
        Args:
            screenshot: Current screenshot of the game
            
        Returns:
            PageDetectionResult with the detected page or None if no match
        """
        best_match = None
        best_confidence = 0.0
        best_elements_found = []
        
        # Check each page in the configuration
        for page_id, page in self.config_manager.config.pages.items():
            # Skip pages with no identifiers
            if not page.identifier_element_ids:
                continue
                
            # Get identifier elements for this page
            identifiers = self.config_manager.get_page_identifiers(page_id)
            
            # Check if all identifier elements are visible
            elements_found = []
            for element in identifiers:
                if element.is_visible(screenshot):
                    elements_found.append(element.name)
            
            # Calculate match confidence
            if elements_found:
                confidence = len(elements_found) / len(identifiers)
                
                # Update best match if this is better
                if confidence > best_confidence:
                    best_match = page_id
                    best_confidence = confidence
                    best_elements_found = elements_found
        
        # Return result
        if best_match:
            return PageDetectionResult(
                page_id=best_match,
                confidence=best_confidence,
                elements_found=best_elements_found
            )
        else:
            return PageDetectionResult()
            
    def navigate_to_page(self, from_page_id: str, to_page_id: str, 
                          click_handler: callable, 
                          screenshot_getter: callable, 
                          max_wait: float = 30.0,
                          check_interval: float = 0.5) -> bool:
        """Navigate from one page to another.
        
        Args:
            from_page_id: ID of the current page
            to_page_id: ID of the target page
            click_handler: Function that takes an element and clicks it
            screenshot_getter: Function that returns a fresh screenshot
            max_wait: Maximum time to wait for page transition in seconds
            check_interval: Interval between checks in seconds
            
        Returns:
            True if navigation was successful, False otherwise
        """
        # Check if we're already on the target page
        if from_page_id == to_page_id:
            return True
            
        # Get transition element
        transition_element = self.config_manager.get_transition_element(from_page_id, to_page_id)
        if not transition_element:
            return False
            
        # Get confirmation elements
        confirmation_elements = self.config_manager.get_confirmation_elements(from_page_id, to_page_id)
        
        # Click the transition element
        screenshot = screenshot_getter()
        if not transition_element.is_visible(screenshot):
            return False
            
        click_handler(transition_element)
        
        # Wait for confirmation elements to appear
        start_time = time.time()
        while time.time() - start_time < max_wait:
            # Get fresh screenshot
            screenshot = screenshot_getter()
            
            # Check if all confirmation elements are visible
            if all(element.is_visible(screenshot) for element in confirmation_elements):
                return True
                
            # Wait before next check
            time.sleep(check_interval)
            
        # Timed out waiting for confirmation
        return False
        
    def find_path(self, from_page_id: str, to_page_id: str) -> Optional[List[str]]:
        """Find a path between two pages.
        
        Args:
            from_page_id: ID of the starting page
            to_page_id: ID of the destination page
            
        Returns:
            List of page IDs forming a path, or None if no path exists
        """
        # Check if pages exist
        if from_page_id not in self.config_manager.config.pages:
            raise ValueError(f"Page with ID {from_page_id} does not exist")
            
        if to_page_id not in self.config_manager.config.pages:
            raise ValueError(f"Page with ID {to_page_id} does not exist")
            
        # Simple case: already at destination
        if from_page_id == to_page_id:
            return [from_page_id]
            
        # Simple case: direct transition
        if self.config_manager.get_transition_element(from_page_id, to_page_id) is not None:
            return [from_page_id, to_page_id]
            
        # BFS to find shortest path
        queue = [(from_page_id, [from_page_id])]
        visited = {from_page_id}
        
        while queue:
            current_page, path = queue.pop(0)
            
            # Get all transitions from current page
            transitions = self.config_manager.config.pages[current_page].transitions
            
            for transition in transitions:
                next_page = transition.target_page
                
                if next_page == to_page_id:
                    # Found destination
                    return path + [to_page_id]
                    
                if next_page not in visited:
                    visited.add(next_page)
                    queue.append((next_page, path + [next_page]))
        
        # No path found
        return None 
