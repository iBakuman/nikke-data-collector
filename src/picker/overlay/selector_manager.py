"""
Overlay manager for coordinating element capture.

This module provides a manager class that coordinates between the
overlay widget and capture strategies for different element types.
"""
from typing import Any, Dict, List, Optional, Type

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from picker.overlay.overlay_widget import OverlayWidget
from picker.overlay.selector import (ElementSelector,
                                     StrategyInfo, PixelColorSelector, ImageSelector)
from picker.overlay.visual_elements import VisualElement

logger = get_logger(__name__)


class SelectorManager(QObject):
    """Manager for coordinating overlay widget and capture strategies."""
    
    # Signals
    selection_started = Signal(str)  # Strategy type
    selection_completed = Signal(str, object)  # Strategy type, result
    selection_cancelled = Signal()
    
    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the overlay manager.
        
        Args:
            overlay: The overlay widget to manage
            window_capturer: Window capturer for screenshots
        """
        super().__init__()
        self.overlay = overlay
        self.window_capturer = window_capturer
        self.current_selector: Optional[ElementSelector] = None
        self.current_strategy_type_id: Optional[str] = None
        self.control_panel: Optional[QWidget] = None
        
        # Strategy registry 
        self.strategy_registry: Dict[str, Type[ElementSelector]] = {}
        
        # Register built-in strategies
        self._register_builtin_strategies()
    
    def _register_builtin_strategies(self) -> None:
        """Register the built-in capture strategies."""
        self.register_strategy(PixelColorSelector)
        self.register_strategy(ImageSelector)
        
        logger.info(f"Registered {len(self.strategy_registry)} built-in capture strategies")
    
    def register_strategy(self, strategy_class: Type[ElementSelector]) -> None:
        """Register a capture strategy.
        
        Args:
            strategy_class: Strategy class to register
            
        Raises:
            ValueError: If strategy type already exists
        """
        strategy_info = strategy_class.get_strategy_info()
        
        if strategy_info.type_id in self.strategy_registry:
            raise ValueError(f"Strategy type '{strategy_info.type_id}' already registered")

        if self.strategy_registry[strategy_info.type_id]:
            raise ValueError(f"Strategy type '{strategy_info.type_id}' already registered")
        
        self.strategy_registry[strategy_info.type_id] = strategy_class
        logger.debug(f"Registered strategy: {strategy_info.display_name} ({strategy_info.type_id})")
    
    def get_strategy_infos(self) -> List[StrategyInfo]:
        """Get all registered strategy information.
        
        Returns:
            List of strategy information objects
        """
        return [cls.get_strategy_info() for cls in self.strategy_registry.values()]
    
    def start_selection(self, strategy_type_id: str) -> None:
        if strategy_type_id not in self.strategy_registry:
            raise ValueError(f"Unknown capture strategy type: {strategy_type_id}")
        
        # If already capturing, cancel current capture
        if self.current_selector:
            self.current_selector.cancel_selection()
            self.current_selector = None
            self.current_strategy_type_id = None
            
            if self.control_panel:
                self.control_panel.close()
                self.control_panel = None
        
        # Get strategy class
        strategy_class = self.strategy_registry[strategy_type_id]
        
        # Create strategy instance
        self.current_selector = strategy_class(self.overlay, self.window_capturer)
        self.current_strategy_type_id = strategy_type_id
        
        # Connect to strategy signals
        self.current_selector.selection_completed.connect(self._handle_selection_completed)
        self.current_selector.selection_cancelled.connect(self._handle_selection_cancelled)
        
        # Emit capture started signal
        self.selection_started.emit(strategy_type_id)
        
        # Start capture and get control panel
        self.control_panel = self.current_selector.start_selection()
        
        # Show control panel
        if self.control_panel:
            self.control_panel.show()
    
    def _handle_selection_completed(self, result: Any) -> None:
        """Handle completion of the capture process.
        
        Args:
            result: Capture result data
        """
        if self.current_strategy_type_id:
            self.selection_completed.emit(self.current_strategy_type_id, result)
            
        # Clean up
        self._cleanup_current_capture()
    
    def _handle_selection_cancelled(self) -> None:
        """Handle cancellation of the capture process."""
        self.selection_cancelled.emit()
        
        # Clean up
        self._cleanup_current_capture()
    
    def _cleanup_current_capture(self) -> None:
        """Clean up resources from current capture."""
        # Disconnect signals
        if self.current_selector:
            self.current_selector.selection_completed.disconnect(self._handle_selection_completed)
            self.current_selector.selection_cancelled.disconnect(self._handle_selection_cancelled)
            
        # Close control panel
        if self.control_panel:
            self.control_panel.close()
            self.control_panel = None
            
        # Clear strategy
        self.current_selector = None
        self.current_strategy_type_id = None
    
    def cancel_current_selection(self) -> None:
        """Cancel the current capture process if active."""
        if self.current_selector:
            self.current_selector.cancel_selection()
    
    def load_elements(self, config_list: List[Dict[str, Any]]) -> List[VisualElement]:
        """Load visual elements from configuration.
        
        Args:
            config_list: List of element configurations
            
        Returns:
            List of created visual elements
        """
        elements = []
        
        for config in config_list:
            # Get element type
            type_id = config.get("type")
            if not type_id:
                logger.warning(f"Skipping element config with missing type: {config}")
                continue
                
            # Find strategy that handles this type
            if type_id not in self.strategy_registry:
                logger.warning(f"No strategy registered for element type: {type_id}")
                continue
                
            # Create element
            strategy_class = self.strategy_registry[type_id]
            try:
                element = strategy_class.create_visual_element(config)
                elements.append(element)
            except Exception as e:
                logger.error(f"Error creating element of type {type_id}: {e}")
        
        return elements
    
    def get_configs_from_elements(self, elements: List[VisualElement]) -> List[Dict[str, Any]]:
        """Get configurations from visual elements.
        
        Args:
            elements: List of visual elements
            
        Returns:
            List of element configurations
        """
        configs = []
        
        for element in elements:
            # Find strategy that handles this element
            handled = False
            
            for strategy_class in self.strategy_registry.values():
                if strategy_class.handles_element_type(element):
                    try:
                        config = strategy_class.get_config_from_element(element)
                        configs.append(config)
                        handled = True
                        break
                    except Exception as e:
                        logger.error(f"Error getting config from element: {e}")
            
            if not handled:
                logger.warning(f"No strategy handles element type: {type(element).__name__}")
        
        return configs 
