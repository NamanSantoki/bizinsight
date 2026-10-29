import os
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.all_models import User
from backend.app.schemas.schemas import UserResponse
from backend.app.security.auth import verify_password, create_access_token, get_current_active_user
from backend.app.security.rbac import require_roles
from backend.app.audit.service import verify_audit_log_chain

router = APIRouter(prefix="/auth", tags=["auth"])

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/login", response_model=dict)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible login endpoint.
    Returns a JWT access token on successful authentication.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email
        }
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Returns the authenticated user's profile and active permissions."""
    return current_user

@router.get("/audit/verify-chain")
def verify_audit_chain(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "analyst"]))
):
    """Verifies cryptographic hash chain integrity of all historical system audit events."""
    return verify_audit_log_chain(db)
