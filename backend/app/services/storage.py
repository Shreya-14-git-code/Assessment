import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from backend.app.config import UPLOAD_DIR, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS

def save_upload_file(upload_file: UploadFile) -> tuple[str, str, int, str]:
    """
    Validates file extension and size, saves to storage, and returns metadata tuple:
    (job_id, saved_file_path, file_size_bytes, extension)
    """
    file_ext = Path(upload_file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    job_id = str(uuid.uuid4())
    saved_filename = f"{job_id}{file_ext}"
    target_path = UPLOAD_DIR / saved_filename

    # Read and calculate size
    try:
        file_size = 0
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        file_size = os.path.getsize(target_path)
        
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            target_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE_MB}MB"
            )
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to save upload file: {str(e)}")

    return job_id, str(target_path), file_size, file_ext
