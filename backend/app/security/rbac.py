"""Role‑Based Access Control utilities.
Provides a FastAPI dependency that ensures the current user has one of the allowed roles.
"""
from fastapi import Depends, HTTPException, status
from typing import List
from backend.app.security.auth import get_current_active_user

def require_roles(allowed_roles: List[str]):
    """Return a dependency that validates the authenticated user's role.
    Usage::
        @router.get("/admin")
        def admin_endpoint(user=Depends(require_roles(["admin"]))):
            ...
    """
    async def role_checker(current_user=Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges"
            )
        return current_user
    return role_checker

require_role = require_roles

