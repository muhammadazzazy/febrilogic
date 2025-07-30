"""Encapsulate the request model for patient biomarkers."""
from pydantic import BaseModel


class PatientBiomarkerRequest(BaseModel):
    """Request model for patient biomarkers."""
    patient_id: int
    biomarker_id: int
    biomarker_value: float
    measured_at: str
