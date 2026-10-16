-- FeedbackIQ PostgreSQL + pgvector Schema

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS reviews (
  id            BIGSERIAL PRIMARY KEY,
  org_id        INT NOT NULL DEFAULT 1,
  source        TEXT NOT NULL,
  external_id   TEXT,
  content_hash  CHAR(64) NOT NULL,
  raw_text      TEXT NOT NULL,
  clean_text    TEXT NOT NULL,
  language      TEXT DEFAULT 'en',
  rating        SMALLINT CHECK (rating BETWEEN 1 AND 5),
  created_at    TIMESTAMPTZ NOT NULL,
  ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  status        TEXT NOT NULL DEFAULT 'pending',
  attempts      SMALLINT NOT NULL DEFAULT 0,
  tsv           TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', clean_text)) STORED,
  UNIQUE (org_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews (status) WHERE status <> 'enriched';
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews (created_at);
CREATE INDEX IF NOT EXISTS reviews_tsv_gin ON reviews USING GIN (tsv);

CREATE TABLE IF NOT EXISTS enrichments (
  review_id        BIGINT PRIMARY KEY REFERENCES reviews(id) ON DELETE CASCADE,
  sentiment        TEXT NOT NULL CHECK (sentiment IN ('positive','neutral','negative','mixed')),
  sentiment_score  REAL,
  topics           TEXT[] NOT NULL,
  summary          TEXT NOT NULL,
  confidence       REAL,
  model            TEXT NOT NULL,
  prompt_version   TEXT NOT NULL,
  taxonomy_version TEXT NOT NULL,
  raw_json         JSONB NOT NULL,
  enriched_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_enrichments_topics ON enrichments USING GIN (topics);
CREATE INDEX IF NOT EXISTS idx_enrichments_sentiment ON enrichments (sentiment);

CREATE TABLE IF NOT EXISTS review_embeddings (
  review_id  BIGINT PRIMARY KEY REFERENCES reviews(id) ON DELETE CASCADE,
  embedding  VECTOR(1024) NOT NULL,
  model      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_review_embeddings_hnsw ON review_embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

CREATE TABLE IF NOT EXISTS topics (
  slug TEXT PRIMARY KEY,
  label TEXT,
  description TEXT,
  parent_slug TEXT,
  active BOOLEAN DEFAULT true,
  taxonomy_version TEXT
);

CREATE TABLE IF NOT EXISTS llm_cache (
  cache_key   CHAR(64) PRIMARY KEY,
  response    JSONB NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now(),
  hits        INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS llm_calls (
  id BIGSERIAL PRIMARY KEY,
  trace_id TEXT,
  purpose TEXT,
  model TEXT,
  prompt_version TEXT,
  batch_size INT,
  input_tokens INT,
  output_tokens INT,
  cached_input_tokens INT,
  cost_usd NUMERIC(10,6),
  latency_ms INT,
  status TEXT,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_created_at_purpose ON llm_calls (created_at, purpose);

CREATE TABLE IF NOT EXISTS ingest_jobs (
  id UUID PRIMARY KEY,
  total INT,
  done INT,
  failed INT,
  state TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_runs (
  id BIGSERIAL PRIMARY KEY,
  git_sha TEXT,
  prompt_version TEXT,
  model TEXT,
  dataset TEXT,
  metrics JSONB,
  cost_usd NUMERIC,
  p95_latency_ms INT,
  created_at TIMESTAMPTZ DEFAULT now()
);
