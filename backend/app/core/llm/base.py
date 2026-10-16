from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable
from pydantic import BaseModel

@dataclass
class LLMResult:
    text: str
    parsed: BaseModel | None
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    latency_ms: int
    cost_usd: Decimal
    model: str
    request_id: str


@runtime_checkable
class LLMClient(Protocol):
    async def complete(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel] | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        purpose: str = "enrich",
        trace_id: str = "trace-default",
    ) -> LLMResult:
        ...


@runtime_checkable
class Embedder(Protocol):
    dim: int
    model: str
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...
