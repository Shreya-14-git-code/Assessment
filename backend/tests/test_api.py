import os
import io
import time
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def dummy_image_bytes():
    buf = io.BytesIO()
    img = Image.new("RGB", (300, 300), color=(100, 150, 200))
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()

def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

def test_upload_and_status_flow(client, dummy_image_bytes):
    # 1. Upload file
    files = {"file": ("test_vehicle.jpg", dummy_image_bytes, "image/jpeg")}
    upload_res = client.post("/api/v1/media/upload", files=files)
    assert upload_res.status_code == 202
    
    data = upload_res.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    job_id = data["job_id"]

    # 2. Poll status endpoint until completed
    max_wait = 10
    start = time.time()
    final_status = "pending"
    
    while time.time() - start < max_wait:
        status_res = client.get(f"/api/v1/media/{job_id}/status")
        assert status_res.status_code == 200
        final_status = status_res.json()["status"]
        if final_status in ["completed", "failed"]:
            break
        time.sleep(0.5)

    assert final_status == "completed"

    # 3. Fetch results
    results_res = client.get(f"/api/v1/media/{job_id}/results")
    assert results_res.status_code == 200
    results = results_res.json()
    assert results["job_id"] == job_id
    assert results["risk_level"] in ["PASS", "WARNING", "REJECT"]
    assert "details" in results

def test_analytics_summary(client):
    res = client.get("/api/v1/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_jobs" in data
    assert "issues_breakdown" in data
