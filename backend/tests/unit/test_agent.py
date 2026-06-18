import pytest
from unittest.mock import MagicMock
from app.core.agent import SquashAgent
from app.core.schemas import CoachTip

@pytest.fixture
def agent(mock_genai_client):
    # Przekazanie fikcyjnego klucza, by uniknąć błędów inicjalizacji
    return SquashAgent(api_key="fake_key")

def test_build_user_prompt(agent):
    base_prompt = "Base"
    tips = ["Tip1"]
    config = '{"playerA": {"name": "TestPlayer"}}'
    
    prompt = agent._build_user_prompt(base_prompt, tips, config, lang="pl")
    
    assert "Base" in prompt
    assert "Polish" in prompt
    assert "TestPlayer" in prompt
    assert "Tip1" in prompt

@pytest.mark.asyncio
async def test_analyze_native_video_success(agent, mock_genai_client):
    # Używamy mocka dla Google GenAI (zdefiniowanego w conftest.py)
    tip = await agent._analyze_native_video("fake_path.mp4", "gemma-4-31b-it")
    
    assert isinstance(tip, CoachTip)
    assert tip.has_tip is True
    assert tip.tip_category == "footwork"
    assert tip.target_player == "Jan"

@pytest.mark.asyncio
async def test_analyze_video_failover(agent, mocker):
    # Mockujemy _analyze_native_video żeby zawsze rzucał błąd
    mocker.patch.object(agent, "_analyze_native_video", side_effect=Exception("API Error"))
    
    # Mockujemy _analyze_frame_by_frame żeby zwracał sukces
    mock_frame = mocker.patch.object(agent, "_analyze_frame_by_frame", return_value=CoachTip(has_tip=False))
    
    result = await agent.analyze_video("fake.mp4")
    
    # Powinien użyć failovera i wywołać analizę po klatkach
    assert mock_frame.called
    assert result.has_tip is False

def test_parse_response_clean(agent):
    clean_json = '{"has_tip": true, "tip_text": "Clean"}'
    tip = agent._parse_response(clean_json)
    assert tip.tip_text == "Clean"

def test_parse_response_markdown(agent):
    md_json = '```json\n{"has_tip": true, "tip_text": "MD"}\n```'
    tip = agent._parse_response(md_json)
    assert tip.tip_text == "MD"

def test_parse_response_invalid(agent):
    invalid_json = 'Not a json'
    with pytest.raises(ValueError):
        agent._parse_response(invalid_json)
