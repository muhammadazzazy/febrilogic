"""Authentication API for user management in FastAPI application."""
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from starlette import status
from sqlalchemy.orm import Session


from apis.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY
)

from apis.db.database import get_db

from apis.models.user_request import UserRequest
from apis.models.token import Token
from apis.models.user_patient import User

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
            detail="Incorrect username or password",
        )
    token = create_access_token(user.username, user.id, user.role, timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Check if the user exists and the password is correct."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(username: str, user_id: int,
                        role: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """Get the current user from the access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user.',
            )
        return {'username': username, 'id': user_id, 'role': user_role}
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user.',
        ) from e


def require_admin(user: User = Depends(get_current_user)):
    """Ensure the user has admin privileges."""
    print(f"Authenticated user: {user['username']}, role: {user['role']}")
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403,
                            detail='Not enough permissions to access this resource.')
    return user


@api_router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(user_request: UserRequest,
                      user: Annotated[User, Depends(require_admin)],
                      db: Session = Depends(get_db)):
    """Create a new user in the database."""
    existing_user = db.query(User).filter(
        User.username == user_request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'User {user_request.username} already exists.'
        )

    user_model = User(
        role=user_request.role,
        username=user_request.username,
        hashed_password=bcrypt_context.hash(user_request.password),
    )
    db.add(user_model)
    db.commit()
    return {
        'message':
        f"User {user_request.username} with role {user_request.role} created by admin {user['username']}."
    }


@api_router.get('/id')
def get_user_id(user: Annotated[User, Depends(get_current_user)],
                db: Session = Depends(get_db)) -> dict[str, int]:
    """Get the user ID based on the authenticated user."""
    if user is None:
        raise HTTPException(status_code=401,
                            detail='Authentication failed.')
    user_id: int = db.query(User).filter(
        User.username == user['username']).first().id
    if not user_id:
        raise HTTPException(status_code=404,
                            detail='User not found.')
    return {
        'user_id': user_id
    }
