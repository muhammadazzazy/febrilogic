from pydantic import BaseModel


class ResetPasswordForm(BaseModel):
    token: str
    new_password: str
