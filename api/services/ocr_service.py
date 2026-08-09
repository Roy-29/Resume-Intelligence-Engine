import pytesseract
from PIL import Image
import os
import logging

logger = logging.getLogger(__name__)

# Point to the Tesseract executable (Manual Install Path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRService:
    """Service to handle text extraction from image-based resumes."""

    @staticmethod
    def extract_text(image_path):
        """Extracts text from a given image path using Tesseract."""
        if not os.path.exists(image_path):
            logger.error(f"Image not found at path: {image_path}")
            return ""

        try:
            img = Image.open(image_path)
            return OCRService.extract_text_from_image(img)
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract is not installed or not in PATH. OCR failed.")
            return ""
        except Exception as e:
            logger.error(f"OCR Error extracting text from {image_path}: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_image(img):
        """Extracts text from a PIL Image object using Tesseract.
        Used by the OCR fallback in candidate/engine.py for scanned PDFs.
        """
        try:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            extracted_text = pytesseract.image_to_string(img)
            return extracted_text.strip()
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract is not installed or not in PATH. OCR failed.")
            return ""
        except Exception as e:
            logger.error(f"OCR Error extracting text from image: {str(e)}")
            return ""
