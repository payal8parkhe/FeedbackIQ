# FeedbackIQ — Architecture & System Design (HLD)

## 1. Overview
FeedbackIQ is an enterprise AI platform that ingests unstructured customer feedback, enriches each review into validated JSON (sentiment, multi-label taxonomy topics, summaries, confidence), and powers hybrid semantic search alongside strictly grounded Q&A with verifiable citations.

## 2. High-Level Flow Diagram
```
                        +----------------------+
   CSV / API / Webhook  |      Web UI (Next)   |
          |             +----------+-----------+
          v                        | REST/SSE
+-------------------+    +---------v-----------+
|  Ingestion API    |    |   Query API         |  (FastAPI)
|  validate, dedupe |    |  search, ask, stats |
+---------+---------+    +----+-----------+----+
          |                   |           |
          v                   v           v
   +-------------+     +-----------+  +--------------+
   | Redis queue |     | Retriever |  | Answer Svc   |
   +------+------+     | hybrid+RRF|  | prompt+cite  |
          |            +-----+-----+  +------+-------+
          v                  |               |
+---------------------+      |               |
|  Enrichment Workers |      |               |
| preprocess -> batch |      |               |
| -> cache check ->   |      |               |
| LLM -> validate ->  |      |               |
| repair -> persist   |      |               |
+----+-------+--------+      |               |
     |       |               v               v
     |       |        +---------------------------+
     |       +------> |  PostgreSQL + pgvector    |
     |                |  reviews, enrichments,    |
     |                |  embeddings, topics,      |
     v                |  llm_calls, eval_runs     |
+-----------+         +---------------------------+
| LLM / Emb |<--- LLMClient + Embedder interfaces (retry, rate limit,
| providers |     usage + cost accounting, trace id)
+-----------+
```

## 3. Core Design Principles
1. **Offline Write Path vs. Online Read Path**: Ingestion & enrichment are throughput- and cost-bound (batching, caching, offline retry), while querying is latency-bound (hybrid retrieval + SSE streaming under 4s).
2. **Postgres as Single Source of Truth**: Relational constraints, JSONB flexibility, full-text GIN indexing, and pgvector cosine search live in a single ACID engine.
3. **Structured Output Ladder**: Constrained JSON -> Pydantic validation -> Invariant check -> Single-item retry repair -> Dead-letter queue. Zero silent drops.
4. **Engineering over Guesswork**: Hand-labeled gold evaluation set (300 items), Cohen's kappa measurement, and automated regression gates in CI.
