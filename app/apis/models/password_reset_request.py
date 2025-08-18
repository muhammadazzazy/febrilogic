from pydantic import BaseModel


class PasswordResetRequest(BaseModel):
    email: str
