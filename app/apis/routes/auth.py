"""Authentication API for user management in FastAPI application."""
from datetime import datetime, timedelta
from typing import Annotated
from uuid import uuid4

import resend
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jinja2 import Template
from jose import jwt, JWTError
from passlib.context import CryptContext
from starlette import status
from sqlalchemy.orm import Session


from apis.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    RESEND_API_KEY,
    VERIFICATION_EMAIL_TEMPLATE
)

from apis.db.database import get_db

from apis.models.user_request import UserRequest
from apis.models.token import Token
from apis.models.model import User

resend.api_key = RESEND_API_KEY

api_router: APIRouter = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')

bcrypt_context: CryptContext = CryptContext(schemes=['bcrypt'],
                                            deprecated='auto')


@api_router.post('/token', response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not verified",
        )
    token = create_access_token(user.email, user.id, timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Check if the user exists and the password is correct."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(email: str, user_id: int, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    encode = {'sub': email, 'id': user_id}
    expires = datetime.now() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """Get the current user from the access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        user_id: int = payload.get('id')
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user.',
            )
        return {'email': email, 'id': user_id}
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user.',
        ) from e


@api_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(user_request: UserRequest,
                      db: Session = Depends(get_db)):
    """Create a new user in the database."""
    existing_user = db.query(User).filter(
        User.email == user_request.email).first()
    if existing_user and existing_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'User with verified email {user_request.email} already exists.'
        )
    if not existing_user:
        verification_code: str = str(uuid4())
        user_model = User(
            email=user_request.email,
            hashed_password=bcrypt_context.hash(user_request.password),
            is_verified=False,
            verification_code=verification_code
        )
        db.add(user_model)
        db.commit()
    if existing_user and not existing_user.is_verified:
        verification_code: str = existing_user.verification_code
        send_verification_email(
            user_request.email, verification_code
        )
    return {
        'message': f'Verification link sent to your email: {user_request.email}'
    }


@api_router.get('/verify/{verification_code}')
def verify_user(verification_code: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify a user based on the verification code."""
    user = db.query(User).filter(
        User.verification_code == verification_code).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found.'
        )
    user.is_verified = True
    user.verification_code = None
    db.commit()
    return {
        'message': f'{user.email} verified successfully.'
    }


def send_verification_email(to_email: str, verification_code: str) -> None:
    """Send a verification email to the user."""
    with open(VERIFICATION_EMAIL_TEMPLATE, encoding='utf-8') as file:
        template = Template(file.read())
    html = template.render(verification_code=verification_code)
    params: resend.Emails.SendParams = {
        "from": "FebriLogic <noreply@febrilogic.com>",
        "to": [to_email],
        "subject": "Verify your email",
        "html": html
    }
    _email: resend.Email = resend.Emails.send(params)
