from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import MediaJob, AnalysisResult
from backend.app.schemas import StatusResponse, ResultsResponse, FailureResponse, AnalysisDetail

router = APIRouter(prefix="/api/v1/media", tags=["Media Status & Results"])

@router.get("/{job_id}/status", response_model=StatusResponse)
def get_processing_status(job_id: str, db: Session = Depends(get_db)):
    """Fetches the asynchronous processing status of a media job."""
    job = db.query(MediaJob).filter(MediaJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Media job '{job_id}' not found")

    return StatusResponse(
        job_id=job.id,
        status=job.status,
        original_filename=job.original_filename,
        file_size=job.file_size,
        created_at=job.created_at,
        updated_at=job.updated_at,
        processing_time_ms=job.processing_time_ms,
        failure_reason=job.failure_reason
    )

@router.get("/{job_id}/results", response_model=ResultsResponse)
def get_analysis_results(job_id: str, db: Session = Depends(get_db)):
    """Fetches full heuristic analysis results for a completed media job."""
    job = db.query(MediaJob).filter(MediaJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Media job '{job_id}' not found")

    if job.status == "pending" or job.status == "processing":
        raise HTTPException(
            status_code=425,  # Too Early
            detail=f"Analysis is still in progress (Current status: '{job.status}')"
        )
    elif job.status == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Job failed during processing. Reason: {job.failure_reason}"
        )

    result = job.analysis_result
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result record not found")

    detail_dto = AnalysisDetail(
        is_blurry=result.is_blurry,
        blur_score=result.blur_score,
        is_low_light=result.is_low_light,
        is_overexposed=result.is_overexposed,
        brightness_score=result.brightness_score,
        is_duplicate=result.is_duplicate,
        duplicate_of_job_id=result.duplicate_of_job_id,
        duplicate_distance=result.duplicate_distance,
        is_screenshot=result.is_screenshot,
        screenshot_score=result.screenshot_score,
        is_tampered=result.is_tampered,
        tamper_score=result.tamper_score,
        license_plate_text=result.license_plate_text,
        is_valid_license_plate=result.is_valid_license_plate,
        plate_confidence=result.plate_confidence
    )

    return ResultsResponse(
        job_id=job.id,
        status=job.status,
        original_filename=job.original_filename,
        overall_score=result.overall_score,
        risk_level=result.risk_level,
        detected_issues=result.detected_issues or [],
        details=detail_dto,
        metrics=result.metrics_json or {},
        created_at=result.created_at
    )

@router.get("/{job_id}/failure", response_model=FailureResponse)
def get_failure_reason(job_id: str, db: Session = Depends(get_db)):
    """Fetches detailed failure reason if the job failed."""
    job = db.query(MediaJob).filter(MediaJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Media job '{job_id}' not found")

    if job.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Job '{job_id}' is not in failed state. Current status: '{job.status}'"
        )

    return FailureResponse(
        job_id=job.id,
        status=job.status,
        failure_reason=job.failure_reason or "Unknown internal error occurred during processing",
        updated_at=job.updated_at
    )
