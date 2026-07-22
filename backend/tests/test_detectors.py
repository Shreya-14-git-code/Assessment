import os
import cv2
import numpy as np
import pytest
from PIL import Image

from backend.app.detectors.blur_detector import analyze_blur
from backend.app.detectors.brightness_detector import analyze_brightness
from backend.app.detectors.screenshot_detector import analyze_screenshot_heuristics
from backend.app.detectors.tamper_detector import analyze_editing_and_tampering
from backend.app.detectors.ocr_detector import validate_indian_license_plate, clean_ocr_text

@pytest.fixture
def sharp_image_file(tmp_path):
    path = str(tmp_path / "sharp.jpg")
    # Generate sharp checkerboard matrix
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    img[::40, ::40] = 255
    cv2.imwrite(path, img)
    return path

@pytest.fixture
def blurry_image_file(tmp_path):
    path = str(tmp_path / "blurry.jpg")
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    img[::40, ::40] = 255
    blurred = cv2.GaussianBlur(img, (51, 51), 0)
    cv2.imwrite(path, blurred)
    return path

@pytest.fixture
def dark_image_file(tmp_path):
    path = str(tmp_path / "dark.jpg")
    img = np.ones((400, 400, 3), dtype=np.uint8) * 15
    cv2.imwrite(path, img)
    return path

def test_blur_detector(sharp_image_file, blurry_image_file):
    sharp_res = analyze_blur(sharp_image_file)
    blurry_res = analyze_blur(blurry_image_file)
    
    assert sharp_res["is_blurry"] is False
    assert sharp_res["blur_score"] > 250.0

    assert blurry_res["is_blurry"] is True
    assert blurry_res["severity"] in ["moderate", "severe"]

def test_brightness_detector(dark_image_file):
    dark_res = analyze_brightness(dark_image_file)
    assert dark_res["is_low_light"] is True
    assert dark_res["brightness_score"] < 40.0

def test_indian_plate_regex_validator():
    # Valid test plates
    assert validate_indian_license_plate("MH12AB1234") is True
    assert validate_indian_license_plate("KA01M9999") is True
    assert validate_indian_license_plate("22BH1234A") is True  # Bharat Series
    assert validate_indian_license_plate("DL3CCE1234") is True

    # Invalid test plates
    assert validate_indian_license_plate("INVALID123") is False
    assert validate_indian_license_plate("123456") is False
    assert validate_indian_license_plate("ABCDEFG") is False

def test_clean_ocr_text():
    assert clean_ocr_text("MH-12 AB 1234!") == "MH12AB1234"
    assert clean_ocr_text(" 22 bh 1234 a ") == "22BH1234A"
