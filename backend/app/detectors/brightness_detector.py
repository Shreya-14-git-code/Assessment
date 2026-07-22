import cv2
import numpy as np
from typing import Dict, Any

def analyze_brightness(image_path: str) -> Dict[str, Any]:
    """
    Analyzes brightness, low-light, and over-exposure.
    """
    image = cv2.imread(image_path)
    if image is None:
        return {
            "is_low_light": False,
            "is_overexposed": False,
            "brightness_score": 0.0,
            "contrast_score": 0.0,
            "issue": "Failed to decode image matrix"
        }
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_luminance = float(np.mean(gray))
    std_luminance = float(np.std(gray))
    
    is_low_light = mean_luminance < 40.0
    is_overexposed = mean_luminance > 220.0
    
    issue = None
    if is_low_light:
        issue = "Low light / dark image detected"
    elif is_overexposed:
        issue = "Severe over-exposure / glare detected"
    elif std_luminance < 20.0:
        issue = "Extremely low image contrast detected"
        
    return {
        "is_low_light": is_low_light,
        "is_overexposed": is_overexposed,
        "brightness_score": round(mean_luminance, 2),
        "contrast_score": round(std_luminance, 2),
        "issue": issue
    }
