# FeedbackIQ Evaluation Report — DEV Split
**Date**: 2026-10-16T07:38:28.236755 | **Model**: `gpt-4o-mini` | **Prompt**: `v1` | **Dataset Size**: 180

## 1. Key Success Metrics vs Plan Targets
| Metric | Result | Target | Status |
| :--- | :--- | :--- | :--- |
| **Sentiment Accuracy** | **44.4%** (95% CI: [37.4%, 51.7%]) | >= 90.0% | NEEDS_TUNING |
| **Sentiment Macro-F1** | **0.4071** | >= 0.850 | NEEDS_TUNING |
| **Topic Micro-F1** | **0.8676** | >= 0.750 | PASS |
| **Topic Macro-F1** | **0.8669** | >= 0.700 | INFO |
| **Schema Valid Rate** | **100.0%** | >= 99.5% | PASS |
| **Cost / 1k Reviews** | **$0.1410** | < $0.50 | PASS |
| **Processing Latency** | **25 ms** (Avg 0.1 ms/item) | < 500 ms/item | PASS |

## 2. Per-Class Sentiment Breakdown
| Sentiment Class | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- |
| `positive` | 0.592 | 0.592 | 0.592 |
| `neutral` | 0.054 | 1.000 | 0.103 |
| `negative` | 0.792 | 0.432 | 0.559 |
| `mixed` | 1.000 | 0.231 | 0.375 |

## 3. Confusion Matrix
| True \ Pred | `positive` | `neutral` | `negative` | `mixed` |
| :--- | --- | --- | --- | --- |
| `positive` | 29 | 15 | 5 | 0 |
| `neutral` | 0 | 4 | 0 | 0 |
| `negative` | 5 | 45 | 38 | 0 |
| `mixed` | 15 | 10 | 5 | 9 |
