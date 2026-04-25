"""
Redis cache helpers for external market-data requests.

The cache is intentionally fail-open: Redis connection failures never block
business logic. Expired entries are kept for a stale window so callers can use
last-known-good data when an upstream data source is unavailable.
"""

from __future__ import annotations

import functools
import hashlib
import logging
import pickle
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

try:
    from core.config import settings
except Exception:
    settings = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CacheResult:
    value: Any
    hit: bool
    stale: bool = False


class RedisCache:
    """Small Redis wrapper with type-aware TTLs and stale fallback support."""

    DEFAULT_TTLS: Dict[str, Tuple[int, int]] = {
        "realtime": (30, 300),
        "technical": (1800, 86400),
        "kline": (1800, 86400),
        "fundamental": (43200, 604800),
        "fund_flow": (1800, 86400),
        "news": (1800, 86400),
        "longhubang": (86400, 604800),
        "price_prediction": (300, 1800),
        "default": (1800, 86400),
    }

    def __init__(self) -> None:
        self._client = None
        self._connect_attempted = False

    @property
    def enabled(self) -> bool:
        return bool(settings is None or getattr(settings, "REDIS_ENABLED", True))

    @property
    def prefix(self) -> str:
        return getattr(settings, "REDIS_KEY_PREFIX", "aiagents-stock") if settings else "aiagents-stock"

    def client(self):
        if not self.enabled:
            return None
        if self._client is not None:
            return self._client
        if self._connect_attempted:
            return None

        self._connect_attempted = True
        try:
            import redis

            redis_url = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0") if settings else "redis://127.0.0.1:6379/0"
            client = redis.Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
            client.ping()
            self._client = client
            logger.info("Redis cache connected: %s", redis_url)
            return self._client
        except Exception as exc:
            logger.warning("Redis cache unavailable, bypassing cache: %s: %s", type(exc).__name__, exc)
            return None

    def ttl_for(self, data_type: str) -> Tuple[int, int]:
        normalized = (data_type or "default").upper()
        default_ttl, default_stale = self.DEFAULT_TTLS.get(data_type, self.DEFAULT_TTLS["default"])
        ttl = getattr(settings, f"CACHE_TTL_{normalized}_SECONDS", default_ttl) if settings else default_ttl
        stale_ttl = getattr(settings, f"CACHE_STALE_TTL_{normalized}_SECONDS", default_stale) if settings else default_stale
        return int(ttl), int(stale_ttl)

    def make_key(self, data_type: str, *parts: Any, **kwargs: Any) -> str:
        raw = pickle.dumps((parts, sorted(kwargs.items())), protocol=pickle.HIGHEST_PROTOCOL)
        digest = hashlib.sha256(raw).hexdigest()
        return f"{self.prefix}:{data_type}:{digest}"

    def get(self, key: str, allow_stale: bool = True) -> Optional[CacheResult]:
        client = self.client()
        if client is None:
            return None

        try:
            raw = client.get(key)
            if raw is None:
                return None
            payload = pickle.loads(raw)
            expires_at = float(payload.get("expires_at", 0))
            stale_expires_at = float(payload.get("stale_expires_at", expires_at))
            now = time.time()
            if expires_at >= now:
                return CacheResult(payload.get("value"), hit=True, stale=False)
            if allow_stale and stale_expires_at >= now:
                return CacheResult(payload.get("value"), hit=True, stale=True)
            return None
        except Exception as exc:
            logger.warning("Redis cache get failed: key=%s error=%s: %s", key, type(exc).__name__, exc)
            return None

    def set(self, key: str, value: Any, ttl: int, stale_ttl: int) -> None:
        client = self.client()
        if client is None:
            return

        now = time.time()
        ttl = max(int(ttl), 1)
        stale_ttl = max(int(stale_ttl), ttl)
        payload = {
            "value": value,
            "expires_at": now + ttl,
            "stale_expires_at": now + stale_ttl,
            "cached_at": now,
        }
        try:
            client.setex(key, stale_ttl, pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception as exc:
            logger.warning("Redis cache set failed: key=%s error=%s: %s", key, type(exc).__name__, exc)

    def get_or_set(
        self,
        data_type: str,
        key_parts: Tuple[Any, ...],
        producer: Callable[[], Any],
        *,
        ttl: Optional[int] = None,
        stale_ttl: Optional[int] = None,
        is_valid: Optional[Callable[[Any], bool]] = None,
        cache_none: bool = False,
    ) -> CacheResult:
        fresh_ttl, fresh_stale_ttl = self.ttl_for(data_type)
        ttl = fresh_ttl if ttl is None else ttl
        stale_ttl = fresh_stale_ttl if stale_ttl is None else stale_ttl
        key = self.make_key(data_type, *key_parts)

        cached = self.get(key, allow_stale=False)
        if cached is not None:
            return cached

        stale = self.get(key, allow_stale=True)
        try:
            value = producer()
            valid = True if is_valid is None else is_valid(value)
            if valid and (value is not None or cache_none):
                self.set(key, value, ttl, stale_ttl)
                return CacheResult(value, hit=False, stale=False)
            if stale is not None:
                logger.warning("Using stale Redis cache for data_type=%s key=%s after invalid fresh data", data_type, key)
                return stale
            return CacheResult(value, hit=False, stale=False)
        except Exception:
            if stale is not None:
                logger.exception("Using stale Redis cache for data_type=%s key=%s after producer failure", data_type, key)
                return stale
            raise


redis_cache = RedisCache()


def cached_call(
    data_type: str,
    key_builder: Optional[Callable[..., Tuple[Any, ...]]] = None,
    *,
    ttl: Optional[int] = None,
    stale_ttl: Optional[int] = None,
    is_valid: Optional[Callable[[Any], bool]] = None,
    cache_none: bool = False,
):
    """Decorator for simple instance methods that fetch external data."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if key_builder:
                key_parts = key_builder(*args, **kwargs)
            else:
                self_marker = args[0].__class__.__name__ if args else ""
                key_parts = (self_marker, args[1:], kwargs)
            return redis_cache.get_or_set(
                data_type,
                key_parts,
                lambda: func(*args, **kwargs),
                ttl=ttl,
                stale_ttl=stale_ttl,
                is_valid=is_valid,
                cache_none=cache_none,
            ).value

        return wrapper

    return decorator
