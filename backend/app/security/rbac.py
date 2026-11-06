"""Role‑Based Access Control (RBAC) utilities.
Provides dependencies ensuring authenticated users have appropriate enterprise roles.
"""
from fastapi import Depends, HTTPException, status
from typing import List, Union, Set
from backend.app.security.auth import get_current_active_user

# Enterprise Roles
ROLE_ADMIN = "admin"
ROLE_DECISION_MAKER = "decision_maker"
ROLE_ML_ENGINEER = "ml_engineer"
ROLE_ANALYST = "analyst"
ROLE_DEVELOPER = "developer"
ROLE_USER = "user"

ALL_ROLES: Set[str] = {
    ROLE_ADMIN,
    ROLE_DECISION_MAKER,
    ROLE_ML_ENGINEER,
    ROLE_ANALYST,
    ROLE_DEVELOPER,
    ROLE_USER,
}

# Role hierarchy: Admin possesses superset privileges across all operational scopes
ROLE_HIERARCHY = {
    ROLE_ADMIN: ALL_ROLES,
    ROLE_DECISION_MAKER: {ROLE_DECISION_MAKER, ROLE_ANALYST, ROLE_USER},
    ROLE_ML_ENGINEER: {ROLE_ML_ENGINEER, ROLE_DEVELOPER, ROLE_ANALYST, ROLE_USER},
    ROLE_DEVELOPER: {ROLE_DEVELOPER, ROLE_USER},
    ROLE_ANALYST: {ROLE_ANALYST, ROLE_USER},
    ROLE_USER: {ROLE_USER},
}

def require_roles(allowed_roles: Union[str, List[str], Set[str]]):
    """Return a dependency that validates the authenticated user's role against required roles.
    Includes administrative hierarchy inheritance.
    Usage::
        @router.get("/admin")
        def admin_endpoint(user=Depends(require_roles(["admin"]))):
            ...
    """
    if isinstance(allowed_roles, str):
        target_roles = {allowed_roles}
    else:
        target_roles = set(allowed_roles)

    async def role_checker(current_user=Depends(get_current_active_user)):
        user_role = getattr(current_user, "role", "user")
        effective_roles = ROLE_HIERARCHY.get(user_role, {user_role})
        
        # Check if user has direct or inherited role match
        if not effective_roles.intersection(target_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Required role in {list(target_roles)}, current role: '{user_role}'"
            )
        return current_user

    return role_checker

require_role = require_roles


