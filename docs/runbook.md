# FeedbackIQ — Operational Runbook & Failure Playbooks

This runbook covers root causes, alarms, and operational mitigation for key failure modes.

---

### Playbook 1: Provider 429 (Rate Limit) or 5xx Spikes
- **Alarm**: `llm_errors_total{error_class="RateLimitError"} > 10` in 5m.
- **Immediate Mitigation**:
  1. The built-in `ResilientLLMClient` automatically engages exponential backoff with full jitter and respects `Retry-After`.
  2. If the circuit breaker trips (5 consecutive failures in 30s), it enters `OPEN` state.
  3. Verify provider dashboard quota. If primary is exhausted, toggle `FALLBACK_MODEL` in config.

---

### Playbook 2: Schema Validation Failure / Dead-Letter Accumulation
- **Alarm**: `enrich_reviews_total{outcome="dead"} > 1%` of job batch.
- **Immediate Mitigation**:
  1. Inspect failed items via `GET /v1/reviews?status=dead`.
  2. The pipeline executes a 1-item repair retry appending the Pydantic error trace.
  3. If models hallucinate non-taxonomy topics, check if input reviews represent an emerging trend (`other` category) and trigger Topic Discovery.

---

### Playbook 3: Stuck Jobs (Worker Crash Mid-Batch)
- **Alarm**: Reviews remaining in `enriching` status for > 15 minutes.
- **Immediate Mitigation**:
  1. Automatic reaper runs periodically: resets `status = 'pending'` for rows where `updated_at < now() - INTERVAL '15 minutes'` and `attempts < 3`.
  2. Manual command:
     ```sql
     UPDATE reviews SET status = 'pending' WHERE status = 'enriching' AND ingested_at < NOW() - INTERVAL '15 minutes';
     ```

---

### Playbook 4: Grounded Q&A Citation Verification Failure
- **Alarm**: Repeated fallback to evidence-only citations on `/v1/ask`.
- **Immediate Mitigation**:
  1. Inspect the hallucinated citation ID in `llm_calls` logs.
  2. If retrieval top-k contains low semantic density, increase `RETRIEVE_K` or check embedding freshness.
