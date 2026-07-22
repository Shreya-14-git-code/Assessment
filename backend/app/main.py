import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.database import init_db
from backend.app.config import UPLOAD_DIR
from backend.app.api.upload import router as upload_router
from backend.app.api.status import router as status_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.seed import router as seed_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database tables on application startup
    init_db()
    yield

app = FastAPI(
    title="Intelligent Media Processing Pipeline",
    description="Asynchronous media upload, heuristic anomaly detection, and vehicle license plate validation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for frontend dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(upload_router)
app.include_router(status_router)
app.include_router(analytics_router)
app.include_router(seed_router)

# Mount Uploads directory for image preview in dashboard
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Mount Frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

@app.get("/")
def root():
    return {
        "system": "Intelligent Media Processing Pipeline",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }
