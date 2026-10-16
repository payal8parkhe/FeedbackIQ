import asyncio
import random
import time
from typing import Callable, TypeVar, Any
from app.domain.errors import LLMClientError, CircuitBreakerOpenError

T = TypeVar("T")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False


async def retry_with_backoff(
    fn: Callable[..., Any],
    *args,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    **kwargs
) -> Any:
    """Exponential backoff with full jitter: sleep = random(0, min(cap, base * 2^n))"""
    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise e
            # Full jitter backoff
            cap = min(max_delay, base_delay * (2 ** attempt))
            sleep_time = random.uniform(0, cap)
            await asyncio.sleep(sleep_time)
