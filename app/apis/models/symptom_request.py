"""Encapsulate the request model for creating a new symptom record."""
from pydantic import BaseModel


class SymptomRequest(BaseModel):
    """Represent the request model for creating a new symptom record."""
    patient_id: int
    symptom_names: list[str]
