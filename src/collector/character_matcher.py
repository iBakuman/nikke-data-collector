from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image
from diskcache import Cache

from domain.character import Character
from repository.character_dao import CharacterDAO
from .image_processor import ImageProcessor
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MatchResult:
    """Result of a character detection operation with similarity score"""
    character: Optional[Character]  # Matched character or None if no match
    similarity: float  # Similarity score (0.0-1.0)

    @property
    def has_match(self) -> bool:
        """Whether this result contains a valid match"""
        return self.character is not None


class CharacterMatcher:
    """
    Character matchers that matches images against character references in SQLite database.
    Implements template matching with caching for improved performance.
    """

    def __init__(self,
                 cache_dir: str, character_dao: CharacterDAO,
                 similarity_threshold: Optional[float] = None,
                 cache_size_limit: int = int(1e9)):
        """
        Initialize the character detector with database connection and cache settings.

        Args:
            cache_dir: Directory to store the disk cache
            character_dao: Data access object for character data
            similarity_threshold: Minimum similarity score to consider a match valid (optional)
            cache_size_limit: Maximum cache size in bytes (default: 1GB)
        """
        self.cache = Cache(cache_dir, size_limit=cache_size_limit)
        self.similarity_threshold = similarity_threshold
        self.character_dao = character_dao

        logger.info(f"Cache initialized at: {cache_dir}")
        logger.info(
            f"Similarity threshold: {similarity_threshold if similarity_threshold is not None else 'None (always return best match)'}")

    def find_best_match(self, query_image: np.ndarray) -> Tuple[Optional[Character], float]:
        """
        Find the best matching character from the database.

        Args:
            query_image: Input image to match

        Returns:
            Tuple of (Character, similarity_score) or (None, best_similarity) if no match found
        """
        # Preprocess query image
        preprocessed_query = ImageProcessor.preprocess_image(query_image)

        best_match = None
        best_similarity = 0.0

        # Get all characters from database
        characters = self.character_dao.get_all_characters()

        for character in characters:
            # Get all images for this character
            char_images = self.character_dao.get_character_images(character.id)

            # Skip if no images for this character
            if not char_images:
                continue

            # Test each image
            for image_id, image_data in char_images:
                try:
                    # Convert blob to OpenCV image and preprocess
                    ref_image = ImageProcessor.blob_to_cv_image(image_data)
                    preprocessed_ref = ImageProcessor.preprocess_image(ref_image)

                    # Match images
                    similarity = ImageProcessor.match_with_template(
                        preprocessed_query, preprocessed_ref
                    )

                    # Update best match if better
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = character

                except Exception as e:
                    logger.error(f"Error processing character image {character.id}/{image_id}: {e}")

        # Check against threshold if set
        if self.similarity_threshold is None:
            logger.info(
                f"Best match: ID={best_match.id if best_match else None}, similarity={best_similarity:.4f} (no threshold applied)")
            return best_match, best_similarity
        elif best_similarity >= self.similarity_threshold:
            logger.info(
                f"Best match: ID={best_match.id if best_match else None}, similarity={best_similarity:.4f} (threshold={self.similarity_threshold:.4f})")
            return best_match, best_similarity
        else:
            logger.info(
                f"No match found with similarity >= {self.similarity_threshold:.4f} (best was {best_similarity:.4f})")
            return None, best_similarity

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
            cache_key = ImageProcessor.compute_image_hash(query_image)

            # Check if result is in cache
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                logger.info(f"Cache hit for image from {image_source}")

                # Reconstruct MatchResult from cached data
                if cached_result is None:
                    return MatchResult(None, 0.0)

                character, similarity = cached_result
                return MatchResult(character, similarity)

            logger.info(f"Cache miss for image from {image_source}, performing matching...")

            # Perform matching
            character, similarity = self.find_best_match(query_image)

            # Create result object and cache results
            result = MatchResult(character, similarity)

            # Cache the result
            self.cache[cache_key] = (character, similarity)

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
                query_image = ImageProcessor.load_image_safely(image)
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
                query_image = ImageProcessor.pil_to_cv(image)
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
        logger.info("Character detector cache cleared")