"""
Overlay manager for coordinating element capture.

This module provides a manager class that coordinates between the
overlay widget and capture strategies for different element types.
"""
from typing import Any, Dict, List, Optional, Type

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout)

from collector.logging_config import get_logger
from collector.window_capturer import WindowCapturer
from picker.overlay.capture_strategies import (CaptureStrategy,
                                               ImageElementCaptureStrategy,
                                               PixelColorCaptureStrategy,
                                               StrategyInfo)
from picker.overlay.overlay_widget import OverlayWidget

logger = get_logger(__name__)


class CaptureDialog(QDialog):
    """Dialog for controlling element capture process."""
    
    def __init__(self, strategy: CaptureStrategy, parent=None):
        """Initialize the capture dialog.
        
        Args:
            strategy: The active capture strategy
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.strategy = strategy
        self.setWindowTitle("Element Capture")
        self.setMinimumWidth(300)
        
        # Setup UI
        self._init_ui()
        
        # Connect to strategy signals
        self.strategy.capture_step_completed.connect(self._on_step_completed)
        self.strategy.capture_completed.connect(self.accept)
        self.strategy.capture_cancelled.connect(self.reject)
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Instructions label
        self.instructions_label = QLabel(self.strategy.get_instructions())
        layout.addWidget(self.instructions_label)
        
        # Status label
        self.status_label = QLabel("Ready to capture")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.done_button = QPushButton("Done")
        self.done_button.clicked.connect(self._on_done)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        
        button_layout.addWidget(self.done_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _on_step_completed(self, step_index: int, step_data: Any):
        """Handle strategy step completion.
        
        Args:
            step_index: The completed step index
            step_data: The step result data
        """
        # Update instructions
        self.instructions_label.setText(self.strategy.get_instructions())
        
        # Update status based on step
        if isinstance(self.strategy, PixelColorCaptureStrategy):
            self.status_label.setText(f"Captured {step_index} point(s)")
        elif isinstance(self.strategy, ImageElementCaptureStrategy):
            if step_index == 0:
                self.status_label.setText("Template region selected")
            else:
                self.status_label.setText("Detection region selected")
    
    def _on_done(self):
        """Handle done button click."""
        self.strategy.complete_capture()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.strategy.cancel_capture()


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
