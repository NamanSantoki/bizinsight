import secrets
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class APIKey(BaseModel):
    id: str
    name: str
    prefix: str
    hashed_key: str
    scopes: List[str]
    created_at: str
    last_used: Optional[str] = None
    rate_limit_per_minute: int = 120
    is_active: bool = True

class APIKeyManager:
    """Enterprise API Key Service for programmatic machine-to-machine integrations.
    Supports secure hashing, prefix verification, and scope validation.
    """

    def __init__(self):
        self._keys: Dict[str, APIKey] = {}
        # Pre-seed a default service account key for integrations
        self._seed_default_key()

    def _seed_default_key(self):
        prefix = "bk_live_svc"
        key_secret = "89dfa43e827361bf9a01e"
        full_key = f"{prefix}_{key_secret}"
        hashed = hashlib.sha256(full_key.encode()).hexdigest()
        self._keys["key_default_analytics"] = APIKey(
            id="key_default_analytics",
            name="Tableau / PowerBI Analytics Connector",
            prefix=prefix,
            hashed_key=hashed,
            scopes=["datasets:read", "metrics:read", "sql:execute"],
            created_at=datetime.now(timezone.utc).isoformat()
        )

    def create_key(self, name: str, scopes: List[str], rate_limit: int = 120) -> Dict[str, Any]:
        random_part = secrets.token_hex(16)
        prefix = "bk_live"
        full_secret = f"{prefix}_{random_part}"
        hashed = hashlib.sha256(full_secret.encode()).hexdigest()
        key_id = f"key_{secrets.token_hex(4)}"

        key = APIKey(
            id=key_id,
            name=name,
            prefix=prefix,
            hashed_key=hashed,
            scopes=scopes,
            created_at=datetime.now(timezone.utc).isoformat(),
            rate_limit_per_minute=rate_limit
        )
        self._keys[key_id] = key

        return {
            "id": key_id,
            "name": name,
            "api_key": full_secret,  # Only revealed once at creation
            "prefix": f"{prefix}_****",
            "scopes": scopes,
            "rate_limit_per_minute": rate_limit
        }

    def list_keys(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": k.id,
                "name": k.name,
                "prefix": f"{k.prefix}_****",
                "scopes": k.scopes,
                "created_at": k.created_at,
                "last_used": k.last_used,
                "rate_limit_per_minute": k.rate_limit_per_minute,
                "is_active": k.is_active
            }
            for k in self._keys.values()
        ]

    def verify_key(self, api_key: str, required_scope: Optional[str] = None) -> bool:
        hashed = hashlib.sha256(api_key.encode()).hexdigest()
        for k in self._keys.values():
            if k.hashed_key == hashed and k.is_active:
                if required_scope and required_scope not in k.scopes:
                    return False
                k.last_used = datetime.now(timezone.utc).isoformat()
                return True
        return False

api_key_manager = APIKeyManager()

