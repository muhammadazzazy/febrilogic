from pydantic import BaseModel


class ContactRequest(BaseModel):
    email: str
    message: str
    name: str
    subject: str
