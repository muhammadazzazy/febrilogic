from pydantic import BaseModel


class BiomarkerInfo(BaseModel):
    """Encapsulate biomarker factor for each unit grouped by biomarker ID."""
    id: int
    units: dict[str, float]
