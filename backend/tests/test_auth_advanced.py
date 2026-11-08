import pytest
from datetime import timedelta
from fastapi import HTTPException
from unittest.mock import MagicMock
from jose import jwt
from backend.app.core.config import settings
from backend.app.models.all_models import User
from backend.app.security.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user_optional,
    get_current_user,
    get_current_user_or_default,
    get_current_active_user
)

def test_verify_password_invalid_hash():
    assert verify_password("secret", "") is False
    assert verify_password("secret", "invalid_no_dollar") is False

def test_create_access_token_custom_expiry():
    token = create_access_token({"sub": "42"}, expires_delta=timedelta(hours=2))
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "42"
    assert "exp" in payload

@pytest.mark.asyncio
async def test_get_current_user_optional():
    mock_db = MagicMock()
    # No token
    res = await get_current_user_optional(token=None, db=mock_db)
    assert res is None

    # Invalid token
    res = await get_current_user_optional(token="invalid.token.here", db=mock_db)
    assert res is None

    # Valid token but no sub
    token_no_sub = jwt.encode({"role": "guest"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res = await get_current_user_optional(token=token_no_sub, db=mock_db)
    assert res is None

    # Valid token with sub
    user_obj = User(id=99, username="test_u")
    mock_db.query().filter().first.return_value = user_obj
    token_valid = jwt.encode({"sub": "99"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res = await get_current_user_optional(token=token_valid, db=mock_db)
    assert res.username == "test_u"

@pytest.mark.asyncio
async def test_get_current_user_failures():
    mock_db = MagicMock()
    # Missing token -> 401
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=None, db=mock_db)
    assert exc.value.status_code == 401

    # Invalid jwt -> 401
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token="bad_token", db=mock_db)
    assert exc.value.status_code == 401

    # Token with missing sub -> 401
    token_no_sub = jwt.encode({"test": 1}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token_no_sub, db=mock_db)
    assert exc.value.status_code == 401

    # Token valid but user deleted from DB -> 401
    mock_db.query().filter().first.return_value = None
    token_valid = jwt.encode({"sub": "123"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token_valid, db=mock_db)
    assert exc.value.status_code == 401
    assert "no longer exists" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_or_default():
    mock_db = MagicMock()
    # Valid token
    user_obj = User(id=1, username="custom_user")
    mock_db.query().filter().first.return_value = user_obj
    token_valid = jwt.encode({"sub": "1"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res = await get_current_user_or_default(token=token_valid, db=mock_db)
    assert res.username == "custom_user"

    # Token error falls back to default analyst
    default_analyst = User(id=2, username="analyst")
    mock_db.query().filter().first.return_value = default_analyst
    res2 = await get_current_user_or_default(token="bad_token", db=mock_db)
    assert res2.username == "analyst"

@pytest.mark.asyncio
async def test_get_current_active_user():
    inactive_user = User(id=1, username="inactive", is_active=False)
    with pytest.raises(HTTPException) as exc:
        await get_current_active_user(current_user=inactive_user)
    assert exc.value.status_code == 400
    assert "Inactive user account" in exc.value.detail

    active_user = User(id=2, username="active", is_active=True)
    res = await get_current_active_user(current_user=active_user)
    assert res.username == "active"

