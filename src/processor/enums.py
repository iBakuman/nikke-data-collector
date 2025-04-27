"""
Enumerations used throughout the NIKKE data collection system.

This module defines various enumeration types used to categorize and identify
different parts of the system such as screen regions, UI elements, and states.
"""

from enum import Enum, auto


class RegionKey(Enum):
    """
    Keys for identifying screen regions.
    
    These keys uniquely identify different areas of the screen that are
    relevant for the NIKKE data collection system.
    """
    
    # General screen regions
    FULL_SCREEN = auto()
    HEADER = auto()
    FOOTER = auto()
    MAIN_CONTENT = auto()
    
    # Menu regions
    MAIN_MENU = auto()
    TOP_MENU = auto()
    SIDE_MENU = auto()
    
    # Game-specific regions
    CHARACTER_LIST = auto()
    CHARACTER_DETAILS = auto()
    INVENTORY = auto()
    SHOP = auto()
    GACHA = auto()
    BATTLE = auto()
    LOBBY = auto()
    
    # Dialog regions
    DIALOG_BOX = auto()
    CONFIRMATION_DIALOG = auto()
    ERROR_DIALOG = auto()
    
    # Button regions
    BACK_BUTTON = auto()
    CONFIRM_BUTTON = auto()
    CANCEL_BUTTON = auto()
    CLOSE_BUTTON = auto()
    
    # Custom or specialized regions
    CHARACTER_STATS = auto()
    SKILL_DESCRIPTION = auto()
    EQUIPMENT_SLOTS = auto()

class StateType(Enum):
    """
    Types of screen states.
    
    These types represent the different states that the application can be in,
    which determine what UI elements are visible and what actions are available.
    """
    
    # General application states
    LOADING = auto()
    ERROR = auto()
    NORMAL = auto()
    
    # Game-specific states
    TITLE_SCREEN = auto()
    LOGIN = auto()
    MAIN_MENU = auto()
    CHARACTER_SELECTION = auto()
    CHARACTER_DETAILS = auto()
    INVENTORY = auto()
    SHOP = auto()
    GACHA = auto()
    BATTLE = auto()
    BATTLE_RESULTS = auto()
    LOBBY = auto()
    
    # Dialog states
    DIALOG = auto()
    CONFIRMATION = auto()
    ERROR_DIALOG = auto()


class DataType(Enum):
    """
    Types of data that can be collected.
    
    These types categorize the different kinds of data that the system can
    collect from the game.
    """
    
    # Basic data types
    TEXT = auto()
    IMAGE = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    
    # Game-specific data types
    CHARACTER_STAT = auto()
    SKILL_INFO = auto()
    EQUIPMENT_INFO = auto()
    INVENTORY_ITEM = auto()
    CURRENCY = auto()
    GACHA_RESULT = auto()
    BATTLE_RESULT = auto()
    
    # Metadata
    TIMESTAMP = auto()
    SESSION_ID = auto()
    USER_ACTION = auto()


class ActionType(Enum):
    """
    Types of actions that can be performed.
    
    These types represent the different actions that the automation system
    can perform to interact with the game.
    """
    
    # Basic interactions
    CLICK = auto()
    DOUBLE_CLICK = auto()
    DRAG = auto()
    TYPE = auto()
    WAIT = auto()
    CAPTURE = auto()
    
    # Game-specific actions
    NAVIGATE = auto()
    SELECT_CHARACTER = auto()
    EQUIP_ITEM = auto()
    UPGRADE = auto()
    PURCHASE = auto()
    SELL = auto()
    GACHA_PULL = auto()
    START_BATTLE = auto()
    
    # System actions
    RESTART_APP = auto()
    CLOSE_APP = auto()
    TAKE_SCREENSHOT = auto()
    LOG_DATA = auto()


class DataCollectionType(Enum):
    """Types of data that can be collected."""
    NIKKE_STATS = auto()
    EQUIPMENT_STATS = auto()
    SHOP_ITEMS = auto()
    BATTLE_RESULTS = auto()
    EVENT_REWARDS = auto()
    MISSION_OBJECTIVES = auto()


class InteractionType(Enum):
    """Types of interactions that can be performed."""
    CLICK = auto()
    SWIPE = auto()
    DRAG = auto()
    WAIT = auto()
    TEXT_INPUT = auto()
    KEYPRESS = auto()


class LogLevel(Enum):
    """Log levels for the automation system."""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class ElementKey(Enum):
    """Keys for UI elements that can be detected on screen."""
    # Login screen elements
    LOGIN_BUTTON = auto()
    USERNAME_FIELD = auto()
    PASSWORD_FIELD = auto()
    
    # Main menu elements
    MENU_BUTTON = auto()
    INVENTORY_BUTTON = auto()
    SHOP_BUTTON = auto()
    MISSIONS_BUTTON = auto()
    SETTINGS_BUTTON = auto()
    
    # Generic elements
    CLOSE_BUTTON = auto()
    BACK_BUTTON = auto()
    CONFIRM_BUTTON = auto()
    CANCEL_BUTTON = auto()


class StateKey(Enum):
    """Keys for different screen states in the application."""
    UNKNOWN = auto()
    LOGIN = auto()
    TITLE_SCREEN = auto()
    MAIN_MENU = auto()
    INVENTORY = auto()
    SHOP = auto()
    MISSIONS = auto()
    BATTLE = auto()
    SETTINGS = auto()
    DIALOG = auto()


class StepId(Enum):
    """Identifiers for automation steps."""
    LOGIN = auto()
    NAVIGATE_TO_MAIN = auto()
    START_BATTLE = auto()
    WAIT_BATTLE_RESULT = auto()
    COLLECT_DAMAGE = auto()
    COLLECT_REWARDS = auto()
    CONTINUE = auto()
    CHECK_ERROR = auto()


class CollectorType(Enum):
    """Types of data collectors."""
    OCR = auto()  # Optical Character Recognition
    IMAGE = auto()  # Raw image capture
    NUMBER = auto()  # Numeric data extraction
    COLOR = auto()  # Color information
    TABLE = auto()  # Tabular data 
