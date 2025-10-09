from pydantic import BaseModel


class PatientBiomarkersRequest(BaseModel):
    """Request model for patient biomarkers."""
    biomarker_value_unit: dict[str, tuple[float, str]]


class PatientNegativeDiseasesRequest(BaseModel):
    """Represent a request to record negative diseases for a patient."""
    negative_diseases: list[str]


class PatientRequest(BaseModel):
    """Represent the request model for creating a new patient record."""
    age: int
    city: str
    country_id: int
    race: str
    sex: str


class PatientSymptomsRequest(BaseModel):
    """Represent the request model for creating a new symptom record."""
    symptom_names: list[str]
