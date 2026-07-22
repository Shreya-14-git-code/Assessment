from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class UploadResponse(BaseModel):
    job_id: str
    filename: str
    file_size: int
    status: str
    created_at: datetime
    message: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    original_filename: str
    file_size: int
    created_at: datetime
    updated_at: datetime
    processing_time_ms: Optional[float] = None
    failure_reason: Optional[str] = None

class AnalysisDetail(BaseModel):
    is_blurry: bool
    blur_score: float
    is_low_light: bool
    is_overexposed: bool
    brightness_score: float
    is_duplicate: bool
    duplicate_of_job_id: Optional[str] = None
    duplicate_distance: Optional[int] = None
    is_screenshot: bool
    screenshot_score: float
    is_tampered: bool
    tamper_score: float
    license_plate_text: Optional[str] = None
    is_valid_license_plate: bool
    plate_confidence: float

class ResultsResponse(BaseModel):
    job_id: str
    status: str
    original_filename: str
    overall_score: float
    risk_level: str  # PASS, WARNING, REJECT
    detected_issues: List[str]
    details: AnalysisDetail
    metrics: Dict[str, Any]
    created_at: datetime

class FailureResponse(BaseModel):
    job_id: str
    status: str
    failure_reason: str
    updated_at: datetime

class MediaJobItem(BaseModel):
    job_id: str
    filename: str
    status: str
    created_at: datetime
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    issues_count: Optional[int] = None

class MediaListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[MediaJobItem]

class AnalyticsSummaryResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    pending_jobs: int
    failed_jobs: int
    pass_count: int
    warning_count: int
    reject_count: int
    issues_breakdown: Dict[str, int]
    avg_processing_time_ms: float
