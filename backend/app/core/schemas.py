from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TipCategory(str, Enum):
    FOOTWORK = "footwork"
    RACKET_TECHNIQUE = "racket_technique"
    SHOT_SELECTION = "shot_selection"
    TACTICAL = "tactical"
    POSITIONING = "positioning"


class SeverityLevel(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"


class CoachTip(BaseModel):
    has_tip: bool = Field(..., description="True if a notable error was detected that warrants coaching feedback. False if the players are playing well or the error is too minor to comment on.")
    target_player: Optional[str] = Field(None, description="Identifier of the player the tip is directed at (e.g., player name or visual description like 'black shirt'), only if has_tip=True.")
    tip_text: Optional[str] = Field(None, description="One or two concise, motivating sentences of coaching advice (e.g., 'Jan, bring your racket up earlier before running to the ball! This gives you more time for a controlled swing.'), only if has_tip=True.")
    tip_category: Optional[TipCategory] = Field(None, description="Category of the detected error: footwork, racket_technique, shot_selection, tactical, or positioning. Only if has_tip=True.")
    severity_level: Optional[SeverityLevel] = Field(None, description="How critical the detected error is: minor (small refinement), moderate (impacts game quality), critical (fundamental issue). Only if has_tip=True.")
    drill_suggestion: Optional[str] = Field(None, description="A short corrective drill suggestion the player can practice to fix the identified error (e.g., 'Solo drill: hit 50 forehand drives focusing on bringing the racket up immediately after each shot.'). Only if has_tip=True.")

