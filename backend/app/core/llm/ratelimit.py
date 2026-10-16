import asyncio
import time

class TokenBucket:
    """Thread-safe and async-safe token bucket for RPM and TPM rate limiting."""
    def __init__(self, capacity: float, refill_rate_per_sec: float):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> bool:
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.last_refill = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_and_acquire(self, tokens: float = 1.0, timeout: float = 10.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            if await self.acquire(tokens):
                return True
            await asyncio.sleep(0.05)
        return False
