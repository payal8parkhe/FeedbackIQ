from app.config import settings
from app.core.embeddings.local import LocalEmbedder

class HostedEmbedder:
    def __init__(self, model: str = "text-embedding-3-small", dim: int = 1024):
        self.model = model
        self.dim = dim
        self._fallback = LocalEmbedder(dim=dim, model=f"{model}-fallback")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not settings.OPENAI_API_KEY:
            # Graceful fallback to local embedder if API key not supplied
            return await self._fallback.embed(texts)

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.embeddings.create(
                input=texts,
                model=self.model,
                dimensions=self.dim
            )
            return [data.embedding for data in response.data]
        except Exception:
            return await self._fallback.embed(texts)
