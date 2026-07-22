import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/media_pipeline.db")
MAX_FILE_SIZE_MB = 15
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "3"))

# Heuristic thresholds
BLUR_THRESHOLD_SEVERE = 100.0
BLUR_THRESHOLD_MODERATE = 250.0
BRIGHTNESS_MIN = 40.0
BRIGHTNESS_MAX = 220.0
DUPLICATE_HAMMING_THRESHOLD = 8
