from PIL import Image
import imagehash
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models import PerceptualHash
from backend.app.config import DUPLICATE_HAMMING_THRESHOLD

def generate_hashes(image_path: str) -> Dict[str, str]:
    """Generates dHash, pHash, and aHash for an image file."""
    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        dhash_val = str(imagehash.dhash(img_rgb))
        phash_val = str(imagehash.phash(img_rgb))
        ahash_val = str(imagehash.average_hash(img_rgb))
    return {
        "dhash": dhash_val,
        "phash": phash_val,
        "ahash": ahash_val
    }

def check_duplicate(
    image_path: str,
    db: Session,
    current_job_id: str
) -> Dict[str, Any]:
    """
    Computes perceptual hashes and checks against database records for near-duplicates.
    """
    hashes = generate_hashes(image_path)
    curr_dhash = imagehash.hex_to_hash(hashes["dhash"])
    curr_phash = imagehash.hex_to_hash(hashes["phash"])
    
    # Query stored hashes from DB
    existing_hashes = db.query(PerceptualHash).filter(PerceptualHash.job_id != current_job_id).all()
    
    closest_match_job_id: Optional[str] = None
    min_distance = 999
    
    for record in existing_hashes:
        rec_dhash = imagehash.hex_to_hash(record.dhash)
        rec_phash = imagehash.hex_to_hash(record.phash)
        
        # Combined Hamming distance
        dist_d = curr_dhash - rec_dhash
        dist_p = curr_phash - rec_phash
        dist = min(dist_d, dist_p)
        
        if dist < min_distance:
            min_distance = dist
            closest_match_job_id = record.job_id
            
    is_duplicate = min_distance <= DUPLICATE_HAMMING_THRESHOLD
    
    return {
        "is_duplicate": is_duplicate,
        "hashes": hashes,
        "duplicate_of_job_id": closest_match_job_id if is_duplicate else None,
        "duplicate_distance": min_distance if closest_match_job_id else None,
        "issue": f"Duplicate image detected (Matches job {closest_match_job_id[:8]}... with Hamming distance {min_distance})" if is_duplicate else None
    }
