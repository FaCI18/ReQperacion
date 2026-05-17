"""OCR processing module for ReQperacion.

Uses Tesseract OCR with multiple preprocessing strategies to extract text from images.
Supports: PNG, JPG, JPEG, BMP, TIFF, WEBP

The module tries multiple preprocessing approaches and returns the best result:
1. Original image (upscaled) - works for clear, high-quality images
2. Grayscale + contrast enhancement - works for slightly noisy images
3. Gentle adaptive threshold - works for documents with varying lighting
4. OTSU binarization - works for images with uniform background (signs, screenshots)
"""

import os
import cv2
import numpy as np
import logging
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

# Image file extensions that support OCR
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def is_image_file(filename: str) -> bool:
    """Check if a file is a supported image type."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in IMAGE_EXTENSIONS


def _upscale(image: np.ndarray, factor: float = 2.0) -> np.ndarray:
    """Upscale image for better OCR on small text."""
    h, w = image.shape[:2]
    new_w = int(w * factor)
    new_h = int(h * factor)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)


def _strategy_original(image: Image.Image) -> Image.Image:
    """
    Strategy 1: Just upscale the original image.
    Best for clean, high-quality images with clear text.
    """
    img = np.array(image.convert("RGB"))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    # Upscale 2x for better OCR
    img = _upscale(img, 2.0)
    # Convert to grayscale for Tesseract (works better)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return Image.fromarray(gray, mode="L")


def _strategy_grayscale_contrast(image: Image.Image) -> Image.Image:
    """
    Strategy 2: Grayscale + contrast enhancement + slight sharpening.
    Best for images with faded or low-contrast text.
    No binarization - preserves grayscale information.
    """
    # Enhance contrast first (PIL works well for this)
    enhancer = ImageEnhance.Contrast(image)
    enhanced = enhancer.enhance(1.5)

    # Convert to OpenCV
    img = np.array(enhanced.convert("RGB"))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Upscale
    img = _upscale(img, 2.0)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # This enhances local contrast without amplifying noise too much
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    return Image.fromarray(enhanced_gray, mode="L")


def _strategy_gentle_threshold(image: Image.Image) -> Image.Image:
    """
    Strategy 3: Gentle adaptive threshold with larger block size.
    Best for documents or images with uneven lighting.
    Less aggressive than the previous implementation.
    """
    img = np.array(image.convert("RGB"))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Upscale
    img = _upscale(img, 2.0)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur (mild)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Adaptive threshold with LARGER block size and higher C value
    # This is LESS aggressive than before (blockSize=11, C=2 was too aggressive)
    # blockSize=31 means it looks at a larger area, C=4 means it's more lenient
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,  # larger block size = less sensitive to local variations
        4,   # higher C = less likely to classify pixels as text
    )

    return Image.fromarray(binary, mode="L")


def _strategy_otsu(image: Image.Image) -> Image.Image:
    """
    Strategy 4: OTSU's global threshold.
    Best for images with uniform background like traffic signs, screenshots.
    OTSU automatically finds the optimal threshold value.
    """
    img = np.array(image.convert("RGB"))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Upscale
    img = _upscale(img, 2.0)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply slight Gaussian blur
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # OTSU threshold - automatically determines the best threshold value
    # This works very well for images with bimodal histograms
    # (e.g., dark text on light background or vice versa)
    _, binary = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    # Ensure dark text on light background (Tesseract prefers this)
    white_pixels = np.sum(binary == 255)
    black_pixels = np.sum(binary == 0)
    if black_pixels > white_pixels:
        binary = cv2.bitwise_not(binary)

    return Image.fromarray(binary, mode="L")


def extract_text_from_image(file_path: str, lang: str = "spa+eng") -> str:
    """
    Extract text from an image using Tesseract OCR with multiple strategies.

    Tries multiple preprocessing approaches and returns the best result.
    This significantly improves OCR accuracy across different image types.

    Args:
        file_path: Path to the image file
        lang: Tesseract language(s) - default Spanish + English

    Returns:
        Extracted text string, or empty string on failure
    """
    if not os.path.exists(file_path):
        logger.warning(f"Image file not found: {file_path}")
        return ""

    try:
        import pytesseract

        # Open the image with Pillow
        image = Image.open(file_path)
        logger.info(
            f"Processing image: {file_path} "
            f"(size: {image.size}, mode: {image.mode})"
        )

        # Try multiple strategies and pick the best result
        strategies = [
            ("original (upscaled)", _strategy_original),
            ("grayscale + contrast", _strategy_grayscale_contrast),
            ("gentle adaptive threshold", _strategy_gentle_threshold),
            ("OTSU binarization", _strategy_otsu),
        ]

        best_text = ""
        best_len = 0

        for strategy_name, strategy_fn in strategies:
            try:
                processed = strategy_fn(image)

                text = pytesseract.image_to_string(
                    processed,
                    lang=lang,
                    config="--psm 3 --oem 3",
                )
                text = text.strip()

                logger.info(
                    f"  Strategy '{strategy_name}': "
                    f"extracted {len(text)} characters"
                )

                # Pick the strategy that extracted the most text
                if len(text) > best_len:
                    best_text = text
                    best_len = len(text)

            except Exception as e:
                logger.warning(
                    f"  Strategy '{strategy_name}' failed: {e}"
                )
                continue

        # If all strategies failed, try with just the original image
        if best_len == 0:
            logger.info("All strategies returned empty, trying raw image...")
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang=lang,
                    config="--psm 3 --oem 3",
                )
                best_text = text.strip()
                best_len = len(best_text)
                logger.info(
                    f"  Raw image: extracted {best_len} characters"
                )
            except Exception as e:
                logger.warning(f"  Raw image also failed: {e}")

        logger.info(
            f"OCR extracted {best_len} characters from "
            f"{os.path.basename(file_path)}"
        )
        if best_text:
            logger.info(f"Text preview: {best_text[:200]}")
        return best_text

    except ImportError:
        logger.error(
            "pytesseract is not installed. "
            "Run: pip install pytesseract"
        )
        return ""
    except Exception as e:
        logger.error(f"OCR processing error for {file_path}: {e}")
        return ""
