import os
import io
import cv2
import numpy as np
from PIL import Image, ImageChops, ExifTags
from typing import Dict, Any

def analyze_editing_and_tampering(image_path: str) -> Dict[str, Any]:
    """
    Analyzes image tampering / suspicious editing using:
    1. Error Level Analysis (ELA): Resaves image at 95% JPEG quality and compares pixel compression artifacts.
    2. Editing Software EXIF tag detection (Photoshop, GIMP, Canva, PicsArt, etc.).
    """
    tamper_score = 0.0
    reasons = []

    # 1. ELA Compression Disparity Analysis
    try:
        with Image.open(image_path) as orig_img:
            orig_rgb = orig_img.convert("RGB")
            
            # Save temporary 95% quality JPEG in memory
            buffer = io.BytesIO()
            orig_rgb.save(buffer, format="JPEG", quality=95)
            buffer.seek(0)
            resaved_img = Image.open(buffer)
            
            # Calculate absolute difference image
            ela_diff = ImageChops.difference(orig_rgb, resaved_img)
            extrema = ela_diff.getextrema()
            
            # Find max difference across channels
            max_diff = max([ex[1] for ex in extrema]) if extrema else 0
            
            # Convert ELA diff to numpy array for variance analysis
            ela_arr = np.array(ela_diff)
            mean_diff = float(np.mean(ela_arr))
            std_diff = float(np.std(ela_arr))
            
            # Suspicious localized compression differences (editing/splicing)
            if std_diff > 18.0 or max_diff > 120:
                tamper_score += 45.0
                reasons.append(f"High localized ELA compression variance detected (std: {round(std_diff, 1)}, max: {max_diff})")
            elif std_diff > 12.0:
                tamper_score += 25.0
                reasons.append(f"Moderate ELA compression disparity detected (std: {round(std_diff, 1)})")
    except Exception as e:
        pass

    # 2. Software EXIF Inspection
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                exif = {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items() if k in ExifTags.TAGS}
                software = str(exif.get("Software", "")).lower()
                editing_tools = ["photoshop", "gimp", "canva", "picsart", "lightroom", "pixlr", "snapseed", "aftereffects"]
                for tool in editing_tools:
                    if tool in software:
                        tamper_score += 50.0
                        reasons.append(f"Image edited using software tag: '{software}'")
                        break
    except Exception:
        pass

    is_tampered = tamper_score >= 40.0

    return {
        "is_tampered": is_tampered,
        "tamper_score": round(min(100.0, tamper_score), 2),
        "reasons": reasons,
        "issue": "Suspicious editing or image tampering detected" if is_tampered else None
    }
