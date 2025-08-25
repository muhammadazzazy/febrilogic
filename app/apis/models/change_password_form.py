from pydantic import BaseModel


class ChangePasswordForm(BaseModel):
    current_password: str
    new_password: str
