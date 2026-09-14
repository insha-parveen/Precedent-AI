-- Precedent schema.
-- Applied by scripts/init_db.py. Treat as a migration once data is ingested —
-- don't hand-edit a live DB, add a new numbered migration file instead.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- One row per source contract (a CUAD PDF, or an EDGAR exhibit).
CREATE TABLE IF NOT EXISTS documents (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL CHECK (source IN ('cuad', 'edgar')),
    external_id     TEXT NOT NULL,             -- CUAD filename, or EDGAR accession number
    title           TEXT NOT NULL,
    doc_type        TEXT,                      -- e.g. 'License Agreement', 'Credit Agreement'
    parties         TEXT[] DEFAULT '{}',
    filing_date     DATE,
    -- Permission simulation: every row belongs to an access group, the same way a real
    -- deployment would tag documents by matter/client. Queries MUST filter on this —
    -- see retrieval.py. 'public' is the default open group for this demo corpus.
    access_group    TEXT NOT NULL DEFAULT 'public',
    source_url      TEXT,
    raw_text        TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, external_id)
);

-- One row per labeled clause span. Chunking is clause-boundary-aware, not fixed-size:
-- for CUAD this comes directly from the dataset's own expert-labeled character offsets
-- (see scripts/ingest_cuad.py) rather than an arbitrary sliding window.
CREATE TABLE IF NOT EXISTS clauses (
    id              BIGSERIAL PRIMARY KEY,
    document_id     BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    clause_type     TEXT NOT NULL,              -- one of CUAD's 41 categories, or 'Other'
    clause_text     TEXT NOT NULL,
    char_start      INT,
    char_end        INT,
    -- Match EMBEDDING_DIM in .env to whatever embedding model you actually call.
    -- voyage-law-2 / voyage-4 default to 1024; verify against the model docs before
    -- ingesting — changing this after data is loaded means re-embedding everything.
    embedding       VECTOR(1024),
    tsv             TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', clause_text)) STORED,
    access_group    TEXT NOT NULL DEFAULT 'public',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clauses_embedding
    ON clauses USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_clauses_tsv
    ON clauses USING gin (tsv);

CREATE INDEX IF NOT EXISTS idx_clauses_type
    ON clauses (clause_type);

CREATE INDEX IF NOT EXISTS idx_clauses_access_group
    ON clauses (access_group);

CREATE INDEX IF NOT EXISTS idx_documents_parties
    ON documents USING gin (parties);

CREATE INDEX IF NOT EXISTS idx_documents_doc_type
    ON documents (doc_type);

-- Governance / agent-operations log. Every agent run writes exactly one row here.
-- This is the thing most portfolio RAG projects skip — see CLAUDE.md rule 5.
CREATE TABLE IF NOT EXISTS skill_runs (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now(),
    skill_name      TEXT,                       -- NULL if no skill matched
    user_query      TEXT NOT NULL,
    model           TEXT NOT NULL,
    tool_calls      JSONB NOT NULL DEFAULT '[]', -- [{name, input, result_doc_ids}, ...]
    cited_doc_ids   BIGINT[] DEFAULT '{}',
    grounded        BOOLEAN NOT NULL,            -- did the final answer pass the citation check
    input_tokens    INT NOT NULL DEFAULT 0,
    output_tokens   INT NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(10, 6) NOT NULL DEFAULT 0,
    latency_ms      INT NOT NULL,
    error           TEXT
);

CREATE INDEX IF NOT EXISTS idx_skill_runs_ts ON skill_runs (ts DESC);
CREATE INDEX IF NOT EXISTS idx_skill_runs_skill ON skill_runs (skill_name);
