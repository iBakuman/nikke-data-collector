"""
Overlay manager for coordinating element capture.

This module provides a manager class that coordinates between the
overlay widget and capture strategies for different element types.
"""
from typing import Any, Dict, List, Optional, Type

from PySide6.QtCore import QObject, Signal

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from picker.overlay.capture_strategies import (CaptureStrategy,
                                               ImageElementCaptureStrategy,
                                               PixelColorCaptureStrategy,
                                               StrategyInfo)
from picker.overlay.overlay_widget import OverlayWidget

logger = get_logger(__name__)

class OverlayManager(QObject):
    """Manager for coordinating overlay widget and capture strategies."""
    
    # Signals
    capture_started = Signal(str)  # Strategy type
    capture_completed = Signal(str, object)  # Strategy type, result
    capture_cancelled = Signal()
    
    def __init__(self, overlay: OverlayWidget, window_capturer: WindowCapturer):
        """Initialize the overlay manager.
        
        Args:
            overlay: The overlay widget to manage
            window_capturer: Window capturer for screenshots
        """
        super().__init__()
        self.overlay = overlay
        self.window_capturer = window_capturer
        self.current_strategy: Optional[CaptureStrategy] = None
        self.original_state: Optional[Dict[str, Any]] = None
        
        # Strategy registry 
        self.strategy_infos: Dict[str, StrategyInfo] = {}
        self._register_builtin_strategies()
    
    def _register_builtin_strategies(self):
        """Register built-in capture strategies."""
        self.register_strategy(PixelColorCaptureStrategy)
        self.register_strategy(ImageElementCaptureStrategy)
    
    def register_strategy(self, strategy_class: Type[CaptureStrategy]):
        """Register a capture strategy.
        
        Args:
            strategy_class: Strategy class to register
            
        Raises:
            ValueError: If strategy type already exists
        """
        strategy_info = strategy_class.get_strategy_info()
        if strategy_info.type_id in self.strategy_infos:
            raise ValueError(f"Strategy type '{strategy_info.type_id}' already registered")
        
        self.strategy_infos[strategy_info.type_id] = strategy_info
        logger.debug(f"Registered strategy: {strategy_info.display_name} ({strategy_info.type_id})")
    
    def get_strategy_infos(self) -> List[StrategyInfo]:
        """Get all registered strategy information.
        
        Returns:
            List of strategy information objects
        """
        return list(self.strategy_infos.values())
    
    def start_capture(self, strategy_type_id: str) -> Optional[Any]:
        """Start capture process with specified strategy type.
        
        Args:
            strategy_type_id: Type ID of capture strategy
            
        Returns:
            Capture result data or None if cancelled
            
        Raises:
            ValueError: If strategy type is unknown
        """
        # Check if strategy type is valid
        if strategy_type_id not in self.strategy_infos:
            raise ValueError(f"Unknown capture strategy type: {strategy_type_id}")
        
        # Get strategy info
        strategy_info = self.strategy_infos[strategy_type_id]
        
        # Save original overlay state
        self._save_original_state()
        
        # Create strategy instance
        self.current_strategy = strategy_info.strategy_class(self.overlay, self.window_capturer)
        
        self.capture_started.emit(strategy_type_id)
        self.current_strategy.start_capture()

        capture_result = None
        if  self.current_strategy.result_data:
            capture_result = self.current_strategy.result_data
            self.capture_completed.emit(strategy_type_id, capture_result)
        else:
            self.capture_cancelled.emit()
        
        # Restore original state
        self._restore_original_state()
        
        # Clear current strategy
        self.current_strategy = None
        
        return capture_result
    
    def _save_original_state(self):
        """Save the original state of the overlay."""
        self.original_state = {
            "visual_elements": self.overlay.get_visual_elements()
        }
    
    def _restore_original_state(self):
        """Restore the overlay to its original state."""
        if not self.original_state:
            return
            
        # Clear current visual elements
        self.overlay.clear_visual_elements()
        
        # Restore original visual elements
        for element in self.original_state["visual_elements"]:
            self.overlay.add_visual_element(element) 
