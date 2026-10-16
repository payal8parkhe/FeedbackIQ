import argparse
import json
import sys
from pathlib import Path

def compare_reports(base_path: Path, candidate_path: Path, fail_on_regression: bool = False) -> bool:
    if not base_path.exists():
        print(f"Warning: Baseline report {base_path} not found. Skipping diff.")
        return True
    if not candidate_path.exists():
        print(f"Error: Candidate report {candidate_path} not found.")
        return False

    with open(base_path, "r", encoding="utf-8") as f:
        base = json.load(f)
    with open(candidate_path, "r", encoding="utf-8") as f:
        candidate = json.load(f)

    b_f1 = base["sentiment_metrics"]["macro_f1"]
    c_f1 = candidate["sentiment_metrics"]["macro_f1"]
    f1_delta = c_f1 - b_f1

    b_acc = base["sentiment_metrics"]["accuracy"]
    c_acc = candidate["sentiment_metrics"]["accuracy"]
    acc_delta = c_acc - b_acc

    b_valid = base["schema_reliability"]["schema_valid_rate"]
    c_valid = candidate["schema_reliability"]["schema_valid_rate"]

    b_cost = base["cost_and_latency"]["cost_per_1k_usd"]
    c_cost = candidate["cost_and_latency"]["cost_per_1k_usd"]
    cost_ratio = (c_cost / b_cost) if b_cost > 0 else 1.0

    print("=" * 60)
    print("FEEDBACKIQ EVALUATION REGRESSION GATE")
    print("=" * 60)
    print(f"Sentiment Macro-F1:  Base = {b_f1:.4f} | Cand = {c_f1:.4f} (Delta: {f1_delta:+.4f})")
    print(f"Sentiment Accuracy:  Base = {b_acc*100:.1f}% | Cand = {c_acc*100:.1f}% (Delta: {acc_delta*100:+.1f}%)")
    print(f"Schema Valid Rate:   Base = {b_valid*100:.1f}% | Cand = {c_valid*100:.1f}%")
    print(f"Cost per 1k Reviews: Base = ${b_cost:.4f} | Cand = ${c_cost:.4f} (Ratio: {cost_ratio:.2f}x)")
    print("-" * 60)

    regressed = False
    reasons = []

    if f1_delta < -0.02:  # Drops more than 2 points
        regressed = True
        reasons.append(f"Macro-F1 dropped by {abs(f1_delta):.4f} (limit: -0.020)")

    if c_valid < 0.99:
        regressed = True
        reasons.append(f"Schema validity is {c_valid*100:.1f}% (target: >= 99.0%)")

    if cost_ratio > 1.15:
        regressed = True
        reasons.append(f"Cost increased by {((cost_ratio - 1) * 100):.1f}% (limit: +15%)")

    if regressed:
        print("[FAIL] CI Regression Gate Failed:")
        for r in reasons:
            print(f"  - {r}")
        if fail_on_regression:
            return False
    else:
        print("[PASS] Quality, schema validity, and cost within acceptable bounds.")

    return True


def main():
    parser = argparse.ArgumentParser(description="Compare FeedbackIQ evaluation runs")
    parser.add_argument("--base", type=str, required=True, help="Baseline JSON report path")
    parser.add_argument("--candidate", type=str, required=True, help="Candidate JSON report path")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit code 1 on regression")
    args = parser.parse_args()

    passed = compare_reports(Path(args.base), Path(args.candidate), fail_on_regression=args.fail_on_regression)
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
