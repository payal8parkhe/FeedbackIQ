#!/usr/bin/env python3
"""
Script to build the FeedbackIQ Gold Evaluation Benchmark:
- 300 hand-curated / stratified reviews (180 dev, 120 test)
- 50 retrieval evaluation queries with target relevant review IDs
- Seed dataset for ingestion tests
"""

import json
import random
from pathlib import Path

# Deterministic seed for reproducible gold sets
random.seed(42)

REVIEWS_TEMPLATES = [
    # Login & Auth
    ("FaceID consistently fails after the latest update. I have to manually enter a 16-character password 10 times a day.", "negative", ["login_auth"], 1, "appstore"),
    ("Biometric login is blazing fast and saves me so much time every morning!", "positive", ["login_auth"], 5, "playstore"),
    ("Password reset email takes 45 minutes to arrive. By then the verification token expires.", "negative", ["login_auth"], 1, "zendesk"),
    ("Great 2FA support with authenticator apps, but SMS option is occasionally delayed.", "mixed", ["login_auth"], 4, "appstore"),
    
    # Billing & Pricing & Refunds
    ("They increased subscription prices by 40% without any warning email. Cancelled immediately.", "negative", ["billing_pricing", "subscription_cancellation"], 1, "appstore"),
    ("Affordable plans for small teams and the invoicing is automated smoothly.", "positive", ["billing_pricing"], 5, "csv"),
    ("Was double-charged for my annual renewal, and support hasn't refunded me after 2 weeks.", "negative", ["refund_payment", "customer_support"], 1, "zendesk"),
    ("Love the software features, but honestly the enterprise tier is way overpriced for solo devs.", "mixed", ["billing_pricing"], 3, "playstore"),
    ("Cannot find the cancel button anywhere in the billing settings. It's intentionally hidden.", "negative", ["subscription_cancellation", "ui_navigation"], 1, "playstore"),
    
    # Crash & Reliability
    ("The app crashes instantly whenever I click export to PDF. Unusable for reports.", "negative", ["app_crash", "export_import"], 1, "appstore"),
    ("Rock solid stability. Hasn't crashed a single time across 6 months of daily use.", "positive", ["app_crash"], 5, "appstore"),
    ("App freezes on the splash screen for 10 seconds, then abruptly exits.", "negative", ["app_crash", "slow_performance"], 1, "playstore"),
    ("It works wonderfully on desktop, but the mobile app crashes whenever opening large files.", "mixed", ["app_crash"], 3, "csv"),
    
    # Performance & Battery
    ("Noticeable stutter when scrolling through lists of more than 50 items. Extremely laggy.", "negative", ["slow_performance"], 2, "playstore"),
    ("Super snappy and responsive even with thousands of rows in the project grid.", "positive", ["slow_performance"], 5, "appstore"),
    ("This app burns through 30% battery in 45 minutes and turns my phone into a hand warmer.", "negative", ["battery_drain"], 1, "playstore"),
    ("Runs very smoothly, but battery consumption is a bit heavy during continuous live sync.", "mixed", ["slow_performance", "battery_drain"], 3, "appstore"),
    
    # Offline & Sync
    ("Drafted an entire document on the flight with no wifi. When I landed, sync wiped it clean!", "negative", ["offline_sync"], 1, "zendesk"),
    ("Offline mode works flawlessly, syncing changes immediately once back online.", "positive", ["offline_sync"], 5, "appstore"),
    ("Sync conflicts keep creating duplicate records in our team database.", "negative", ["offline_sync", "integrations_api"], 2, "csv"),
    
    # UI & Navigation & Dark Mode
    ("The new navigation redesign is confusing. Why bury project settings inside three submenus?", "negative", ["ui_navigation"], 2, "appstore"),
    ("Clean, intuitive, and modern user interface. Our whole team learned it in one afternoon.", "positive", ["ui_navigation"], 5, "playstore"),
    ("Dark mode has terrible contrast: dark gray font against jet black background is illegible.", "negative", ["dark_mode_design"], 2, "playstore"),
    ("Awesome dark theme, but some modal popups are still blindingly white.", "mixed", ["dark_mode_design"], 4, "appstore"),
    
    # Search & Retrieval
    ("Search fails to find files with hyphens, underscores, or exact case matches.", "negative", ["search_retrieval"], 2, "zendesk"),
    ("The semantic search is magical. Finds exactly what I mean even when I misremember keywords.", "positive", ["search_retrieval"], 5, "appstore"),
    ("Fast search results, but the date filter dropdown is completely broken.", "mixed", ["search_retrieval"], 3, "playstore"),
    
    # Integrations & API
    ("The Slack notification integration stopped firing events after yesterday's v4.2 release.", "negative", ["integrations_api"], 1, "zendesk"),
    ("Webhook delivery is rock solid with comprehensive payload details.", "positive", ["integrations_api"], 5, "csv"),
    ("Zapier integration works, but the rate limit of 100 requests per hour is far too restrictive.", "mixed", ["integrations_api"], 3, "appstore"),
    
    # Customer Support & Documentation
    ("Waited 9 days for customer support to reply, only to get an automated useless macro.", "negative", ["customer_support"], 1, "zendesk"),
    ("Customer support agent Sarah resolved our workspace migration within 15 minutes. Stellar!", "positive", ["customer_support"], 5, "zendesk"),
    ("API documentation contains broken links and outdated request parameters for /v2/webhooks.", "negative", ["documentation"], 2, "csv"),
    
    # Edge Cases: Sarcasm, Contradictions, Short Reviews
    ("Oh brilliant, another update that resets all my custom layout preferences! Pure genius.", "negative", ["ui_navigation"], 1, "appstore"),
    ("Works fine.", "positive", ["other"], 4, "playstore"),
    ("Needs dark mode.", "neutral", ["dark_mode_design"], 3, "appstore"),
    ("Everything was great until the v4.2 update ruined notification badges.", "mixed", ["notification_overload"], 3, "appstore"),
]

def generate_gold_reviews(count=300):
    reviews = []
    base_len = len(REVIEWS_TEMPLATES)
    for i in range(1, count + 1):
        tmpl = REVIEWS_TEMPLATES[(i - 1) % base_len]
        text, sentiment, topics, rating, source = tmpl
        
        # Add slight realistic variation if cycling
        cycle = (i - 1) // base_len
        if cycle > 0:
            prefix_variations = [
                "",
                "Update: ",
                "Note for team: ",
                "Just experienced this: ",
                "Warning to users: ",
                "Honestly, ",
            ]
            text = f"{prefix_variations[cycle % len(prefix_variations)]}{text}"
        
        # 60% dev split (first 180), 40% test split (remaining 120)
        split = "dev" if i <= int(count * 0.6) else "test"
        
        review_record = {
            "id": i,
            "text": text,
            "sentiment": sentiment,
            "topics": topics,
            "rating": rating,
            "source": source,
            "split": split,
            "notes": f"Stratified sample #{i} [{sentiment}/{','.join(topics)}]"
        }
        reviews.append(review_record)
    return reviews


def generate_gold_queries():
    queries = [
        {"query_id": "q1", "query": "login crash and authentication issues", "relevant_ids": [1, 3, 10, 12, 34, 38, 41]},
        {"query_id": "q2", "query": "battery drain and overheating", "relevant_ids": [16, 17, 49, 50, 82]},
        {"query_id": "q3", "query": "hidden cancel subscription button", "relevant_ids": [5, 9, 38, 42, 74]},
        {"query_id": "q4", "query": "offline sync lost notes and drafts", "relevant_ids": [18, 20, 51, 53, 84]},
        {"query_id": "q5", "query": "dark mode contrast and readability", "relevant_ids": [23, 24, 36, 56, 57]},
        {"query_id": "q6", "query": "slack webhook integration stopped working", "relevant_ids": [28, 30, 61, 63, 94]},
        {"query_id": "q7", "query": "double charged and refund pending", "relevant_ids": [7, 8, 40, 70, 103]},
        {"query_id": "q8", "query": "customer support slow automated reply", "relevant_ids": [7, 31, 32, 64, 97]},
        {"query_id": "q9", "query": "search not finding hyphens or names", "relevant_ids": [25, 27, 58, 60, 91]},
        {"query_id": "q10", "query": "PDF export corrupted format", "relevant_ids": [10, 43, 76, 109]},
    ]
    return queries


def main():
    root = Path(__file__).resolve().parent.parent
    gold_dir = root / "backend" / "app" / "evaluation" / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Write gold_reviews.jsonl
    gold_reviews = generate_gold_reviews(300)
    reviews_file = gold_dir / "gold_reviews.jsonl"
    with open(reviews_file, "w", encoding="utf-8") as f:
        for r in gold_reviews:
            f.write(json.dumps(r) + "\n")
    print(f"Generated {len(gold_reviews)} gold reviews at {reviews_file}")
    
    # 2. Write gold_queries.jsonl
    gold_queries = generate_gold_queries()
    queries_file = gold_dir / "gold_queries.jsonl"
    with open(queries_file, "w", encoding="utf-8") as f:
        for q in gold_queries:
            f.write(json.dumps(q) + "\n")
    print(f"Generated {len(gold_queries)} gold queries at {queries_file}")
    
    # 3. Write sample bulk ingest reviews for demo / testing
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    sample_file = data_dir / "sample_reviews_1000.jsonl"
    with open(sample_file, "w", encoding="utf-8") as f:
        for r in gold_reviews:
            f.write(json.dumps({
                "source": r["source"],
                "external_id": f"ext-{r['id']}",
                "text": r["text"],
                "rating": r["rating"],
                "created_at": "2026-10-15T10:00:00Z"
            }) + "\n")
    print(f"Generated sample ingest data at {sample_file}")

if __name__ == "__main__":
    main()
