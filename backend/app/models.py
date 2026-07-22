import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class MediaJob(Base):
    __tablename__ = "media_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Status: pending, processing, completed, failed
    status = Column(String(50), nullable=False, default="pending", index=True)
    failure_reason = Column(Text, nullable=True)
    processing_time_ms = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    analysis_result = relationship("AnalysisResult", back_populates="job", uselist=False, cascade="all, delete-orphan")
    perceptual_hash = relationship("PerceptualHash", back_populates="job", uselist=False, cascade="all, delete-orphan")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("media_jobs.id"), nullable=False, unique=True, index=True)

    overall_score = Column(Float, nullable=False)  # 0 to 100
    risk_level = Column(String(20), nullable=False)  # PASS, WARNING, REJECT

    # Individual check results
    is_blurry = Column(Boolean, default=False)
    blur_score = Column(Float, default=0.0)  # Variance of Laplacian

    is_low_light = Column(Boolean, default=False)
    is_overexposed = Column(Boolean, default=False)
    brightness_score = Column(Float, default=0.0)  # Mean luminance

    is_duplicate = Column(Boolean, default=False)
    duplicate_of_job_id = Column(String(36), nullable=True)
    duplicate_distance = Column(Integer, nullable=True)

    is_screenshot = Column(Boolean, default=False)
    screenshot_score = Column(Float, default=0.0)

    is_tampered = Column(Boolean, default=False)
    tamper_score = Column(Float, default=0.0)

    license_plate_text = Column(String(100), nullable=True)
    is_valid_license_plate = Column(Boolean, default=False)
    plate_confidence = Column(Float, default=0.0)

    # Detailed issues list & full metric dictionary
    detected_issues = Column(JSON, nullable=False, default=list)
    metrics_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    job = relationship("MediaJob", back_populates="analysis_result")


class PerceptualHash(Base):
    __tablename__ = "perceptual_hashes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("media_jobs.id"), nullable=False, unique=True, index=True)
    
    dhash = Column(String(64), nullable=False, index=True)
    phash = Column(String(64), nullable=False, index=True)
    ahash = Column(String(64), nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    job = relationship("MediaJob", back_populates="perceptual_hash")
