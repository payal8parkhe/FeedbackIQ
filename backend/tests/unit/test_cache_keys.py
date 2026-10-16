import pytest
from app.core.enrichment.cache import compute_cache_key

def test_cache_key_deterministic_and_normalized():
    k1 = compute_cache_key("gpt-4o-mini", "v1", "v1", "  App crashed on login!  ")
    k2 = compute_cache_key("gpt-4o-mini", "v1", "v1", "app crashed on login!")
    assert k1 == k2
    assert len(k1) == 64


def test_cache_key_changes_on_model_or_version_change():
    k_base = compute_cache_key("gpt-4o-mini", "v1", "v1", "great app")
    k_diff_model = compute_cache_key("gpt-4o", "v1", "v1", "great app")
    k_diff_prompt = compute_cache_key("gpt-4o-mini", "v2", "v1", "great app")
    k_diff_tax = compute_cache_key("gpt-4o-mini", "v1", "v2", "great app")

    assert k_base != k_diff_model
    assert k_base != k_diff_prompt
    assert k_base != k_diff_tax
