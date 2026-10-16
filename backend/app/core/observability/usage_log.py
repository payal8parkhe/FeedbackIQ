import time
from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Any

@dataclass
class LLMCallLog:
    trace_id: str
    purpose: str
    model: str
    prompt_version: str
    batch_size: int
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    cost_usd: float
    latency_ms: int
    status: str
    error: str | None = None
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()


class UsageLogger:
    def __init__(self):
        self._logs: list[LLMCallLog] = []

    def log_call(self, entry: LLMCallLog):
        self._logs.append(entry)

    def get_summary(self) -> dict[str, Any]:
        total_cost = sum(l.cost_usd for l in self._logs)
        total_in = sum(l.input_tokens for l in self._logs)
        total_out = sum(l.output_tokens for l in self._logs)
        by_purpose: dict[str, float] = {}
        for l in self._logs:
            by_purpose[l.purpose] = by_purpose.get(l.purpose, 0.0) + l.cost_usd

        return {
            "total_calls": len(self._logs),
            "total_cost_usd": round(total_cost, 6),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "spend_by_purpose": {k: round(v, 6) for k, v in by_purpose.items()},
            "recent_calls": [asdict(l) for l in self._logs[-20:]]
        }


global_usage_logger = UsageLogger()
