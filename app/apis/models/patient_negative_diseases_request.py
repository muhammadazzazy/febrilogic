"""Define the request model for recording negative diseases for a patient."""
from pydantic import BaseModel


class PatientNegativeDiseasesRequest(BaseModel):
    """Represent a request to record negative diseases for a patient."""
    negative_diseases: list[str]
