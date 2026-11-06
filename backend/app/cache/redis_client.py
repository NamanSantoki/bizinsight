"""
Production-Grade Resilient Cache Client
Supports Redis with automatic fallback to high-performance in-memory TTL store
if Redis is unreachable or during local test execution.
"""
import os
import json
import time
import logging
from typing import Any, Optional
from backend.app.core.config import settings

logger = logging.getLogger("bizinsight.cache")

class InMemoryCache:
    def __init__(self):
        self._store = {}
        self._expiries = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            expiry = self._expiries.get(key)
            if expiry and time.time() > expiry:
                self.delete(key)
                return None
            return self._store[key]
        return None

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        self._store[key] = value
        if expire_seconds:
            self._expiries[key] = time.time() + expire_seconds
        elif key in self._expiries:
            del self._expiries[key]
        return True

    def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        self._expiries.pop(key, None)
        return True

    def clear(self):
        self._store.clear()
        self._expiries.clear()


class CacheClient:
    def __init__(self):
        self._redis = None
        self._memory = InMemoryCache()
        self._hits = 0
        self._misses = 0
        self._init_redis()

    def _init_redis(self):
        try:
            import redis
            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url, socket_connect_timeout=1.0, decode_responses=True)
            client.ping()
            self._redis = client
            logger.info("Connected to Redis cache cluster at %s", redis_url)
        except Exception as exc:
            self._redis = None
            logger.info("Redis unavailable (%s); using in-memory TTL cache fallback.", exc)

    def get(self, key: str) -> Optional[Any]:
        val = None
        if self._redis:
            try:
                raw = self._redis.get(key)
                if raw is not None:
                    val = json.loads(raw)
            except Exception as e:
                logger.warning("Redis get error for %s: %s; falling back to memory", key, e)
                val = self._memory.get(key)
        else:
            val = self._memory.get(key)

        if val is not None:
            self._hits += 1
        else:
            self._misses += 1
        return val

    def set(self, key: str, value: Any, expire_seconds: int = 300) -> bool:
        serialized = json.dumps(value)
        if self._redis:
            try:
                self._redis.setex(key, expire_seconds, serialized)
                return True
            except Exception as e:
                logger.warning("Redis set error for %s: %s; setting in memory", key, e)
        return self._memory.set(key, value, expire_seconds)

    def delete(self, key: str) -> bool:
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        return self._memory.delete(key)

    def get_stats(self) -> dict:
        total = self._hits + self._misses
        hit_ratio = round((self._hits / total) * 100, 2) if total > 0 else 0.0
        return {
            "backend": "redis" if self._redis else "in_memory_ttl",
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_ratio_pct": hit_ratio
        }

cache_client = CacheClient()

