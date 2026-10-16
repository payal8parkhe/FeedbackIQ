from prometheus_client import Counter, Histogram, Gauge

# Prometheus Metrics Definitions

llm_request_seconds = Histogram(
    "llm_request_seconds",
    "LLM call latency in seconds",
    ["purpose", "model", "status"]
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens consumed by direction and model",
    ["purpose", "model", "direction"]
)

llm_cost_usd_total = Counter(
    "llm_cost_usd_total",
    "Total cost incurred in USD",
    ["purpose", "model"]
)

llm_errors_total = Counter(
    "llm_errors_total",
    "Total LLM errors categorized by error class",
    ["purpose", "model", "error_class"]
)

cache_requests_total = Counter(
    "cache_requests_total",
    "Two-tier cache requests",
    ["tier", "result"]
)

enrich_queue_depth = Gauge(
    "enrich_queue_depth",
    "Current number of pending reviews awaiting enrichment"
)

enrich_reviews_total = Counter(
    "enrich_reviews_total",
    "Total reviews processed by outcome",
    ["outcome"]  # ok, repaired, failed, dead
)

search_seconds = Histogram(
    "search_seconds",
    "Retrieval latency by stage",
    ["stage"]  # embed, vector, keyword, fuse, rerank
)

ask_seconds = Histogram(
    "ask_seconds",
    "Grounded QA latency by stage",
    ["stage"]  # route, retrieve, generate, verify
)

daily_budget_used_ratio = Gauge(
    "daily_budget_used_ratio",
    "Ratio of daily USD budget spent"
)
