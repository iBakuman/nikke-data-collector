"""
UI Constants for NIKKE interfaces.
This file defines button and UI element positions using standard coordinates (3580x2014).
All positions are defined as classes with typed attributes to enable IDE autocompletion.
"""
from dataclasses import dataclass
from typing import NamedTuple

from collector.resources import get_detectable_image_path


@dataclass
class Region:
    start_x: int
    start_y: int
    width: int
    height: int


@dataclass
class DetectableImage:
    """Represents an image that can be detected on screen"""
    image_path: str  # Image filename in resources
    region: Region
    name: str
    confidence: float = 0.8  # Matching threshold

    def __str__(self):
        return f"DetectableImage({self.image_path}, region={self.region}, confidence={self.confidence})"


class Position(NamedTuple):
    x: int
    y: int


class GroupSelectionElements:
    """
    Group Tournament Selection Screen Buttons

    This screen allows players to select tournament groups.
    Coordinates are based on standard screen size (3580x2014).
    """
    _START_X = 1466
    _START_Y = 437
    _ROW_HEIGHT = 92
    _COL_WIDTH = 161
    _GROUPS_PER_ROW = 5  # Number of groups per row

    confirm: Position = Position(1964, 1786)  # Confirm button
    cancel: Position = Position(1615, 1788)  # Cancel button
    close: Position = Position(2228, 260)  # Close button (top-right)

    @classmethod
    def get_group_position(cls, group_number: int) -> Position:
        """
        Calculate position for any group number dynamically.

        Args:
            group_number: The group number (1-64)

        Returns:
            Position: The calculated position for the group button

        Raises:
            ValueError: If group_number is outside valid range (1-64)
        """
        if not 1 <= group_number <= 64:
            raise ValueError(f"Group number must be between 1 and 64, got {group_number}")

        # Convert to 0-based index
        index = group_number - 1

        # Calculate row and column
        row = index // cls._GROUPS_PER_ROW
        col = index % cls._GROUPS_PER_ROW

        # Calculate position
        x = cls._START_X + (col * cls._COL_WIDTH)
        y = cls._START_Y + (row * cls._ROW_HEIGHT)

        return Position(x, y)


class GroupDetailElements:
    """
    Group Tournament Results Screen Buttons

    This screen shows a specific group's participants.
    Each participant is displayed in its own row.
    """
    # Base coordinates for user avatars
    _START_X = 1381  # X coordinate of avatar
    _START_Y = 800  # Y coordinate of first participant's avatar
    _ROW_HEIGHT = 244  # Vertical distance between participants

    result_region: Region = Region(start_x=1268, start_y=685, width=1054, height=980)
    group_button: Position = Position(1790, 583)

    @classmethod
    def get_participant_avatar(cls, participant_index: int) -> Position:
        """
        Get the position of a participant's avatar in the current group view.

        Args:
            participant_index: The participant index (1-4)

        Returns:
            Position: The position of the participant's avatar

        Raises:
            ValueError: If participant_index is outside valid range (1-4)
        """
        if not 1 <= participant_index <= 4:
            raise ValueError(f"Participant index must be between 1 and 4, got {participant_index}")

        # Convert to 0-based index for calculation
        zero_based_index = participant_index - 1

        # Calculate position (simple vertical offset)
        y = cls._START_Y + (zero_based_index * cls._ROW_HEIGHT)

        return Position(cls._START_X, y)


class TeamInfoElements:
    # Base coordinates for round buttons
    _ROUND_1_X = 1427
    _ROUND_1_Y = 984
    _WIDTH = 178

    # Fixed character positions in round detail view
    # ROUND_START_X = 1340  # Fixed X position for character in round view
    # ROUND_START_Y = 952  # Fixed Y position for character in round view

    _CHARACTER_START_X = 1347  # Fixed X position for first character in round view
    _CHARACTER_START_Y = 1060  # Fixed Y position for first character in round view
    _ROUND_WIDTH = 896
    _ROUND_HEIGHT = 356
    _CHARACTER_GAP = 22

    close: Position = Position(2208, 634)  # Close button at top
    avatar: Position = Position(1447, 796)  # Avatar button

    round_region: Region = Region(start_x=_CHARACTER_START_X - 5, start_y=_CHARACTER_START_Y, width=_ROUND_WIDTH,
                                  height=_ROUND_HEIGHT)

    def get_character_region(self, character_index: int) -> Region:
        if not 1 <= character_index <= 5:
            raise ValueError(f"Character index must be between 1 and 5, got {character_index}")
        x = self._CHARACTER_START_X + (character_index - 1) * (self._CHARACTER_GAP + STANDARD_CHARACTER_WIDTH)
        y = self._CHARACTER_START_Y
        return Region(start_x=x, start_y=y, width=STANDARD_CHARACTER_WIDTH, height=STANDARD_CHARACTER_HEIGHT)

    @classmethod
    def get_round_button(cls, round_index: int) -> Position:
        """
        Get the position of a specific round button.

        Args:
            round_index: The round number (1-5)

        Returns:
            Position: The position of the round button

        Raises:
            ValueError: If round_index is outside valid range (1-5)
        """
        if not 1 <= round_index <= 5:
            raise ValueError(f"Round index must be between 1 and 5, got {round_index}")

        # Convert to 0-based index for calculation
        zero_based_index = round_index - 1

        # Calculate position
        x = cls._ROUND_1_X + (zero_based_index * cls._WIDTH)

        return Position(x, cls._ROUND_1_Y)


class ProfileElements:
    """
    Buttons in User Profile Screen
    """
    copy_id: Position = Position(1866, 647)
    close: Position = Position(2248, 187)
    profile_region: Region = Region(start_x=1312, start_y=472, width=958, height=916)


class MatchResultElements:
    _START_X = 2170
    _START_Y = 1150
    _GAP = 86

    close: Position = Position(2209, 490)

    @classmethod
    def get_play_position(cls, round_num: int) -> Position:
        if not 1 <= round_num <= 5:
            raise ValueError(f"Round number must be between 1 and 5, got {round_num}")
        return Position(cls._START_X, cls._START_Y + (round_num - 1) * cls._GAP)


class CheerElements:
    # Player avatars
    left_user: Position = Position(1567, 623)
    right_user: Position = Position(2029, 606)

    # Navigation buttons
    cancel_button: Position = Position(1560, 1772)  # X button at top right
    close_button: Position = Position(2222, 321)  # Cancel button at bottom


class LineupViewElements:
    """
    Elements for the lineup view screen that appears after clicking player avatars
    """
    # Character slots (based on typical 5-character lineup)
    # These positions would need to be adjusted based on actual game UI
    characters: list[Position] = [
        Position(358, 900),  # Character 1
        Position(501, 900),  # Character 2
        Position(644, 900),  # Character 3
        Position(787, 900),  # Character 4
        Position(930, 900),  # Character 5
    ]

    # Lineup screen region for capturing the entire lineup
    lineup_area: Region = Region(300, 750, 700, 250)

    # Navigation buttons
    back_button: Position = Position(250, 180)

    # Detectable elements
    LINEUP_SCREEN = DetectableImage(
        image_path=get_detectable_image_path("lineup_screen.png"),
        name="LINEUP_SCREEN",
        region=Region(start_x=300, start_y=150, width=300, height=80),
        confidence=0.8
    )


class BattleElements:
    next: Position = Position(1800, 1760)




class BattleResultElements:
    left_user: Position = Position(1420, 1020)
    right_user: Position = Position(2034, 1012)
    close: Position = Position(2208, 490)
    stage_32_16: Position = Position(2035, 1620)
    stage_16_8: Position = Position(1540, 1620)
    _FIRST_RESULT_START_X = 1577
    _FIRST_RESULT_START_Y = 1124
    _RESULT_WIDTH = 94
    _RESULT_HEIGHT = 48
    _RESULT_GAP = 37
    # _FIRST_RESULT_START_X = 1550
    # _FIRST_RESULT_START_Y = 1104
    # _RESULT_WIDTH = 138
    # _RESULT_HEIGHT = 85


    _START_X = 1335
    _START_Y = 900
    _WIDTH = 910
    _HEIGHT = 636

    STATISTIC_IMAGE = DetectableImage(
        image_path=get_detectable_image_path("statistic.png"),
        name="STATISTIC",
        region=Region(start_x=2177, start_y=1840, width=280, height=160)
    )

    def get_total_region(self) -> Region:
        return Region(start_x=self._START_X, start_y=self._START_Y, width=self._WIDTH, height=self._HEIGHT)

    def get_region(self, round_num: int) -> Region:
        start_y = self._FIRST_RESULT_START_Y + (round_num - 1) * (self._RESULT_GAP + self._RESULT_HEIGHT)
        return Region(start_x=self._FIRST_RESULT_START_X, start_y=start_y, width=self._RESULT_WIDTH,
                      height=self._RESULT_HEIGHT)

    def get_detectable_win_image(self, round_num: int) -> DetectableImage:
        region = self.get_region(round_num)
        return DetectableImage(
            image_path=get_detectable_image_path("win.png"),
            name="WIN",
            region=region
        )

    def get_detectable_lose_image(self, round_num: int) -> DetectableImage:
        region = self.get_region(round_num)
        return DetectableImage(
            image_path=get_detectable_image_path("lose.png"),
            name="LOSE",
            region=region
        )

class PromotionTournament:
    _GROUP_START_X = 250
    _GROUP_START_Y = 508
    BUTTON_WIDTH = 440

    cheer: Position = Position(1793, 1812)
    CHEER_IMAGE = DetectableImage(
        image_path=get_detectable_image_path("cheer.png"),
        name="CHEER",
        region=Region(start_x=1486, start_y=1699, width=700, height=220)
    )

    @classmethod
    def get_group_button_position(cls, group_number: int) -> Position:
        """
        Calculate position for any group number dynamically.

        Args:
            group_number: The group number (1-8)

        Returns:
            Position: The calculated position for the group button

        Raises:
            ValueError: If group_number is outside valid range (1-64)
        """
        if not 1 <= group_number <= 8:
            raise ValueError(f"Group number must be between 1 and 64, got {group_number}")
        x = cls._GROUP_START_X + (group_number - 1) * cls.BUTTON_WIDTH
        return Position(x, cls._GROUP_START_Y)

    _STAGE_64_32_START_X = 1645
    _STAGE_64_32_START_Y = 839
    _STAGE_64_32_WIDTH = 284
    _STAGE_64_32_HEIGHT = 736

    def get_stage_64_32_position(self, battle_id: int) -> Position:
        if not 1 <= battle_id <= 4:
            raise ValueError(f"Group number must be between 1 and 8, got {battle_id}")
        if battle_id <= 2:
            x = self._STAGE_64_32_START_X + (battle_id - 1) * self._STAGE_64_32_WIDTH
            y = self._STAGE_64_32_START_Y
        else:
            x = self._STAGE_64_32_START_X + (battle_id - 3) * self._STAGE_64_32_WIDTH
            y = self._STAGE_64_32_START_Y + self._STAGE_64_32_HEIGHT
        return Position(x, y)

    @staticmethod
    def get_stage_32_16_position(index: int) -> Position:
        if not 1 <= index <= 2:
            raise ValueError(f"Group number must be between 1 and 2, got {index}")
        if index == 1:
            return Position(1848, 1074)
        else:
            return Position(1730, 1315)

    BUTTON_16 = DetectableImage(
        image_path=get_detectable_image_path("button-16.png"),
        name="BUTTON_16",
        region=Region(start_x=1462, start_y=1570, width=160, height=82)
    )

    _FIRST_AVATAR_START_X = 1335
    _FIRST_AVATAR_START_Y = 700
    _AVATAR_COLUMN_SPACING = 907
    _AVATAR_ROW_SPACING_SMALL = 255
    _AVATAR_ROW_SPACING_LARGE = 489

    def get_player_avatar_position(self, index: int) -> Position:
        """
        Get screen position of player avatar boxes.

        Args:
            index: Avatar index (1-8), ordered from left to right, top to bottom.
                1: Top-left, 2: Top-right
                3: Middle-left, 4: Middle-right
                5: Bottom-left, 6: Bottom-right

        Returns:
            Position object with x,y coordinates
        """
        # Validate index
        if not 1 <= index <= 8:
            raise ValueError(f"Avatar index must be between 1 and 8, got {index}")

        # Calculate vertical position (row)
        row = (index - 1) // 2

        # Calculate horizontal position (column)
        # If even, it's on the right side; if odd, it's on the left
        is_right_column = (index % 2 == 0)

        # Start with base coordinates
        x = self._FIRST_AVATAR_START_X
        y = self._FIRST_AVATAR_START_Y

        # Adjust x-coordinate for right column
        if is_right_column:
            x += self._AVATAR_COLUMN_SPACING

        # Adjust y-coordinate based on row
        if row >= 1:
            y += self._AVATAR_ROW_SPACING_SMALL
        if row >= 2:  # Bottom row
            y += self._AVATAR_ROW_SPACING_LARGE
        if row >= 3:
            y += self._AVATAR_ROW_SPACING_SMALL

        return Position(x, y)


class ChampionshipTournament:
    """UI elements for the championship tournament screen"""
    _STAGE_8_4_START_X = 1655
    _STAGE_8_4_START_Y = 765
    _STAGE_8_4_WIDTH = 260
    _STAGE_8_4_HEIGHT = 740

    _STAGE_4_2_A_START_X = 1842
    _STAGE_4_2_A_START_Y = 1000

    _STAGE_4_2_B_START_X = 1730
    _STAGE_4_2_B_START_Y = 1244

    stage_4_2: Position = Position(2036, 1618)

    CHAMPION_BUTTON = DetectableImage(
        image_path=get_detectable_image_path("button-champion.png"),
        name="BUTTON_CHAMPION",
        region=Region(start_x=1477, start_y=1580, width=130, height=72)
    )

    def get_stage_8_4_position(self, index: int) -> Position:
        """Get position for a match in the 8->4 stage"""
        if not 1 <= index <= 4:
            raise ValueError(f"Match ID must be between 1 and 4 for 8->4 stage, got {index}")

        if index <= 2:
            x = self._STAGE_8_4_START_X + (index - 1) * self._STAGE_8_4_WIDTH
            y = self._STAGE_8_4_START_Y
        else:
            x = self._STAGE_8_4_START_X + (index - 3) * self._STAGE_8_4_WIDTH
            y = self._STAGE_8_4_START_Y + self._STAGE_8_4_HEIGHT
        return Position(x, y)

    def get_stage_4_2_position(self, index: int) -> Position:
        """Get position for a match in the 4->2 stage"""
        if not 1 <= index <= 2:
            raise ValueError(f"Match ID must be between 1 and 2 for 4->2 stage, got {index}")

        if index == 1:
            return Position(self._STAGE_4_2_A_START_X, self._STAGE_4_2_A_START_Y)
        else:
            return Position(self._STAGE_4_2_B_START_X, self._STAGE_4_2_B_START_Y)


# Add these to the module exports
PROMOTION_TOURNAMENT = PromotionTournament()
CHAMPIONSHIP_TOURNAMENT = ChampionshipTournament()
GROUP_SELECTION = GroupSelectionElements()
GROUP_DETAIL = GroupDetailElements()
TEAM_INFO = TeamInfoElements()
PROFILE = ProfileElements()
CHEER = CheerElements()
BATTLE = BattleElements()
LINEUP = LineupViewElements()
BATTLE_RESULT = BattleResultElements()

# Standard window dimensions for NIKKE
STANDARD_WINDOW_WIDTH = 3580
STANDARD_WINDOW_HEIGHT = 2014

STANDARD_CHARACTER_WIDTH = 160
STANDARD_CHARACTER_HEIGHT = 235


