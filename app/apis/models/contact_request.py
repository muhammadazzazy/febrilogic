from pydantic import BaseModel


class ContactRequest(BaseModel):
    subject: str
    message: str
