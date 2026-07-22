from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import MediaJob, AnalysisResult
from backend.app.schemas import MediaListResponse, MediaJobItem, AnalyticsSummaryResponse

router = APIRouter(prefix="/api/v1", tags=["Analytics & List"])

@router.get("/media/list", response_model=MediaListResponse)
def list_media_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Paginated list of uploaded media jobs with optional filtering by status or risk level."""
    query = db.query(MediaJob)
    
    if status:
        query = query.filter(MediaJob.status == status)
        
    if risk_level:
        query = query.join(AnalysisResult).filter(AnalysisResult.risk_level == risk_level)

    total = query.count()
    offset = (page - 1) * limit
    jobs = query.order_by(MediaJob.created_at.desc()).offset(offset).limit(limit).all()

    items: List[MediaJobItem] = []
    for j in jobs:
        res = j.analysis_result
        items.append(MediaJobItem(
            job_id=j.id,
            filename=j.original_filename,
            status=j.status,
            created_at=j.created_at,
            overall_score=res.overall_score if res else None,
            risk_level=res.risk_level if res else None,
            issues_count=len(res.detected_issues) if res and res.detected_issues else 0
        ))

    return MediaListResponse(
        total=total,
        page=page,
        limit=limit,
        items=items
    )

@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Computes aggregate analytics statistics across all processed media jobs."""
    total_jobs = db.query(MediaJob).count()
    completed_jobs = db.query(MediaJob).filter(MediaJob.status == "completed").count()
    pending_jobs = db.query(MediaJob).filter(MediaJob.status == "pending").count()
    failed_jobs = db.query(MediaJob).filter(MediaJob.status == "failed").count()

    pass_count = db.query(AnalysisResult).filter(AnalysisResult.risk_level == "PASS").count()
    warning_count = db.query(AnalysisResult).filter(AnalysisResult.risk_level == "WARNING").count()
    reject_count = db.query(AnalysisResult).filter(AnalysisResult.risk_level == "REJECT").count()

    # Calculate average processing time
    avg_time = db.query(func.avg(MediaJob.processing_time_ms)).filter(MediaJob.status == "completed").scalar() or 0.0

    # Issues breakdown
    all_results = db.query(AnalysisResult).all()
    issues_breakdown = {
        "blur": 0,
        "low_light": 0,
        "overexposed": 0,
        "duplicate": 0,
        "screenshot": 0,
        "tampered": 0,
        "invalid_license_plate": 0
    }

    for r in all_results:
        if r.is_blurry:
            issues_breakdown["blur"] += 1
        if r.is_low_light:
            issues_breakdown["low_light"] += 1
        if r.is_overexposed:
            issues_breakdown["overexposed"] += 1
        if r.is_duplicate:
            issues_breakdown["duplicate"] += 1
        if r.is_screenshot:
            issues_breakdown["screenshot"] += 1
        if r.is_tampered:
            issues_breakdown["tampered"] += 1
        if not r.is_valid_license_plate:
            issues_breakdown["invalid_license_plate"] += 1

    return AnalyticsSummaryResponse(
        total_jobs=total_jobs,
        completed_jobs=completed_jobs,
        pending_jobs=pending_jobs,
        failed_jobs=failed_jobs,
        pass_count=pass_count,
        warning_count=warning_count,
        reject_count=reject_count,
        issues_breakdown=issues_breakdown,
        avg_processing_time_ms=round(avg_time, 2)
    )
