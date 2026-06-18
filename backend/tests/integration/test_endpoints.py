import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()

def test_upload_chunk_no_session():
    # Should fail or return 4xx without session_id
    response = client.post("/api/upload-chunk")
    assert response.status_code == 422

def test_upload_chunk_mocked(mocker):
    # Mock manager to simulate an active session
    mocker.patch("app.api.endpoints.manager.motion_detectors", {"test_session": mocker.MagicMock()})
    mocker.patch("app.api.endpoints.manager.is_analyzing", {"test_session": False})
    mocker.patch("app.api.endpoints.process_analysis_background")
    
    files = {"file": ("test.webm", b"dummy video content", "video/webm")}
    response = client.post("/api/upload-chunk?session_id=test_session", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["processing", "analysis_started"]

def test_websocket_connection():
    # Do not mock connect/disconnect so the manager state is properly updated
    with client.websocket_connect("/ws/session?session_id=ws_test&lang=en") as websocket:
        # Pomyślne nawiązanie połączenia - wyślij ping
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"
    
    # After context exit, the websocket should disconnect
    from app.api.endpoints import manager
    assert "ws_test" not in manager.active_websockets
