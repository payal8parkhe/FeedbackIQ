# FeedbackIQ — Gold Dataset Annotation & Labeling Guide (v1)

This document establishes the gold standard labeling manual for human annotators and evaluation benchmarks. Every review in the gold set (`gold_reviews.jsonl`) must adhere strictly to these operational guidelines.

---

## 1. Sentiment Classification Rules

Annotators must assign exactly one sentiment label: `positive`, `negative`, `neutral`, or `mixed`.

| Label | Definition | Boundary Condition |
| :--- | :--- | :--- |
| **positive** | Expresses clear satisfaction, praise, delight, or gratitude regarding the product. | Minor feature requests at the end of glowing praise remain `positive`. |
| **negative** | Expresses dissatisfaction, frustration, disappointment, bug complaints, or anger. | Polite bug reports ("It seems there's a bug") are `negative`. |
| **neutral** | Factual, objective statements without emotional valence or sentiment tone. | "The app was updated on Tuesday" or purely procedural queries. |
| **mixed** | Contains explicit contrastive components of both substantial praise and substantial complaint. | Must contain both positive and negative clauses (e.g. "Great UI, but constant crashes"). |

> **Crucial Rule**: Sentiment is defined strictly by the **textual content**, NOT the star rating. If a 5-star review says *"Worst update ever, broke everything"*, it is **negative**.

---

## 2. Topic Taxonomy Rules

Annotators must assign between **1 and 5** controlled topic slugs from the controlled taxonomy:

1. `login_auth`: Sign-in, 2FA, biometric ID, password reset, session drops.
2. `account_management`: Profile, team roles, workspace permissions, account deletion.
3. `billing_pricing`: Price hikes, tier changes, invoices, enterprise pricing.
4. `subscription_cancellation`: Auto-renewal, cancellation friction, plan downgrade.
5. `refund_payment`: Double charges, failed transactions, pending refunds.
6. `app_crash`: Fatal crashes, frozen blank screens, unhandled exceptions.
7. `slow_performance`: Latency, sluggish UI, spinner hangs, slow load times.
8. `battery_drain`: High battery consumption, device heating, background CPU.
9. `offline_sync`: Offline note edits lost, cloud sync conflicts.
10. `ui_navigation`: Cluttered menus, confusing tab layouts, awkward gestures.
11. `feature_discoverability`: Hidden settings, lack of tooltips, onboarding confusion.
12. `notification_overload`: Spammy push alerts, too many marketing emails.
13. `dark_mode_design`: Unreadable gray-on-black, poor contrast, color palette.
14. `search_retrieval`: Search queries failing to find items, broken filters.
15. `export_import`: Corrupted CSV/PDF exports, broken table formatting.
16. `integrations_api`: Slack, Zapier, Webhooks, REST API sync breaks.
17. `customer_support`: Rude reps, automated bot loops, unanswered tickets.
18. `documentation`: Outdated guides, missing API endpoints in docs.
19. `other`: Unrelated feedback that fits no existing category.

---

## 3. Ten Specific Edge-Case Rulings

1. **Sarcasm**: *"Oh wonderful, another update that deletes all my saved drafts!"*
   - **Ruling**: Label as `negative`. Topics: `offline_sync` or relevant feature. Sarcastic praise is negative.
2. **Rating Contradiction**: Rating: 5/5, Text: *"Total scam, charged my card twice without consent."*
   - **Ruling**: Label as `negative`. Topic: `refund_payment`. Text overrides rating.
3. **Praise followed by Bug**: *"I love this app, but since v4.2 it crashes whenever I open settings."*
   - **Ruling**: Label as `mixed`. Topics: `app_crash`, `ui_navigation`.
4. **Short Reviews ("Ok", "Works")**: *"Works fine."*
   - **Ruling**: Label as `positive`. Topic: `other` (do not force specific topics on non-specific praise).
5. **Feature Requests Without Complaint**: *"Please add dark mode support!"*
   - **Ruling**: Label as `neutral`. Topic: `dark_mode_design`.
6. **Support Involving Billing**: *"Support refused to refund my duplicate payment."*
   - **Ruling**: Label as `negative`. Topics: `customer_support`, `refund_payment`.
7. **Multiple Complaints**: *"App is freezing, drains my battery, and customer service never answers."*
   - **Ruling**: Label as `negative`. Topics: `slow_performance`, `battery_drain`, `customer_support`.
8. **App Won't Open**: *"Can't get past splash screen, just closes."*
   - **Ruling**: Label as `negative`. Topic: `app_crash`.
9. **Competitive Comparison**: *"Switched from CompetitorX. This is 10x faster but 3x more expensive."*
   - **Ruling**: Label as `mixed`. Topics: `slow_performance`, `billing_pricing`.
10. **Off-Topic / Spam**: *"Download free coins at scam-link.com"*
    - **Ruling**: Label as `neutral`. Topic: `other`.

---

## 4. Inter-Annotator Agreement (Cohen's Kappa)

- Annotations must be conducted independently by two annotators on a subset of at least 100 items.
- Target inter-annotator agreement: $\kappa \ge 0.70$ for sentiment and topic tagging.
- Disagreements are arbitrated by the ML owner to maintain benchmark integrity.
