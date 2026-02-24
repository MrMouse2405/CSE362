from fastapi.testclient import TestClient
from app.main import app

# Initialize the test client with our FastAPI app
client = TestClient(app)

def test_health_check():
    """Test that the REST API health endpoint returns a 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "FastAPI is running"}