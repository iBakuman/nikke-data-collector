import glob
import os
import re
from dataclasses import dataclass
from typing import List, Tuple

from collector.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CharacterExtractionParams:
    """Parameters for character extraction"""
    boundary_width: int
    character_width: int
    character_spacing: int
    height_width_ratio: float

def calculate_character_positions(
        boundary_width: int,
        character_width: int,
        character_spacing: int,
        character_count: int = 12
) -> List[Tuple[int, int]]:
    """
    Calculate the x-coordinates (start, end) for each character in the image.

    Args:
        boundary_width: Width of the boundary on each side
        character_width: Width of each character
        character_spacing: Spacing between characters
        character_count: Number of characters to extract

    Returns:
        List of (start_x, end_x) tuples for each character
    """
    positions = []
    current_x = boundary_width

    for i in range(character_count):
        start_x = current_x
        end_x = start_x + character_width
        positions.append((start_x, end_x))
        current_x = end_x + character_spacing

    return positions


def generate_character_filename(output_folder: str, character_name: str) -> str:
    """
    Generate a filename for a character based on the specified rules.

    Rules:
    1. If files with the character name exist in the format "id_name_suffix",
       use the same id and increment the suffix.
    2. If no matching files exist, find the highest id and use (id+1) with suffix 'a'.

    Args:
        output_folder: Directory where images are saved
        character_name: Name of the character

    Returns:
        Full path for the new file
    """
    # Pattern to match existing character files: "id_name_suffix.png"
    existing_files = glob.glob(os.path.join(output_folder, f"*_{character_name}_*.png"))

    if existing_files:
        # Find files matching the current character name
        matching_files = []
        pattern = re.compile(r"(\d{3})_" + re.escape(character_name) + r"_([a-z])\.png$")

        for file_path in existing_files:
            file_name = os.path.basename(file_path)
            match = pattern.match(file_name)
            if match:
                id_str = match.group(1)
                suffix = match.group(2)
                matching_files.append((id_str, suffix))

        if matching_files:
            # Sort by id and suffix
            matching_files.sort(key=lambda x: (x[0], x[1]))
            last_id, last_suffix = matching_files[-1]

            # Increment the suffix
            next_suffix = chr(ord(last_suffix) + 1)
            new_filename = f"{last_id}_{character_name}_{next_suffix}.png"
            return os.path.join(output_folder, new_filename)

    # No matching files found, find the highest ID across all files
    all_files = glob.glob(os.path.join(output_folder, "*.png"))
    highest_id = 0

    id_pattern = re.compile(r"^(\d{3})_")
    for file_path in all_files:
        file_name = os.path.basename(file_path)
        match = id_pattern.match(file_name)
        if match:
            id_str = match.group(1)
            highest_id = max(highest_id, int(id_str))

    # Use next ID with suffix 'a'
    next_id = highest_id + 1
    next_id_str = f"{next_id:03d}"  # Format as 3 digits with leading zeros
    new_filename = f"{next_id_str}_{character_name}_a.png"

    return os.path.join(output_folder, new_filename)