from pydantic import BaseModel


class ContactRequest(BaseModel):
    """Encapsulate a contact request."""
    email: str
    message: str
    name: str
    subject: str
