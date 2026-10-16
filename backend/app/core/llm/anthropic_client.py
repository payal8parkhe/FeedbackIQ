import json
import time
from decimal import Decimal
from pydantic import BaseModel
from app.core.llm.base import LLMResult
from app.core.llm.pricing import calculate_llm_cost
from app.config import settings

class AnthropicClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def complete(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel] | None = None,
        model: str = "claude-3-5-haiku-20241022",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        purpose: str = "enrich",
        trace_id: str = "trace-default"
    ) -> LLMResult:
        client = self._get_client()
        start = time.perf_counter()

        system_prompt = system
        if schema:
            schema_json = json.dumps(schema.model_json_schema(), indent=2)
            system_prompt += f"\n\nYou MUST respond with valid JSON matching this JSON schema:\n{schema_json}\nReturn ONLY JSON, no markdown fences."

        response = await client.messages.create(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        latency = int((time.perf_counter() - start) * 1000)
        raw_text = response.content[0].text if response.content else ""
        
        parsed = None
        if schema:
            try:
                clean_text = raw_text.strip()
                if clean_text.startswith("```"):
                    clean_text = clean_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = schema.model_validate_json(clean_text)
            except Exception:
                parsed = None

        in_tok = response.usage.input_tokens
        out_tok = response.usage.output_tokens
        cached_in = getattr(response.usage, "cache_read_input_tokens", 0)

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
