from pydantic import BaseModel


class UserRequest(BaseModel):
    """Encapsulates user login request data."""
    email: str
    password: str


class PasswordResetRequest(BaseModel):
    """Encapsulates password reset request data."""
    email: str


class ResetPasswordForm(BaseModel):
    """Encapsulates reset password form data."""
    token: str
    new_password: str


class ChangePasswordForm(BaseModel):
    """Encapsulates change password form data."""
    current_password: str
    new_password: str


class Token(BaseModel):
    """Encapsulate a JWT token response."""
    access_token: str
    token_type: str
