# Intelligent Media Processing Pipeline

A high-performance, asynchronous backend system and web dashboard designed to ingest vehicle images from field uploads, evaluate image quality/authenticity via 6 multi-heuristic detectors, and output structured analysis reports.

---

## 🏗️ Architecture & System Design

### 1. Service Flow
```
[Client / Dashboard] 
       │
       ├── (POST /upload) ──> [FastAPI Upload Server]
       │                            │
       │                            ├── 1. Saves raw file to disk/object storage
       │                            ├── 2. Creates DB record (status: 'pending')
       │                            └── 3. Dispatches async worker task
       │                                  └── Returns 202 Accepted + UUID Job ID immediately
       │
       ├── (Polling / WebSocket) ──> [FastAPI Status/Results APIs]
       │
[Background Worker Pool] <── (Job Task) ── [Async Worker Queue]
       │
       ├── Runs Multi-Heuristic Inspection Pipeline
       │      ├── Blur Detector (Laplacian Variance)
       │      ├── Brightness & Exposure Analyzer (Luminance Histogram)
       │      ├── Duplicate Detector (Perceptual Hashes: dHash/pHash)
       │      ├── Screenshot & Photo-of-Screen Detector (EXIF, Aspect Ratio, 2D FFT Moiré)
       │      ├── Tamper Detector (ELA JPEG compression artifact disparity)
       │      └── OCR & License Plate Validator (Indian Standard Formats)
       │
       └── Updates DB Record (status: 'completed' / 'failed', risk_level, scores, metrics)
```

### 2. Processing Flow & Status Lifecycle
Jobs transition through four explicit states:
- `pending`: Upload accepted, metadata recorded in DB.
- `processing`: Background worker has acquired job lock and is running image inspection heuristics.
- `completed`: All 6 detectors completed execution; structured results, scores, and issue lists persisted.
- `failed`: An unhandled exception occurred; stack trace and failure reason stored.

### 3. Queue Strategy & Decoupling
- **Zero-Dependency Default Mode**: Uses FastAPI `BackgroundTasks` / `asyncio.Queue` worker pool for single-command local runs without external queue dependencies.
- **Production Enterprise Mode**: Configured for Redis + Celery worker pool with job locking and retry mechanics.

### 4. Major Design Decisions
- **Multi-Heuristic Engine**: Combined lightweight OpenCV/PIL mathematical algorithms rather than heavy, opaque ML models for deterministic, explainable, and fast performance.
- **Perceptual Hashing for Duplicate Detection**: Computes dHash and pHash fingerprints and checks Hamming distance ($\le 8$) against database index.
- **Indian Vehicle Registration Validation**: Regex verification supporting Standard State series (`MH12AB1234`), Bharat (BH) series (`22BH1234A`), and commercial formats.

---

## 🤖 Mandatory AI Usage Disclosure

### 1. Where AI Was Used
- Assisting in boilerplating Pydantic DTO schemas and FastAPI router syntax.
- Drafting initial OpenCV Fourier transform (FFT 2D) frequency spectrum filtering snippets for Moiré pattern detection.
- Structuring dark-mode HTML/CSS UI dashboard components.

### 2. What AI Helped With
- Accelerating regex formulation for Indian license plate validation variations.
- Generating synthetic test image creation functions (`cv2.GaussianBlur`, noise addition) for seeding demo cases.

### 3. Where AI Output Was Wrong
- **OpenCV Color Space Bug**: AI generated code that passed OpenCV BGR matrices directly into PIL Image without converting to RGB, resulting in swapped blue/red colors during ELA analysis.
- **Asynchronous Database Session Leak**: AI suggested passing the active FastAPI `db: Session` directly into `BackgroundTasks`, which caused `SQLite objects created in a thread can only be used in the same thread` errors.
- **Tesseract Config Syntax**: AI generated invalid PyTesseract command flags (`-psm 6 --oem 3` in inverted order) causing runtime execution crashes on Windows binaries.

### 4. How AI-Generated Code Was Validated
- **Empirical Unit Tests**: Built an automated `pytest` test suite verifying sharpness, dark brightness, duplicate distance, and plate regex matching.
- **Runtime Verification**: Tested synthetic sample images representing blur, dark, duplicate, invalid plate, and clean cases through the dashboard UI.

---

## ⚖️ Trade-offs & Limitations

### 1. Intentionally Simplified
- **Single-Node Queue**: Used in-memory / `asyncio` task queue by default to eliminate mandatory Redis setup for evaluators.
- **Local File System Storage**: Saved uploads to `/uploads` directory instead of AWS S3 bucket.

### 2. Future Improvements (Given More Time)
- **Dead Letter Queue (DLQ)**: Add dedicated DLQ queue for retrying transient OCR timeouts.
- **YOLO License Plate Localization**: Integrate a lightweight YOLOv8 nano model for precise bounding-box cropping before running OCR.
- **Perceptual Hash Indexing**: Replace linear DB hash comparison with a BK-Tree / VP-Tree for $O(\log N)$ duplicate matching at scale.

### 3. Scalability Concerns
- Processing high-resolution 4K field photos can saturate CPU matrix operations. High-throughput deployments require worker scaling and GPU acceleration for OCR.

### 4. Failure Handling
- Unreadable or corrupted image files are caught safely at step 1 of the pipeline, marking the job as `failed` with a clear user-facing error message without crashing the background worker.

---

## 🚀 Running Instructions

### Prerequisites
- Python 3.10+ installed
- (Optional) Docker & Docker Compose

### Option A: Local Python Run (Recommended for Quick Testing)

1. **Activate Virtual Environment & Install Dependencies**:
   ```bash
   cd intelligent-media-pipeline
   .\venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

2. **Run Server**:
   ```bash
   python run_local.py
   ```

3. **Access App**:
   - **Dashboard UI**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
   - **Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

4. **Seed Test Data**:
   Click the **"⚡ Seed Demo Cases"** button in the dashboard or run:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/seed
   ```

### Option B: Docker Compose Setup
```bash
docker-compose up --build
```

---

## 🧪 Automated Test Suite

Run unit and integration tests:
```bash
pytest backend/tests/
```

---

## 📬 Sample API Requests & Responses

### 1. Upload Image
`POST /api/v1/media/upload` (Multipart Form)

**Response (`202 Accepted`)**:
```json
{
  "job_id": "e4b9d7a2-1234-4567-89ab-cdef01234567",
  "filename": "vehicle_front.jpg",
  "file_size": 1048576,
  "status": "pending",
  "created_at": "2026-07-22T10:00:00.000Z",
  "message": "Image upload accepted. Processing asynchronously in background."
}
```

### 2. Fetch Results
`GET /api/v1/media/e4b9d7a2-1234-4567-89ab-cdef01234567/results`

**Response (`200 OK`)**:
```json
{
  "job_id": "e4b9d7a2-1234-4567-89ab-cdef01234567",
  "status": "completed",
  "original_filename": "vehicle_front.jpg",
  "overall_score": 95.0,
  "risk_level": "PASS",
  "detected_issues": [],
  "details": {
    "is_blurry": false,
    "blur_score": 450.2,
    "is_low_light": false,
    "is_overexposed": false,
    "brightness_score": 115.4,
    "is_duplicate": false,
    "is_screenshot": false,
    "is_tampered": false,
    "license_plate_text": "MH12AB1234",
    "is_valid_license_plate": true,
    "plate_confidence": 95.0
  }
}
```
