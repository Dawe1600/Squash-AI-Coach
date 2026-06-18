import pytest
from unittest.mock import MagicMock
from app.core.schemas import CoachTip

# Mock Google GenAI API Client
@pytest.fixture
def mock_genai_client(mocker):
    mock_client = MagicMock()
    
    # Mock file upload
    mock_file = MagicMock()
    mock_file.name = "mock_file_name"
    mock_file.state.name = "ACTIVE"
    mock_client.files.upload.return_value = mock_file
    mock_client.files.get.return_value = mock_file
    
    # Mock content generation
    mock_response = MagicMock()
    mock_response.text = '{"has_tip": true, "target_player": "Jan", "tip_text": "Test Tip", "tip_category": "footwork", "severity_level": "minor", "drill_suggestion": "Test Drill"}'
    mock_client.models.generate_content.return_value = mock_response
    
    # Patch the genai.Client globally
    mocker.patch("app.core.agent.genai.Client", return_value=mock_client)
    return mock_client

# Mock gTTS (Text to Speech)
@pytest.fixture
def mock_gtts(mocker):
    mock_tts = MagicMock()
    mocker.patch("app.core.tts.gTTS", return_value=mock_tts)
    return mock_tts
