"""Encapsulate the request model for patient biomarkers."""
from pydantic import BaseModel


class PatientBiomarkersRequest(BaseModel):
    """Request model for patient biomarkers."""
    biomarker_value_unit: dict[str, tuple[float, str]]
