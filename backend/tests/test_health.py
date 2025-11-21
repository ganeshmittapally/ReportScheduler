"""Test health check endpoints."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test the /health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "python_version" in data


def test_readiness_check(client: TestClient):
    """Test the /health/ready endpoint returns 200."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data


def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data
