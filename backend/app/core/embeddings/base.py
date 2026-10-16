from typing import Protocol, runtime_checkable

@runtime_checkable
class Embedder(Protocol):
    dim: int
    model: str
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...
