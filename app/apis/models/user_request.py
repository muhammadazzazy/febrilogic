from pydantic import BaseModel


class UserRequest(BaseModel):
    email: str
    password: str
