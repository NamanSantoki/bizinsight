import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.all_models import User

def get_password_hash(password: str) -> str:
    salt = os.urandom(16).hex()
    pwd_bytes = password.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or "$" not in hashed_password:
        return False
    salt, hash_val = hashed_password.split("$", 1)
    pwd_bytes = plain_password.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt.encode('utf-8'), 100000)
    return key.hex() == hash_val

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Extracts authenticated user if token is provided, returns None otherwise."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return db.query(User).filter(User.id == int(user_id)).first()
    except JWTError:
        return None

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Zero-Trust Token Validator: Rejects unauthenticated requests with HTTP 401.
    Never defaults to an arbitrary admin user.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensures user account is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")
    return current_user
