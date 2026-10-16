import math
from typing import Any
from collections import defaultdict
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score, confusion_matrix

def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Calculate 95% Wilson score confidence interval for a proportion."""
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + (z ** 2) / total
    centre = (p + (z ** 2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1 - p) / total) + ((z ** 2) / (4 * (total ** 2))))
    return max(0.0, centre - spread), min(1.0, centre + spread)


def compute_sentiment_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, Any]:
    labels = ["positive", "neutral", "negative", "mixed"]
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    
    # Per-class metrics
    p_per = precision_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    r_per = recall_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    f1_per = f1_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    ci_low, ci_high = wilson_score_interval(
        successes=sum(1 for t, p in zip(y_true, y_pred) if t == p),
        total=len(y_true)
    )

    per_class = {}
    for i, label in enumerate(labels):
        per_class[label] = {
            "precision": round(float(p_per[i]), 4),
            "recall": round(float(r_per[i]), 4),
            "f1": round(float(f1_per[i]), 4),
        }

    return {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "confidence_interval_95": [round(ci_low, 4), round(ci_high, 4)],
        "per_class": per_class,
        "confusion_matrix": cm,
        "labels": labels
    }


def compute_topic_metrics(y_true_topics: list[list[str]], y_pred_topics: list[list[str]]) -> dict[str, Any]:
    # Multi-label micro and macro F1
    all_topics = sorted(list(set(t for sub in y_true_topics for t in sub)))
    
    tp_micro = 0
    fp_micro = 0
    fn_micro = 0

    per_topic_f1 = {}
    f1_list = []

    for topic in all_topics:
        tp = fp = fn = 0
        for true_set, pred_set in zip(y_true_topics, y_pred_topics):
            has_true = topic in true_set
            has_pred = topic in pred_set
            if has_true and has_pred:
                tp += 1
                tp_micro += 1
            elif not has_true and has_pred:
                fp += 1
                fp_micro += 1
            elif has_true and not has_pred:
                fn += 1
                fn_micro += 1
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        per_topic_f1[topic] = round(f1, 4)
        f1_list.append(f1)

    micro_prec = tp_micro / (tp_micro + fp_micro) if (tp_micro + fp_micro) > 0 else 0.0
    micro_rec = tp_micro / (tp_micro + fn_micro) if (tp_micro + fn_micro) > 0 else 0.0
    micro_f1 = (2 * micro_prec * micro_rec) / (micro_prec + micro_rec) if (micro_prec + micro_rec) > 0 else 0.0
    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0

    return {
        "micro_f1": round(float(micro_f1), 4),
        "macro_f1": round(float(macro_f1), 4),
        "per_topic_f1": per_topic_f1
    }


def compute_retrieval_metrics(queries_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate Recall@k and Mean Reciprocal Rank (MRR)."""
    if not queries_results:
        return {"recall_at_5": 0.0, "mrr": 0.0}
    
    recalls_5 = []
    reciprocal_ranks = []

    for q in queries_results:
        target_ids = set(q["target_ids"])
        retrieved_ids = q["retrieved_ids"]
        
        top_5 = set(retrieved_ids[:5])
        hits_5 = len(target_ids.intersection(top_5))
        recalls_5.append(hits_5 / len(target_ids) if target_ids else 0.0)

        rr = 0.0
        for rank, rid in enumerate(retrieved_ids, start=1):
            if rid in target_ids:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    return {
        "recall_at_5": round(sum(recalls_5) / len(recalls_5), 4),
        "mrr": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4)
    }
