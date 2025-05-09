"""
Screen regions module for the NIKKE data collection system.

This module provides classes for defining, managing, and interacting with
screen regions - rectangular areas of the screen used for capturing, analyzing,
and detecting UI elements.
"""

from dataclasses import dataclass

from dataclass_wizard import JSONWizard

from mixin.json import JSONSerializableMixin


@dataclass
class Point:
    x: int
    y: int
    total_width: int
    total_height: int


@dataclass
class Region(JSONWizard, JSONSerializableMixin):
    name: str
    start_x: int
    start_y: int
    width: int
    height: int
    total_width: int
    total_height: int
