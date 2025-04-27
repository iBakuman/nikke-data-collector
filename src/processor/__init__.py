"""
Automation processor package for NIKKE data collection.

This package provides a framework for automating game interactions and data collection.
"""

from domain.regions import Region
from .collectors import (DataCollector, ImageCollector, NumberCollector,
                         OCRCollector)
from .conditions import (ElementCondition, MultiCondition, StateCondition,
                         WaitCondition)
from .context import AutomationContext, Result
from .controller import AutomationController
from .elements import ImageElementEntity, TextElement, UIElement
from .enums import CollectorType, RegionKey, StateType, StepId
from .states import ScreenState
from .steps import (AutomationStep, CollectionStep, ConditionalStep,
                    InteractionStep, WaitStep)

__all__ = [
    # Enums
    'StateType', 'RegionKey', 'StepId', 'CollectorType',

    # Elements
    'UIElement', 'TextElement', 'ImageElementEntity',

    # Regions
    'Region',

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
