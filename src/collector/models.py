import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Annotated, Dict, List, Optional

from PIL import Image
from dataclass_wizard import JSONPyWizard, JSONWizard, json_key

from mixin.json import JSONSerializableMixin
from repository.character_dto import Character


class ServerRegion(Enum):
    """Server regions in NIKKE"""
    JP = "jp"  # Japanese Server
    KR = "kr"  # Korean Server
    GLOBAL = "global"  # Global Server
    SEA = "sea"  # Southeast Asia Server
    NA = "na"  # North American Server
    HK_MO_TW = "hk_mo_tw"  # Hong Kong/Macau/Taiwan Server


@dataclass
class Round(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    round_index: int
    image: Annotated[Optional[Image.Image], json_key("excluded", dump=False)] = None
    characters: Dict[int, Character] = field(default_factory=dict)

    def add_character(self, character: Character) -> None:
        """Add a character to this round"""
        self.characters[character.position] = character

    def save_character_images(self, output_dir: str) -> None:
        """
        Save all character images to the specified directory.

        Args:
            output_dir: Directory where character images will be saved
        """
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save each character image
        for position, character in self.characters.items():
            if character.image:
                file_path = os.path.join(output_dir, f"character_{position}.png")
                character.image.save(file_path)

    def __str__(self) -> str:
        result = f"\nRound {self.round_index}"
        for position, character in self.characters.items():
            result += f"\n{position}: {character.name}"
        return result


@dataclass
class User(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    user_id: str
    group_id: int = None
    player_index: int = None
    server_region: Optional[ServerRegion] = None
    profile_image: Annotated[Optional[Image.Image], json_key("excluded", dump=False)] = None
    team_image: Annotated[Optional[Image.Image], json_key("excluded", dump=False)] = None
    rounds: Dict[int, Round] = field(default_factory=dict)

    def add_round(self, round_obj: Round) -> None:
        """Add a round to this user's data"""
        self.rounds[round_obj.round_index] = round_obj

    def save_profile_image(self, output_dir: str, prefix: str = None) -> None:
        """
        Save the user's profile image to the specified directory.

        Args:
            output_dir: Directory where the image will be saved
            prefix: Prefix for the file name
        """
        if not self.profile_image:
            return
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        # Save the user's profile image
        file_path = os.path.join(output_dir, f"{prefix + '_' if prefix else ''}user_{self.user_id}_profile.png")
        self.profile_image.save(file_path)

    def save_team_image(self, output_dir: str, prefix: str = None) -> None:
        """
        Save the user's image to the specified directory.

        Args:
            output_dir: Directory where the image will be saved
            prefix: Prefix for the file name
        """
        if not self.team_image:
            return
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        # Save the user's image
        file_path = os.path.join(output_dir, f"{prefix + '_' if prefix else ''}user_{self.user_id}_team.png")
        self.team_image.save(file_path)


@dataclass
class Group(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    users: List[User]
    combined_image: Annotated[Optional[Image.Image], json_key("excluded", dump=False)] = None
    result_image: Annotated[Optional[Image.Image], json_key("excluded", dump=False)] = None

    @staticmethod
    def _save_image(image: Image.Image, save_path: str):
        """
        Save an image to a file.
        """
        if not image:
            raise ValueError("No image to save")
        # Ensure save directory exists
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        image.save(save_path)

    def save_result_image(self, save_path: str):
        self._save_image(self.result_image, save_path)

    def save_combined_image(self, save_path: str):
        self._save_image(self.combined_image, save_path)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user result by ID.

        Args:
            user_id: User ID string

        Returns:
            User or None if not found
        """
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None


class BattleResult(Enum):
    """Possible results from a battle"""
    VICTORY = auto()
    DEFEAT = auto()
    UNKNOWN = auto()


class TournamentStage(Enum):
    """Tournament stages for promotion and championship tournaments"""
    # Promotion tournament stages
    STAGE_64_32 = "64->32"
    STAGE_32_16 = "32->16"
    STAGE_16_8 = "16->8"

    # Championship tournament stages
    STAGE_8_4 = "8->4"
    STAGE_4_2 = "4->2"
    STAGE_2_1 = "2->1"


@dataclass
class BattleData(JSONWizard, JSONSerializableMixin):
    class _(JSONPyWizard.Meta):
        skip_defaults = True

    """Data structure to hold battle result information"""
    left_user_id: Optional[str] = None
    right_user_id: Optional[str] = None
    result: list[BattleResult] = field(default_factory=list)
    image: Annotated[Optional[Image.Image], json_key("excluded", dump=False)] = None

    def save_image(self, save_path: str) -> None:
        if self.image:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            self.image.save(save_path)
