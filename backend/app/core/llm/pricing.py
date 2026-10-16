from decimal import Decimal
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelPrice:
    input_per_million: Decimal
    output_per_million: Decimal
    cached_input_per_million: Decimal


PRICING_TABLE: dict[str, ModelPrice] = {
    # OpenAI Models
    "gpt-4o-mini": ModelPrice(
        input_per_million=Decimal("0.15"),
        output_per_million=Decimal("0.60"),
        cached_input_per_million=Decimal("0.075"),
    ),
    "gpt-4o": ModelPrice(
        input_per_million=Decimal("2.50"),
        output_per_million=Decimal("10.00"),
        cached_input_per_million=Decimal("1.25"),
    ),
    # Anthropic Models
    "claude-3-5-haiku-20241022": ModelPrice(
        input_per_million=Decimal("1.00"),
        output_per_million=Decimal("5.00"),
        cached_input_per_million=Decimal("0.10"),
    ),
    "claude-3-5-sonnet-20241022": ModelPrice(
        input_per_million=Decimal("3.00"),
        output_per_million=Decimal("15.00"),
        cached_input_per_million=Decimal("0.30"),
    ),
    # Default fallback
    "default": ModelPrice(
        input_per_million=Decimal("0.20"),
        output_per_million=Decimal("0.80"),
        cached_input_per_million=Decimal("0.10"),
    ),
}

def calculate_llm_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int = 0
) -> Decimal:
    price = PRICING_TABLE.get(model, PRICING_TABLE["default"])
    
    uncached_input = max(0, input_tokens - cached_input_tokens)
    
    cost_uncached = (Decimal(uncached_input) * price.input_per_million) / Decimal(1_000_000)
    cost_cached = (Decimal(cached_input_tokens) * price.cached_input_per_million) / Decimal(1_000_000)
    cost_output = (Decimal(output_tokens) * price.output_per_million) / Decimal(1_000_000)
    
    total = cost_uncached + cost_cached + cost_output
    return total.quantize(Decimal("0.000001"))
