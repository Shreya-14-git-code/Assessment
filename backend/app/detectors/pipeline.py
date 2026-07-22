import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.detectors.blur_detector import analyze_blur
from backend.app.detectors.brightness_detector import analyze_brightness
from backend.app.detectors.duplicate_detector import check_duplicate, generate_hashes
from backend.app.detectors.screenshot_detector import analyze_screenshot_heuristics
from backend.app.detectors.tamper_detector import analyze_editing_and_tampering
from backend.app.detectors.ocr_detector import extract_and_validate_license_plate

def run_pipeline(
    image_path: str,
    job_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Executes the multi-heuristic media inspection pipeline on an uploaded image.
    Aggregates metrics and determines overall quality score and risk classification.
    """
    start_time = time.time()
    detected_issues: List[str] = []
    
    # 1. Blur Detection
    blur_res = analyze_blur(image_path)
    if blur_res.get("issue"):
        detected_issues.append(blur_res["issue"])

    # 2. Brightness & Exposure Analysis
    bright_res = analyze_brightness(image_path)
    if bright_res.get("issue"):
        detected_issues.append(bright_res["issue"])

    # 3. Duplicate Detection
    dup_res = check_duplicate(image_path, db, current_job_id=job_id)
    if dup_res.get("issue"):
        detected_issues.append(dup_res["issue"])

    # 4. Screenshot / Photo-of-Photo Detection
    ss_res = analyze_screenshot_heuristics(image_path)
    if ss_res.get("issue"):
        detected_issues.append(ss_res["issue"])

    # 5. Tampering & Suspicious Edit Analysis
    tamper_res = analyze_editing_and_tampering(image_path)
    if tamper_res.get("issue"):
        detected_issues.append(tamper_res["issue"])

    # 6. OCR & License Plate Validation
    ocr_res = extract_and_validate_license_plate(image_path)
    if ocr_res.get("issue"):
        detected_issues.append(ocr_res["issue"])

    # Calculate Overall Quality & Risk Score (100 = Perfect)
    score = 100.0
    
    if blur_res["is_blurry"]:
        score -= 25.0 if blur_res["severity"] == "severe" else 15.0
        
    if bright_res["is_low_light"] or bright_res["is_overexposed"]:
        score -= 20.0
        
    if dup_res["is_duplicate"]:
        score -= 40.0
        
    if ss_res["is_screenshot"]:
        score -= 30.0
        
    if tamper_res["is_tampered"]:
        score -= 35.0
        
    if not ocr_res["is_valid_license_plate"]:
        score -= 20.0

    overall_score = max(0.0, round(score, 1))

    # Risk Level Determination
    if dup_res["is_duplicate"] or tamper_res["is_tampered"] or overall_score < 45.0:
        risk_level = "REJECT"
    elif detected_issues or overall_score < 75.0:
        risk_level = "WARNING"
    else:
        risk_level = "PASS"

    processing_time_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "overall_score": overall_score,
        "risk_level": risk_level,
        "detected_issues": detected_issues,
        "processing_time_ms": processing_time_ms,
        "hashes": dup_res["hashes"],
        "details": {
            "is_blurry": blur_res["is_blurry"],
            "blur_score": blur_res["blur_score"],
            "is_low_light": bright_res["is_low_light"],
            "is_overexposed": bright_res["is_overexposed"],
            "brightness_score": bright_res["brightness_score"],
            "is_duplicate": dup_res["is_duplicate"],
            "duplicate_of_job_id": dup_res["duplicate_of_job_id"],
            "duplicate_distance": dup_res["duplicate_distance"],
            "is_screenshot": ss_res["is_screenshot"],
            "screenshot_score": ss_res["screenshot_score"],
            "is_tampered": tamper_res["is_tampered"],
            "tamper_score": tamper_res["tamper_score"],
            "license_plate_text": ocr_res["license_plate_text"],
            "is_valid_license_plate": ocr_res["is_valid_license_plate"],
            "plate_confidence": ocr_res["plate_confidence"]
        },
        "metrics": {
            "blur": blur_res,
            "brightness": bright_res,
            "duplicate": dup_res,
            "screenshot": ss_res,
            "tamper": tamper_res,
            "ocr": ocr_res
        }
    }
