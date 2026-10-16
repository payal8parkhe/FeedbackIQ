# Prompts Changelog & Evaluation Impact

Every prompt update must be tracked here with its corresponding evaluation run and delta on the gold benchmark dataset.

| Version | Date | Target Model | Sentiment Macro-F1 | Topic Micro-F1 | Schema Valid Rate | Notes / Key Changes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **v1** | 2026-10-16 | gpt-4o-mini | Baseline | Baseline | 99.5% | Initial naive prompt with role definition, 18-topic taxonomy, and JSON schema output. |
| **v2** | Upcoming | gpt-4o-mini | TBD | TBD | TBD | Add 8 few-shot examples for sarcasm and rating-text contradictions. |
| **v3** | Upcoming | gpt-4o-mini | TBD | TBD | TBD | Token-aware batching prompt template with stable prefix for provider prompt caching. |
