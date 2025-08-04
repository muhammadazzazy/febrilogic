"""Encapsulate the request model for patient biomarkers."""
from pydantic import BaseModel


class PatientBiomarkersRequest(BaseModel):
    """Request model for patient biomarkers."""
    biomarker_values: dict[str, float]
