import io
from typing import Optional, Union

import cv2
import imagehash
import numpy as np
from PIL import Image


class ImageProcessor:
    """
    Utility class for image processing operations.
    Provides methods for converting between image formats, preprocessing, and image comparison.
    """
    
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
    def cv_to_pil(cv_image: np.ndarray) -> Image.Image:
        """
        Convert an OpenCV image to PIL format.
        
        Args:
            cv_image: OpenCV image (numpy array in BGR format)
            
        Returns:
            PIL Image object
        """
        # Convert from BGR to RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        return Image.fromarray(rgb_image)
    
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
                # Convert to OpenCV format
                return ImageProcessor.pil_to_cv(pil_img)
        except Exception as e:
            print(f"Failed to load image from {image_path}: {e}")
            return None
    
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
    def compute_image_hash(image: Union[str, np.ndarray, Image.Image]) -> str:
        """
        Compute a perceptual hash for an image.
        
        Args:
            image: Input image as file path, OpenCV image (numpy array), or PIL Image
            
        Returns:
            String hash representing the image
        """
        # Convert input to PIL Image
        pil_img = None
        
        if isinstance(image, str):
            # Load from file path
            pil_img = Image.open(image)
        elif isinstance(image, np.ndarray):
            # Convert from OpenCV to PIL format
            if len(image.shape) == 3:
                pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_img = Image.fromarray(image)
        elif isinstance(image, Image.Image):
            pil_img = image
        else:
            raise TypeError(f"Unsupported image type: {type(image)}. Must be str, np.ndarray, or PIL.Image.Image")
        
        # Compute perceptual hash (more robust to minor variations)
        phash = str(imagehash.phash(pil_img))
        return phash
    
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
            return float(max_val)  # Convert to native Python float
        except cv2.error as e:
            print(f"Template matching error: {e}")
            return 0.0
    
    @staticmethod
    def image_to_blob(image: Union[str, np.ndarray, Image.Image]) -> bytes:
        """
        Convert an image to binary blob data for storage.
        
        Args:
            image: Input image as file path, OpenCV image, or PIL Image
            
        Returns:
            Binary blob data
        """
        if isinstance(image, str):
            # Load from file path
            with open(image, 'rb') as f:
                return f.read()
        elif isinstance(image, np.ndarray):
            # Convert OpenCV image to binary
            is_success, buffer = cv2.imencode('.png', image)
            if not is_success:
                raise ValueError("Failed to encode OpenCV image")
            return buffer.tobytes()
        elif isinstance(image, Image.Image):
            # Convert PIL image to binary
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            return buffer.getvalue()
        else:
            raise TypeError(f"Unsupported image type: {type(image)}. Must be str, np.ndarray, or PIL.Image.Image")
    
    @staticmethod
    def blob_to_cv_image(blob_data: bytes) -> np.ndarray:
        """
        Convert binary blob data to OpenCV image format.
        
        Args:
            blob_data: Binary image data
            
        Returns:
            OpenCV image (numpy array)
        """
        # Convert binary data to numpy array
        nparr = np.frombuffer(blob_data, np.uint8)
        
        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Failed to decode image from blob data")
            
        return img
    
    @staticmethod
    def blob_to_pil_image(blob_data: bytes) -> Image.Image:
        """
        Convert binary blob data to PIL image format.
        
        Args:
            blob_data: Binary image data
            
        Returns:
            PIL Image object
        """
        # Create BytesIO object from blob data
        buffer = io.BytesIO(blob_data)
        
        # Open as PIL image
        img = Image.open(buffer)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        return img 
