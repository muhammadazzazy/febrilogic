from pydantic import BaseModel


class CreatePatientRequest(BaseModel):
    name: str
    age: int
    race: str
    sex: str
