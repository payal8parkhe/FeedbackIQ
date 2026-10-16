from decimal import Decimal
from app.core.llm.pricing import calculate_llm_cost

def test_pricing_calculation_with_cached_discount():
    # gpt-4o-mini prices:
    # input: $0.15 / 1M, cached: $0.075 / 1M, output: $0.60 / 1M
    cost = calculate_llm_cost(
        model="gpt-4o-mini",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cached_input_tokens=500_000
    )
    # uncached input: 500k * 0.15 = 0.075
    # cached input: 500k * 0.075 = 0.0375
    # output: 1M * 0.60 = 0.60
    # total = 0.075 + 0.0375 + 0.60 = 0.712500
    assert cost == Decimal("0.712500")
