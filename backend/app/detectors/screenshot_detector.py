import cv2
import numpy as np
from PIL import Image, ExifTags
from typing import Dict, Any

def analyze_screenshot_heuristics(image_path: str) -> Dict[str, Any]:
    """
    Detects if an image is likely a mobile screenshot or photo-of-a-screen.
    Checks:
    1. EXIF metadata tags (missing camera EXIF info like lens/shutter/aperture or screenshot software tag).
    2. Display aspect ratios (19.5:9, 20:9, 16:9, 4:3).
    3. Moiré grid frequency patterns in 2D FFT spectrum.
    """
    screenshot_score = 0.0
    reasons = []

    # 1. EXIF Inspection
    missing_exif_camera = False
    is_software_screenshot = False
    
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            aspect_ratio = max(width, height) / max(1, min(width, height))
            
            exif_data = img._getexif()
            if not exif_data:
                missing_exif_camera = True
                screenshot_score += 25.0
                reasons.append("Missing EXIF camera metadata")
            else:
                exif = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items() if k in ExifTags.TAGS}
                software = str(exif.get("Software", "")).lower()
                make = str(exif.get("Make", ""))
                model = str(exif.get("Model", ""))
                
                if "screenshot" in software or "ios" in software:
                    is_software_screenshot = True
                    screenshot_score += 60.0
                    reasons.append("EXIF software explicitly tags screenshot")
                elif not make and not model:
                    screenshot_score += 20.0
                    reasons.append("Missing camera Make/Model EXIF tags")

            # Aspect Ratio check for screen sizes (19.5:9 ~ 2.166, 20:9 ~ 2.22, 16:9 ~ 1.777)
            if any(abs(aspect_ratio - target) < 0.05 for target in [2.166, 2.222, 1.777, 2.0]):
                screenshot_score += 20.0
                reasons.append(f"Screen standard aspect ratio detected ({round(aspect_ratio, 2)})")

    except Exception:
        pass

    # 2. Moiré Pattern Frequency Analysis via 2D FFT
    cv_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    moire_detected = False
    if cv_img is not None:
        # Resize to fixed standard matrix for FFT
        resized = cv2.resize(cv_img, (512, 512))
        f = np.fft.fft2(resized)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)
        
        # Calculate energy concentration in mid-high frequencies (hallmark of screen grid pattern)
        h, w = magnitude_spectrum.shape
        center_h, center_w = h // 2, w // 2
        # Mask out DC component
        magnitude_spectrum[center_h-10:center_h+10, center_w-10:center_w+10] = 0
        
        high_freq_peaks = np.sum(magnitude_spectrum > np.percentile(magnitude_spectrum, 99.5))
        if high_freq_peaks > 250:
            moire_detected = True
            screenshot_score += 35.0
            reasons.append("High-frequency Moiré grid pattern detected (Photo-of-screen heuristic)")

    is_screenshot = screenshot_score >= 50.0
    
    return {
        "is_screenshot": is_screenshot,
        "screenshot_score": round(min(100.0, screenshot_score), 2),
        "reasons": reasons,
        "issue": "Screenshot or photo-of-screen detected" if is_screenshot else None
    }
