import hashlib
import json
from typing import Any
from app.config import settings

def compute_cache_key(model: str, prompt_version: str, taxonomy_version: str, clean_text: str) -> str:
    """
    Compute a deterministic 64-char SHA-256 cache key.
    Includes model, prompt version, taxonomy version, and normalized text.
    """
    raw = f"{model}|{prompt_version}|{taxonomy_version}|{clean_text.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class TwoTierCache:
    """
    Two-tier cache:
    L1: In-memory / Redis cache
    L2: Persistent storage
    """
    def __init__(self, redis_client=None):
        self._memory_cache: dict[str, dict[str, Any]] = {}
        self.redis_client = redis_client
        self.hits = 0
        self.misses = 0

    async def get_many(self, keys: list[str]) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        missing_keys = []

        # Check memory first
        for k in keys:
            if k in self._memory_cache:
                results[k] = self._memory_cache[k]
                self.hits += 1
            else:
                missing_keys.append(k)

        # Check Redis if available
        if self.redis_client and missing_keys:
            try:
                for k in missing_keys:
                    val = await self.redis_client.get(f"llmc:{k}")
                    if val:
                        data = json.loads(val)
                        results[k] = data
                        self._memory_cache[k] = data
                        self.hits += 1
                    else:
                        self.misses += 1
            except Exception:
                self.misses += len(missing_keys)
        else:
            self.misses += len(missing_keys)

        return results

    async def set_many(self, items: dict[str, dict[str, Any]], ttl_seconds: int = 30 * 86400) -> None:
        for k, v in items.items():
            self._memory_cache[k] = v
            if self.redis_client:
                try:
                    await self.redis_client.set(f"llmc:{k}", json.dumps(v), ex=ttl_seconds)
                except Exception:
                    pass
