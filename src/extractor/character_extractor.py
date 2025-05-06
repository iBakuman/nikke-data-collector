import glob
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from PIL import Image
from PySide6.QtGui import QImage

from collector.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CharacterExtractionParams:
    """Parameters for character extraction"""
    boundary_width: int
    character_width: int
    character_spacing: int
    height_width_ratio: float


def extract_characters(
        input_image_path: str,
        output_folder: str,
        extraction_params: CharacterExtractionParams,
        character_map: Dict[int, str]
) -> List[str]:
    """
    Extract character images from a long image with equal boundaries and spacing.
    Only extracts characters specified in the character_map.

    Args:
        input_image_path: Path to the input image
        output_folder: Directory to save extracted images
        extraction_params: Extraction parameters
        character_map: Dictionary mapping character positions (1-12) to character names

    Returns:
        List of paths to the extracted character images
    """
    # Create output directory if needed
    os.makedirs(output_folder, exist_ok=True)

    # Open the image
    try:
        image = Image.open(input_image_path)
    except Exception as e:
        logger.error(f"Failed to open image {input_image_path}: {e}")
        return []

    # Calculate character positions
    positions = calculate_character_positions(
        extraction_params.boundary_width,
        extraction_params.character_width,
        extraction_params.character_spacing,
        12  # Fixed at 12 characters
    )

    # Calculate character height based on ratio
    character_height = int(extraction_params.character_width * extraction_params.height_width_ratio)

    # Use image bottom as the bottom boundary
    bottom_boundary = image.height

    # Calculate top boundary position
    top_boundary = bottom_boundary - character_height

    # Extract each character
    output_paths = []
    for position, (start_x, end_x) in enumerate(positions, 1):
        # Skip positions not in the character map
        if position not in character_map:
            continue

        character_name = character_map[position]

        try:
            # Crop the character image
            character_image = image.crop((start_x, top_boundary, end_x, bottom_boundary))

            # Generate output path with proper naming convention
            output_path = generate_character_filename(output_folder, character_name)

            # Save the character image
            character_image.save(output_path)
            logger.info(f"Saved character {position} ({character_name}) to {output_path}")

            output_paths.append(output_path)
        except Exception as e:
            logger.error(f"Failed to extract character {position} ({character_name}): {e}")

    return output_paths


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


def pil_to_qimage(pil_image: Image.Image):
    if pil_image.mode == "RGB":
        r, g, b = pil_image.split()
        pil_image = Image.merge("RGB", (b, g, r))
    elif pil_image.mode == "RGBA":
        r, g, b, a = pil_image.split()
        pil_image = Image.merge("RGBA", (b, g, r, a))

    data = pil_image.tobytes("raw", pil_image.mode)

    if pil_image.mode == "RGBA":
        qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGBA8888)
    else:
        qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888)

    return qimage
