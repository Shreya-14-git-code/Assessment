import cv2
import numpy as np
from typing import Dict, Any

def analyze_blur(image_path: str) -> Dict[str, Any]:
    """
    Analyzes image sharpness/blurriness using Laplacian Variance method.
    """
    image = cv2.imread(image_path)
    if image is None:
        return {
            "is_blurry": True,
            "blur_score": 0.0,
            "severity": "severe",
            "issue": "Failed to decode image matrix"
        }
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    is_blurry = laplacian_var < 250.0
    severity = "none"
    if laplacian_var < 100.0:
        severity = "severe"
    elif laplacian_var < 250.0:
        severity = "moderate"
        
    return {
        "is_blurry": is_blurry,
        "blur_score": round(laplacian_var, 2),
        "severity": severity,
        "issue": "Severe image blur detected" if severity == "severe" else ("Moderate image blur detected" if severity == "moderate" else None)
    }
