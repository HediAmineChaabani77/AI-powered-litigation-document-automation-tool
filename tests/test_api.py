"""Tests for the REST API endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Litigation AI Tool" in response.json()["message"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload_non_pdf():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_get_requests_not_found():
    response = client.get("/api/v1/documents/nonexistent-id/requests")
    assert response.status_code == 404
