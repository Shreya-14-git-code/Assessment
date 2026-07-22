import re
import cv2
import numpy as np
from typing import Dict, Any, Optional

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

INDIAN_PLATE_PATTERNS = [
    # Standard: State (2 letters) + District (1-2 digits) + Series (1-3 letters) + Number (4 digits)
    # e.g., MH12AB1234, KA01M9999, DL3CCE1234, HR26DQ5555
    r"^[A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,3}\s?[0-9]{4}$",
    
    # Bharat (BH) Series: Year (2 digits) + BH + Number (4 digits) + Letters (1-2)
    # e.g., 22BH1234A, 21BH9876XY
    r"^[0-9]{2}\s?BH\s?[0-9]{4}\s?[A-Z]{1,2}$",

    # Vintage / Special Military (e.g., 09D123456X)
    r"^[0-9]{2}\s?[A-Z]\s?[0-9]{5,6}\s?[A-Z]$"
]

def clean_ocr_text(raw_text: str) -> str:
    """Cleans raw OCR output into normalized alphanumeric upper string."""
    cleaned = re.sub(r"[^A-Z0-9]", "", raw_text.upper())
    return cleaned

def validate_indian_license_plate(plate_text: str) -> bool:
    """Checks if plate string conforms to standard Indian vehicle number formats."""
    text = clean_ocr_text(plate_text)
    if not text or len(text) < 6 or len(text) > 13:
        return False
        
    for pattern in INDIAN_PLATE_PATTERNS:
        if re.match(pattern, text):
            return True
    return False

def extract_and_validate_license_plate(image_path: str) -> Dict[str, Any]:
    """
    Extracts license plate text from image and validates format against Indian vehicle standards.
    """
    extracted_text: Optional[str] = None
    is_valid = False
    confidence = 0.0

    image = cv2.imread(image_path)
    if image is None:
        return {
            "license_plate_text": None,
            "is_valid_license_plate": False,
            "plate_confidence": 0.0,
            "issue": "Failed to decode image matrix for OCR"
        }

    # Preprocess image for OCR (grayscale, bilateral filter, adaptive threshold)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    raw_text = ""
    if PYTESSERACT_AVAILABLE:
        try:
            # Custom Tesseract configuration for OCR
            custom_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            raw_text = pytesseract.image_to_string(thresh, config=custom_config)
        except Exception:
            pass

    # If tesseract is missing or yielded empty string, run contour ROI search
    cleaned = clean_ocr_text(raw_text)
    
    if not cleaned:
        # Contour detection fallback for candidate rectangular plate area
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = w / float(h)
                if 2.0 <= aspect_ratio <= 6.0:  # Typical license plate ratio
                    confidence = 70.0
                    break

    # Look for Indian plate pattern anywhere in extracted text
    found_match = None
    for pattern in INDIAN_PLATE_PATTERNS:
        match = re.search(pattern.replace("^", "").replace("$", ""), cleaned)
        if match:
            found_match = match.group(0)
            is_valid = True
            confidence = 95.0
            break

    if found_match:
        extracted_text = found_match
    elif cleaned:
        extracted_text = cleaned
        confidence = 50.0
        is_valid = validate_indian_license_plate(cleaned)

    issue = None
    if not extracted_text:
        issue = "No readable license plate text detected in image"
    elif not is_valid:
        issue = f"Invalid vehicle number plate format: '{extracted_text}'"

    return {
        "license_plate_text": extracted_text,
        "is_valid_license_plate": is_valid,
        "plate_confidence": round(confidence, 2),
        "issue": issue
    }
