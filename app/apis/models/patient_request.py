"""Encapsulate the request model for creating a new patient record."""
from pydantic import BaseModel


class PatientRequest(BaseModel):
    """Represent the request model for creating a new patient record."""
    age: int
    city: str
    country: str
    race: str
    sex: str
