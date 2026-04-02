from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_cameras_invalid_bbox_format():
    response = client.get("/api/v1/cameras?bbox=invalid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid bbox format"

def test_get_cameras_missing_bbox():
    response = client.get("/api/v1/cameras")
    assert response.status_code == 422 # Unprocessable Entity because bbox is required
