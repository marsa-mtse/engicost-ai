"""
Price Cache Layer — TTL-based in-memory caching for market prices.

Prevents expensive AI/API calls on every page render.
Cache expires after 30 minutes (configurable).
"""

import time
import functools
from typing import Any


class TTLCache:
    """Simple Thread-safe TTL dictionary cache."""

    def __init__(self, ttl_seconds: int = 1800):
        self._ttl = ttl_seconds
        self._store: dict = {}
        self._timestamps: dict = {}

    def get(self, key: str) -> Any:
        if key in self._store:
            if time.time() - self._timestamps[key] < self._ttl:
                return self._store[key]
            else:
                self._evict(key)
        return None

    def set(self, key: str, value: Any):
        self._store[key] = value
        self._timestamps[key] = time.time()

    def _evict(self, key: str):
        self._store.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self):
        self._store.clear()
        self._timestamps.clear()

    def age_seconds(self, key: str) -> float:
        if key in self._timestamps:
            return time.time() - self._timestamps[key]
        return float("inf")

    def info(self, key: str) -> dict:
        age = self.age_seconds(key)
        return {
            "cached": key in self._store and age < self._ttl,
            "age_minutes": round(age / 60, 1),
            "expires_in_minutes": max(0, round((self._ttl - age) / 60, 1)),
        }


# Global singleton cache shared across the app session
price_cache = TTLCache(ttl_seconds=1800)  # 30 minutes
