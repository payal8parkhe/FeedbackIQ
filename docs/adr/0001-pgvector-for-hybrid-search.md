# ADR 0001: Selection of pgvector and PostgreSQL Full-Text for Hybrid Retrieval

## Status
Accepted

## Context
FeedbackIQ requires high-accuracy retrieval over hundreds of thousands of customer reviews. Pure vector search misses exact keyword matches (e.g. error codes, specific button names, app versions), while pure keyword search misses synonyms and semantic intent. Furthermore, queries often require metadata filters (date range, sentiment, star rating, source).

Options evaluated:
1. **PostgreSQL + pgvector (HNSW) + tsvector (GIN)**
2. **Dedicated Vector DB (Pinecone, Qdrant) + Elasticsearch / OpenSearch**
3. **SQLite / In-Memory FAISS**

## Decision
We select **PostgreSQL 16 with pgvector (HNSW index) and native tsvector with GIN index**, fused via **Reciprocal Rank Fusion (RRF, k=60)**.

### Rationale
- **Atomic Operations & Metadata Filtering**: SQL predicates (`WHERE created_at >= ... AND rating <= 2`) join directly with vector cosine distance without two-phase cross-network coordination.
- **Operational Simplicity**: Single datastore for raw reviews, enrichments, vectors, and telemetry without distributed sync lag.
- **Scaling Threshold**: pgvector HNSW provides sub-100ms p95 latency up to ~5 million vectors. When scaling exceeds 5M-10M vectors, we will evaluate dedicated indexing engines.
