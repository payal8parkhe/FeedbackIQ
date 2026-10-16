import json
import time
from decimal import Decimal
from pydantic import BaseModel
from app.core.llm.base import LLMResult
from app.core.llm.pricing import calculate_llm_cost
from app.config import settings

class OpenAIClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

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
        trace_id: str = "trace-default"
    ) -> LLMResult:
        client = self._get_client()
        start = time.perf_counter()

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

        if schema:
            # Structured output mode
            response = await client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            parsed = response.choices[0].message.parsed
            raw_text = response.choices[0].message.content or ""
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            parsed = None
            raw_text = response.choices[0].message.content or ""

        latency = int((time.perf_counter() - start) * 1000)
        usage = response.usage
        in_tok = usage.prompt_tokens if usage else len(system + user) // 4
        out_tok = usage.completion_tokens if usage else len(raw_text) // 4
        cached_tok = getattr(usage, "prompt_tokens_details", None)
        cached_in = getattr(cached_tok, "cached_tokens", 0) if cached_tok else 0

        cost = calculate_llm_cost(model, in_tok, out_tok, cached_in)

        return LLMResult(
            text=raw_text,
            parsed=parsed,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cached_input_tokens=cached_in,
            latency_ms=latency,
            cost_usd=cost,
            model=model,
            request_id=response.id
        )
