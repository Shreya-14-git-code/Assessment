import asyncio
import logging
import traceback

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import MediaJob, AnalysisResult, PerceptualHash
from backend.app.detectors.pipeline import run_pipeline

logger = logging.getLogger("queue_service")

async def process_media_job_async(job_id: str):
    """
    Background worker function that processes an uploaded media job asynchronously.
    Updates DB status: pending -> processing -> completed / failed.
    """
    db: Session = SessionLocal()
    try:
        job = db.query(MediaJob).filter(MediaJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in DB")
            return

        # 1. Update status to processing
        job.status = "processing"
        db.commit()

        # 2. Run heuristic image analysis pipeline
        results = run_pipeline(image_path=job.file_path, job_id=job.id, db=db)

        # 3. Store Analysis Result in DB
        details = results["details"]
        analysis_record = AnalysisResult(
            job_id=job.id,
            overall_score=results["overall_score"],
            risk_level=results["risk_level"],
            is_blurry=details["is_blurry"],
            blur_score=details["blur_score"],
            is_low_light=details["is_low_light"],
            is_overexposed=details["is_overexposed"],
            brightness_score=details["brightness_score"],
            is_duplicate=details["is_duplicate"],
            duplicate_of_job_id=details["duplicate_of_job_id"],
            duplicate_distance=details["duplicate_distance"],
            is_screenshot=details["is_screenshot"],
            screenshot_score=details["screenshot_score"],
            is_tampered=details["is_tampered"],
            tamper_score=details["tamper_score"],
            license_plate_text=details["license_plate_text"],
            is_valid_license_plate=details["is_valid_license_plate"],
            plate_confidence=details["plate_confidence"],
            detected_issues=results["detected_issues"],
            metrics_json=results["metrics"]
        )
        db.add(analysis_record)

        # 4. Store Perceptual Hashes for future duplicate detection
        hashes = results["hashes"]
        hash_record = PerceptualHash(
            job_id=job.id,
            dhash=hashes["dhash"],
            phash=hashes["phash"],
            ahash=hashes["ahash"]
        )
        db.add(hash_record)

        # 5. Update job status to completed
        job.status = "completed"
        job.processing_time_ms = results["processing_time_ms"]
        db.commit()
        logger.info(f"Job {job_id} successfully completed in {results['processing_time_ms']}ms")

    except Exception as e:
        db.rollback()
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Error processing job {job_id}: {err_msg}")
        
        job = db.query(MediaJob).filter(MediaJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.failure_reason = str(e)
            db.commit()
    finally:
        db.close()
