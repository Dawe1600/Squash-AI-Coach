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

@pytest.mark.asyncio
async def test_process_analysis_background(mocker):
    from app.api.endpoints import process_analysis_background, manager
    from app.core.schemas import CoachTip

    session_id = "test_session_bg"
    # Setup manager for this session
    manager.active_websockets[session_id] = mocker.AsyncMock()
    manager.players_configs[session_id] = None
    manager.languages[session_id] = "pl"
    manager.is_analyzing[session_id] = True
    manager.analysis_counters[session_id] = 24
    manager.session_history[session_id] = [
        ("Old Tip", 2),
        ("Recent Tip", 10)
    ]
    
    # Mock agent.analyze_video
    mock_analyze = mocker.patch.object(
        manager.agent, 
        "analyze_video", 
        return_value=CoachTip(
            has_tip=True,
            tip_text="New Tip",
            tip_category="footwork",
            target_player="Jan",
            severity_level="minor",
            drill_suggestion="Do something"
        )
    )
    
    # Mock tts.generate_speech and os.path.exists
    mocker.patch.object(manager.tts, "generate_speech", return_value=b"fake tts audio")
    mocker.patch("os.path.exists", return_value=False)
    
    # Call process_analysis_background
    await process_analysis_background(session_id, "fake_video_path.mp4")
    
    # Verify counter incremented to 25
    assert manager.analysis_counters[session_id] == 25
    
    # Verify analyze_video was called with only "Recent Tip" as previous_tips (since 25 - 2 = 23 >= 20; 25 - 10 = 15 < 20)
    mock_analyze.assert_called_once_with(
        "fake_video_path.mp4",
        previous_tips=["Recent Tip"],
        players_config=None,
        lang="pl"
    )
    
    # Verify session_history was updated with "New Tip" and counter 25
    assert ("New Tip", 25) in manager.session_history[session_id]

