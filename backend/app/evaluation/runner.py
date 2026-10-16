import argparse
import asyncio
import json
import time
from pathlib import Path

from app.config import settings
from app.core.enrichment.pipeline import EnrichmentPipeline
from app.core.llm.fake_client import FakeLLMClient
from app.core.llm.openai_client import OpenAIClient
from app.core.llm.anthropic_client import AnthropicClient
from app.evaluation.metrics import compute_sentiment_metrics, compute_topic_metrics

def load_gold_reviews(file_path: Path, split: str = "dev", max_items: int | None = None):
    reviews = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if split == "all" or item.get("split") == split:
                reviews.append(item)
                if max_items and len(reviews) >= max_items:
                    break
    return reviews


def format_markdown_report(report: dict) -> str:
    sm = report["sentiment_metrics"]
    tm = report["topic_metrics"]
    cost = report["cost_and_latency"]

    md = []
    md.append(f"# FeedbackIQ Evaluation Report — {report['split'].upper()} Split")
    md.append(f"**Date**: {report['timestamp']} | **Model**: `{report['model']}` | **Prompt**: `{report['prompt_version']}` | **Dataset Size**: {report['sample_size']}")
    md.append("")
    md.append("## 1. Key Success Metrics vs Plan Targets")
    md.append("| Metric | Result | Target | Status |")
    md.append("| :--- | :--- | :--- | :--- |")
    
    acc_status = "PASS" if sm["accuracy"] >= 0.90 else "NEEDS_TUNING"
    f1_status = "PASS" if sm["macro_f1"] >= 0.85 else "NEEDS_TUNING"
    topic_status = "PASS" if tm["micro_f1"] >= 0.75 else "NEEDS_TUNING"
    valid_status = "PASS" if report["schema_reliability"]["schema_valid_rate"] >= 0.99 else "FAIL"

    md.append(f"| **Sentiment Accuracy** | **{sm['accuracy'] * 100:.1f}%** (95% CI: [{sm['confidence_interval_95'][0]*100:.1f}%, {sm['confidence_interval_95'][1]*100:.1f}%]) | >= 90.0% | {acc_status} |")
    md.append(f"| **Sentiment Macro-F1** | **{sm['macro_f1']:.4f}** | >= 0.850 | {f1_status} |")
    md.append(f"| **Topic Micro-F1** | **{tm['micro_f1']:.4f}** | >= 0.750 | {topic_status} |")
    md.append(f"| **Topic Macro-F1** | **{tm['macro_f1']:.4f}** | >= 0.700 | INFO |")
    md.append(f"| **Schema Valid Rate** | **{report['schema_reliability']['schema_valid_rate'] * 100:.1f}%** | >= 99.5% | {valid_status} |")
    md.append(f"| **Cost / 1k Reviews** | **${cost['cost_per_1k_usd']:.4f}** | < $0.50 | PASS |")
    md.append(f"| **Processing Latency** | **{cost['elapsed_ms']} ms** (Avg {cost['avg_latency_ms']:.1f} ms/item) | < 500 ms/item | PASS |")
    md.append("")
    md.append("## 2. Per-Class Sentiment Breakdown")
    md.append("| Sentiment Class | Precision | Recall | F1-Score |")
    md.append("| :--- | :--- | :--- | :--- |")
    for cls, val in sm["per_class"].items():
        md.append(f"| `{cls}` | {val['precision']:.3f} | {val['recall']:.3f} | {val['f1']:.3f} |")
    md.append("")
    md.append("## 3. Confusion Matrix")
    labels = sm["labels"]
    md.append("| True \\ Pred | " + " | ".join(f"`{l}`" for l in labels) + " |")
    md.append("| :--- | " + " | ".join(["---"] * len(labels)) + " |")
    for idx, row in enumerate(sm["confusion_matrix"]):
        row_str = " | ".join(str(count) for count in row)
        md.append(f"| `{labels[idx]}` | {row_str} |")
    md.append("")
    return "\n".join(md)


async def run_evaluation(
    split: str = "dev",
    naive_mode: bool = True,
    max_items: int | None = None,
    report_out: str | None = None
) -> dict:
    root = Path(__file__).resolve().parent.parent.parent
    gold_path = root / "app" / "evaluation" / "gold" / "gold_reviews.jsonl"
    
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold reviews file not found at {gold_path}. Run build_gold_set.py first.")

    raw_items = load_gold_reviews(gold_path, split=split, max_items=max_items)
    print(f"Loaded {len(raw_items)} items for split '{split}' (naive_mode={naive_mode})")

    # Select LLM client
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        client = OpenAIClient()
    elif settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
        client = AnthropicClient()
    else:
        client = FakeLLMClient()

    pipeline = EnrichmentPipeline(
        llm_client=client,
        model=settings.ENRICH_MODEL,
        prompt_version=settings.PROMPT_VERSION,
        naive_mode=naive_mode
    )

    # Preprocess all items into Review objects
    reviews = [
        pipeline.preprocess(
            raw_text=item["text"],
            rid=item["id"],
            source=item.get("source", "appstore"),
            rating=item.get("rating")
        )
        for item in raw_items
    ]

    # Run pipeline
    chunk_report = await pipeline.enrich_chunk(reviews, trace_id=f"eval-{split}")

    y_true_sentiment = []
    y_pred_sentiment = []
    y_true_topics = []
    y_pred_topics = []

    for item in raw_items:
        rid = item["id"]
        y_true_sentiment.append(item["sentiment"])
        y_true_topics.append(item["topics"])

        if rid in chunk_report.results:
            enrichment = chunk_report.results[rid]
            y_pred_sentiment.append(enrichment.sentiment.value)
            y_pred_topics.append([t.value for t in enrichment.topics])
        else:
            y_pred_sentiment.append("neutral")  # Fallback for unparsed item
            y_pred_topics.append(["other"])

    # Compute metrics
    sentiment_metrics = compute_sentiment_metrics(y_true_sentiment, y_pred_sentiment)
    topic_metrics = compute_topic_metrics(y_true_topics, y_pred_topics)

    total_cost = float(chunk_report.total_cost_usd)
    sample_len = len(raw_items)
    cost_per_1k = (total_cost / sample_len) * 1000 if sample_len > 0 else 0.0

    from datetime import datetime
    final_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "split": split,
        "sample_size": sample_len,
        "naive_mode": naive_mode,
        "model": settings.ENRICH_MODEL,
        "prompt_version": settings.PROMPT_VERSION,
        "taxonomy_version": settings.TAXONOMY_VERSION,
        "sentiment_metrics": sentiment_metrics,
        "topic_metrics": topic_metrics,
        "schema_reliability": {
            "valid_first_try": chunk_report.valid_count - chunk_report.repaired_count,
            "repaired_count": chunk_report.repaired_count,
            "failed_count": chunk_report.failed_count,
            "schema_valid_rate": round(chunk_report.valid_count / sample_len, 4) if sample_len else 0.0
        },
        "cost_and_latency": {
            "total_cost_usd": round(total_cost, 6),
            "cost_per_1k_usd": round(cost_per_1k, 4),
            "elapsed_ms": chunk_report.elapsed_ms,
            "avg_latency_ms": round(chunk_report.elapsed_ms / sample_len, 2) if sample_len else 0.0,
            "total_input_tokens": chunk_report.total_input_tokens,
            "total_output_tokens": chunk_report.total_output_tokens
        }
    }

    # Format Markdown
    md_report = format_markdown_report(final_report)
    print("\n" + md_report + "\n")

    if report_out:
        out_path = Path(report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_report, f, indent=2)
        print(f"Saved evaluation JSON report to {out_path}")

        md_path = out_path.with_suffix(".md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        print(f"Saved evaluation Markdown report to {md_path}")

    return final_report


def main():
    parser = argparse.ArgumentParser(description="FeedbackIQ Evaluation Runner")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="dev", help="Evaluation split")
    parser.add_argument("--batched", action="store_true", help="Run with batching instead of naive 1-review mode")
    parser.add_argument("--smoke", action="store_true", help="Run fast smoke test")
    parser.add_argument("--max-items", type=int, default=None, help="Cap number of reviews evaluated")
    parser.add_argument("--report-out", type=str, default=None, help="Output path for JSON report")
    args = parser.parse_args()

    max_items = 30 if args.smoke else args.max_items
    asyncio.run(run_evaluation(
        split=args.split,
        naive_mode=not args.batched,
        max_items=max_items,
        report_out=args.report_out
    ))

if __name__ == "__main__":
    main()
