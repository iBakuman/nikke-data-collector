"""
NIKKE Arena module

This module provides tools for automating and processing NIKKE arena features.
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

from .character_matcher import CharacterMatcher, MatchResult
from .db.character_dao import CharacterDAO
from .image_processor import ImageProcessor


__all__ = [
    'CharacterMatcher',
    'MatchResult',
    'ImageProcessor',
    'CharacterDAO',
]
