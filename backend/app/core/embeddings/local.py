import hashlib
import math
from typing import Protocol

class Embedder(Protocol):
    dim: int
    model: str
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class LocalEmbedder:
    """
    Lightweight, deterministic local embedding generator producing normalized 1024-dim vectors
    without requiring GPU, downloads, or external network calls.
    Perfect for unit tests, local development, and CI environments.
    """
    def __init__(self, dim: int = 1024, model: str = "bge-small-local"):
        self.dim = dim
        self.model = model

    def _embed_single(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        if not tokens:
            return vec
        
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
            vec[idx] += sign

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0.0:
            vec = [v / norm for v in vec]
        return vec

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(t) for t in texts]
