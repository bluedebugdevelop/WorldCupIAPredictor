"""Esquemas Pydantic de la API."""

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    team_a: str = Field(..., description="Código FIFA de la selección local")
    team_b: str = Field(..., description="Código FIFA de la selección visitante")
    referee: str = Field(..., description="ID del árbitro")
    neutral: bool = Field(True, description="Sede neutral (sin ventaja de campo)")
    knockout: bool = Field(False, description="Fase eliminatoria")
    use_form: bool = Field(True, description="Incorporar la forma real en el torneo")
    n_sims: int = Field(20000, ge=1000, le=100000, description="Nº de simulaciones Monte Carlo")
