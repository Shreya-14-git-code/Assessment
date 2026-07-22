import datetime
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import MediaJob
from backend.app.schemas import UploadResponse
from backend.app.services.storage import save_upload_file
from backend.app.services.queue_service import process_media_job_async

router = APIRouter(prefix="/api/v1/media", tags=["Media Upload"])

@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts media image upload, generates unique job ID, saves metadata,
    dispatches asynchronous processing task, and immediately returns 202 Accepted.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a valid filename")

    job_id, saved_path, file_size, file_ext = save_upload_file(file)

    # Store initial record in database with status 'pending'
    job = MediaJob(
        id=job_id,
        original_filename=file.filename,
        file_path=saved_path,
        file_size=file_size,
        mime_type=file.content_type or f"image/{file_ext.replace('.', '')}",
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue background processing task asynchronously
    background_tasks.add_task(process_media_job_async, job_id)

    return UploadResponse(
        job_id=job.id,
        filename=job.original_filename,
        file_size=job.file_size,
        status="pending",
        created_at=job.created_at,
        message="Image upload accepted. Processing asynchronously in background."
    )
