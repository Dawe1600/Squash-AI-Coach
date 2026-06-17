from pydantic import BaseModel, Field
from typing import Optional

class CoachTip(BaseModel):
    has_tip: bool = Field(..., description="Zwróć True, jeśli wykryłeś rażący błąd u któregoś z graczy i chcesz mu dać uwagę. False, jeśli grają poprawnie lub błędy są nieznaczne.")
    target_player: Optional[str] = Field(None, description="Identyfikator gracza, do którego kierowana jest uwaga (np. 'czarna koszulka'), o ile has_tip=True.")
    tip_text: Optional[str] = Field(None, description="Jedno zwięzłe, motywujące zdanie wskazówki (np. 'Ciemna koszulka, wracaj na środek po uderzeniu!'), o ile has_tip=True.")
