import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from backend.app.core.config import settings

# Salted SHA256 + PBKDF2 implementation to avoid passlib-bcrypt 4.0/5.0 __about__ incompatibility on Python 3.11
def get_password_hash(password: str) -> str:
    salt = os.urandom(16).hex()
    pwd_bytes = password.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if "$" not in hashed_password:
        return False
    salt, hash_val = hashed_password.split("$", 1)
    pwd_bytes = plain_password.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt.encode('utf-8'), 100000)
    return key.hex() == hash_val

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
