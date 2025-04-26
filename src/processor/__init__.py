"""
Automation processor package for NIKKE data collection.

This package provides a framework for automating game interactions and data collection.
"""

from .collectors import (DataCollector, ImageCollector, NumberCollector,
                         OCRCollector)
from .conditions import (ElementCondition, MultiCondition, StateCondition,
                         WaitCondition)
from .context import AutomationContext, Result
from .controller import AutomationController
from .elements import ImageElement, PixelElement, TextElement, UIElement
# Import and re-export main components for easy access
from .enums import CollectorType, ElementKey, RegionKey, StateType, StepId
from .regions import FixedRegion, Region, RelativeRegion
from .states import ScreenState
from .steps import (AutomationStep, CollectionStep, ConditionalStep,
                    InteractionStep, WaitStep)

__all__ = [
    # Enums
    'StateType', 'RegionKey', 'ElementKey', 'StepId', 'CollectorType',

    # Elements
    'UIElement', 'PixelElement', 'TextElement', 'ImageElement',

    # Regions
    'Region', 'FixedRegion', 'RelativeRegion',

    # Conditions
    'WaitCondition', 'ElementCondition', 'StateCondition', 'MultiCondition',

    # Context and Results
    'Result', 'AutomationContext',

    # Collectors
    'DataCollector', 'OCRCollector', 'NumberCollector', 'ImageCollector',

    # States
    'ScreenState',

    # Steps
    'AutomationStep', 'InteractionStep', 'WaitStep', 'CollectionStep', 'ConditionalStep',

    # Controller
    'AutomationController',
]
