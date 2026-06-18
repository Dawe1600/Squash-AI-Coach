import pytest
from pydantic import ValidationError
from app.core.schemas import CoachTip, TipCategory, SeverityLevel

def test_coachtip_valid_full():
    data = {
        "has_tip": True,
        "target_player": "Jan",
        "tip_text": "Biegnij szybciej",
        "tip_category": "footwork",
        "severity_level": "critical",
        "drill_suggestion": "Sprinty"
    }
    tip = CoachTip(**data)
    assert tip.has_tip is True
    assert tip.tip_category == TipCategory.FOOTWORK
    assert tip.severity_level == SeverityLevel.CRITICAL

def test_coachtip_valid_minimal():
    # Only has_tip is strictly required
    data = {"has_tip": False}
    tip = CoachTip(**data)
    assert tip.has_tip is False
    assert tip.tip_text is None

def test_coachtip_invalid_enum():
    data = {
        "has_tip": True,
        "tip_category": "invalid_category",
    }
    with pytest.raises(ValidationError):
        CoachTip(**data)

def test_coachtip_missing_required():
    data = {}
    with pytest.raises(ValidationError):
        CoachTip(**data)
