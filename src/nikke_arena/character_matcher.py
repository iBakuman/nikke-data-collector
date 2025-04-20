import os
import re
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import cv2
import imagehash
import numpy as np
from PIL import Image
from diskcache import Cache

from .logging_config import get_logger
from .models import Character
from .resources import get_ref_images_dir

logger = get_logger(__name__)


@dataclass
class MatchResult:
    """Result of a character matching operation with similarity score"""
    character: Optional[Character]  # Matched character or None if no match
    similarity: float  # Similarity score (0.0-1.0)

    @property
    def has_match(self) -> bool:
        """Whether this result contains a valid match"""
        return self.character is not None


class CharacterImageMatcher:
    """
    A class that matches character images against a reference directory of images.
    Uses template matching with OpenCV and implements disk caching for improved performance.
    """

    def __init__(self, cache_dir: str, reference_dir: Optional[str] = None,
                 cache_size_limit: int = int(1e9), similarity_threshold: Optional[float] = None):
        """
        Initialize the image matcher with reference directory and cache settings.

        Args:
            cache_dir: Directory to store the disk cache. This must be specified.
            reference_dir: Directory containing reference character images.
                          If None, uses the default reference directory from resources.
            cache_size_limit: Maximum cache size in bytes (default: 1GB)
            similarity_threshold: Minimum similarity score to consider a match valid.
                                 If None, always returns the best match regardless of score.
        """
        # Use default reference directory if not specified
        if reference_dir is None:
            self.reference_dir = get_ref_images_dir()
            logger.info(f"Using default reference directory: {self.reference_dir}")
        else:
            self.reference_dir = reference_dir

        self.cache = Cache(cache_dir, size_limit=cache_size_limit)
        self.similarity_threshold = similarity_threshold

        logger.info(f"CharacterImageMatcher initialized with reference dir: {self.reference_dir}")
        logger.info(f"Cache initialized at: {cache_dir}")
        logger.info(
            f"Similarity threshold: {self.similarity_threshold if self.similarity_threshold is not None else 'None (always return best match)'}")

    @staticmethod
    def compute_image_hash(image: np.ndarray) -> str:
        """
        Compute a perceptual hash for an image to use as cache key.
        Uses imagehash library for robust hashing that handles minor image variations.

        Args:
            image: OpenCV image (numpy array)

        Returns:
            A string hash representing the image
        """
        # Convert from OpenCV to PIL format
        if len(image.shape) == 3:
            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            image_pil = Image.fromarray(image)

        # Compute perceptual hash (more robust to minor variations)
        phash = str(imagehash.phash(image_pil))
        return phash

    @staticmethod
    def preprocess_image(image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for matching (convert to grayscale).

        Args:
            image: OpenCV image (numpy array)

        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def match_with_template(query_image: np.ndarray, template_image: np.ndarray) -> float:
        """
        Match a query image with a template using OpenCV's template matching.
        Resizes larger image to match smaller image dimensions.

        Args:
            query_image: The image to match (preprocessed)
            template_image: The template to match against (preprocessed)

        Returns:
            Similarity score (higher is better)
        """
        # Determine which image needs resizing
        query_h, query_w = query_image.shape[:2]
        template_h, template_w = template_image.shape[:2]

        # Resize the larger image to match the smaller one
        if query_h > template_h or query_w > template_w:
            scale = min(template_h / query_h, template_w / query_w)
            new_size = (int(query_w * scale), int(query_h * scale))
            query_image = cv2.resize(query_image, new_size, interpolation=cv2.INTER_AREA)
        elif template_h > query_h or template_w > query_w:
            scale = min(query_h / template_h, query_w / template_w)
            new_size = (int(template_w * scale), int(template_h * scale))
            template_image = cv2.resize(template_image, new_size, interpolation=cv2.INTER_AREA)

        # Perform template matching
        try:
            # Use normalized correlation coefficient method for better results
            result = cv2.matchTemplate(query_image, template_image, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            return float(max_val)  # Convert to native Python float for caching
        except cv2.error as e:
            logger.error(f"Template matching error: {e}")
            return 0.0

    @staticmethod
    def load_image_safely(image_path: str) -> Optional[np.ndarray]:
        """
        Safely load an image from path, supporting Unicode characters (e.g., Chinese)

        Args:
            image_path: Path to the image file

        Returns:
            Image as numpy array in BGR format (OpenCV format) or None if loading fails
        """
        try:
            # Use PIL to open the image which better handles Unicode paths
            with Image.open(image_path) as pil_img:
                # Use existing pil_to_cv method to convert to OpenCV format
                return CharacterImageMatcher.pil_to_cv(pil_img)
        except Exception as e:
            logger.error(f"Failed to load image from {image_path}: {e}")
            return None

    @staticmethod
    def pil_to_cv(pil_image: Image.Image) -> np.ndarray:
        """
        Convert a PIL image to OpenCV format (numpy array in BGR).

        Args:
            pil_image: PIL Image object

        Returns:
            Image as numpy array in BGR format (OpenCV format)
        """
        # Ensure image is in RGB mode
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Convert to numpy array (RGB format)
        img_array = np.array(pil_image)

        # Convert from RGB to BGR (OpenCV format)
        return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    @staticmethod
    def extract_character_info_from_filename(filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract character ID and name from a filename.
        Expected format: "001_character_name_a.png"

        Args:
            filename: Filename to parse

        Returns:
            Tuple of (character_id, character_name) or (None, None) if parsing fails
        """
        # Extract using regex pattern for standard format with letter suffix
        match = re.match(r'^(\d{3})_([^_]+)_[a-z]\.(?:png|jpg|jpeg)$', filename, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)

        # Try alternative pattern without letter suffix
        match = re.match(r'^(\d{3})_([^_]+)\.(?:png|jpg|jpeg)$', filename, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)

        return None, None

    def find_best_match(self, query_image: np.ndarray) -> Tuple[Optional[str], Optional[str], float]:
        """
        Find the best matching character ID and name from reference directory.

        Args:
            query_image: Input image to match

        Returns:
            Tuple of (character_id, character_name, similarity_score)
            If no match is found, returns (None, None, best_similarity)
        """
        # Preprocess query image
        preprocessed_query = self.preprocess_image(query_image)

        best_match_id = None
        best_match_name = None
        best_similarity = 0.0

        # Scan all files in reference directory
        for filename in os.listdir(self.reference_dir):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            # Extract ID from filename (format: 123_name_a.png)
            match = re.match(r'^(\d{3})_', filename)
            if not match:
                continue

            try:
                # Load and preprocess reference image - handle Unicode paths
                ref_image_path = os.path.join(self.reference_dir, filename)
                ref_image = self.load_image_safely(ref_image_path)
                if ref_image is None:
                    logger.warning(f"Failed to load reference image: {ref_image_path}")
                    continue

                preprocessed_ref = self.preprocess_image(ref_image)

                # Match images
                similarity = self.match_with_template(preprocessed_query, preprocessed_ref)

                # Update best match if better
                if similarity > best_similarity:
                    best_similarity = similarity
                    char_id, char_name = self.extract_character_info_from_filename(filename)
                    best_match_id = char_id
                    best_match_name = char_name

            except Exception as e:
                logger.error(f"Error processing reference image {filename}: {e}")

        # If threshold is None, always return the best match
        # Otherwise, only return the match if it meets the threshold
        if self.similarity_threshold is None:
            logger.info(
                f"Best match: ID={best_match_id}, name={best_match_name}, similarity={best_similarity:.4f} (no threshold applied)")
            return best_match_id, best_match_name, best_similarity
        elif best_similarity >= self.similarity_threshold:
            logger.info(
                f"Best match: ID={best_match_id}, name={best_match_name}, similarity={best_similarity:.4f} (threshold={self.similarity_threshold:.4f})")
            return best_match_id, best_match_name, best_similarity
        else:
            logger.info(
                f"No match found with similarity >= {self.similarity_threshold:.4f} (best was {best_similarity:.4f})")
            return None, None, best_similarity

    def _match_core(self, query_image: np.ndarray, image_source: str = "Unknown") -> MatchResult:
        """
        Core matching logic used by the match method.

        Args:
            query_image: OpenCV image (numpy array) to match
            image_source: Description of image source for logging

        Returns:
            MatchResult containing the character information and similarity score
        """
        try:
            # Compute hash for cache lookup
            cache_key = self.compute_image_hash(query_image)

            # Check if result is in cache
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                logger.info(f"Cache hit for image from {image_source}")

                # Reconstruct MatchResult from cached data
                if cached_result is None:
                    return MatchResult(None, 0.0)

                char_id, char_name, similarity = cached_result
                if char_id is None:
                    return MatchResult(None, similarity)

                character = Character(
                    position=0,  # Position not known from matching alone
                    id=char_id,
                    name=char_name
                )
                return MatchResult(character, similarity)

            logger.info(f"Cache miss for image from {image_source}, performing matching...")

            # Perform matching
            char_id, char_name, similarity = self.find_best_match(query_image)

            # Create result object and cache results
            if char_id is not None:
                character = Character(
                    position=0,  # Position not known from matching alone
                    id=char_id,
                    name=char_name
                )
                result = MatchResult(character, similarity)

                # Cache the result
                self.cache[cache_key] = (char_id, char_name, similarity)
            else:
                result = MatchResult(None, similarity)
                # Don't cache null results so we can retry matching next time
                # self.cache[cache_key] = (None, None, similarity)

            return result

        except Exception as e:
            logger.error(f"Error in _match_core: {e}")
            return MatchResult(None, 0.0)

    def match(self, image: Union[str, np.ndarray, Image.Image]) -> MatchResult:
        """
        Universal match method that accepts different image input types.
        Returns a MatchResult with character information and similarity score.

        Args:
            image: Can be a file path (str), OpenCV image (np.ndarray), or PIL image (Image.Image)

        Returns:
            MatchResult containing the character information and similarity score
        """
        try:
            # Process different input types to get OpenCV image
            if isinstance(image, str):
                # Load image from file path
                image_source = f"file: {image}"
                query_image = self.load_image_safely(image)
                if query_image is None:
                    logger.error(f"Failed to load image: {image}")
                    return MatchResult(None, 0.0)
            elif isinstance(image, np.ndarray):
                # Already an OpenCV image
                image_source = "numpy array"
                query_image = image
            elif isinstance(image, Image.Image):
                # Convert PIL image to OpenCV format
                image_source = "PIL image"
                query_image = self.pil_to_cv(image)
            else:
                logger.error(f"Unsupported image type: {type(image)}. Must be str, np.ndarray, or PIL.Image.Image")
                return MatchResult(None, 0.0)

            # Delegate to core matching logic
            return self._match_core(query_image, image_source)

        except Exception as e:
            logger.error(f"Error in match method: {e}")
            return MatchResult(None, 0.0)

    def clear_cache(self):
        """Clear the entire cache"""
        self.cache.clear()
        logger.info("Image matcher cache cleared")
