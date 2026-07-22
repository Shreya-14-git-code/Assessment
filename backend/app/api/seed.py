import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.app.config import UPLOAD_DIR
from backend.app.database import get_db
from backend.app.models import MediaJob
from backend.app.services.queue_service import process_media_job_async

router = APIRouter(prefix="/api/v1", tags=["Seed Test Data"])

def create_synthetic_image(filename: str, mode: str) -> str:
    """Generates a synthetic test vehicle image illustrating a specific issue mode."""
    target_path = UPLOAD_DIR / filename
    
    # Create base canvas (800x600)
    img = Image.new("RGB", (800, 600), color=(200, 200, 210))
    draw = ImageDraw.Draw(img)
    
    # Draw simple vehicle shape
    draw.rectangle([150, 250, 650, 480], fill=(40, 70, 120), outline=(0, 0, 0), width=3)
    draw.rectangle([250, 150, 550, 250], fill=(60, 90, 150), outline=(0, 0, 0), width=3)
    draw.ellipse([200, 430, 300, 530], fill=(20, 20, 20))
    draw.ellipse([500, 430, 600, 530], fill=(20, 20, 20))

    # Draw License Plate Box
    draw.rectangle([300, 380, 500, 440], fill=(255, 255, 255), outline=(0, 0, 0), width=4)
    
    plate_text = "MH 12 AB 1234" if mode != "invalid_plate" else "INVALID_PLATE_1"
    draw.text((320, 395), plate_text, fill=(0, 0, 0))

    # Apply Mode Specific Distortions
    arr = np.array(img)
    
    if mode == "blurry":
        # Apply heavy Gaussian blur
        arr = cv2.GaussianBlur(arr, (45, 45), 0)
    elif mode == "low_light":
        # Darken image
        arr = (arr * 0.15).astype(np.uint8)
    elif mode == "overexposed":
        # Brighten image
        arr = cv2.add(arr, 180)
    elif mode == "screenshot":
        # Add screen status bar and crop ratio
        img_with_bar = Image.fromarray(arr)
        draw_bar = ImageDraw.Draw(img_with_bar)
        draw_bar.rectangle([0, 0, 800, 30], fill=(0, 0, 0))
        draw_bar.text((10, 8), "9:41 AM  100%", fill=(255, 255, 255))
        arr = np.array(img_with_bar)

    cv2.imwrite(str(target_path), cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
    return str(target_path)

@router.post("/seed", status_code=201)
def seed_test_images(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Generates 5 synthetic vehicle test images (Normal, Blurry, Dark, Duplicate, Invalid Plate) and enqueues them."""
    test_cases = [
        ("vehicle_clean.jpg", "clean"),
        ("vehicle_blurry.jpg", "blurry"),
        ("vehicle_dark.jpg", "low_light"),
        ("vehicle_duplicate_1.jpg", "clean"),  # Duplicate target
        ("vehicle_duplicate_2.jpg", "clean"),  # Will trigger duplicate check
        ("vehicle_bad_plate.jpg", "invalid_plate")
    ]

    created_jobs = []
    for filename, mode in test_cases:
        path = create_synthetic_image(filename, mode)
        file_size = os.path.getsize(path)
        
        job = MediaJob(
            original_filename=filename,
            file_path=path,
            file_size=file_size,
            mime_type="image/jpeg",
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        background_tasks.add_task(process_media_job_async, job.id)
        created_jobs.append(job.id)

    return {
        "message": f"Successfully seeded {len(created_jobs)} test media jobs",
        "job_ids": created_jobs
    }
