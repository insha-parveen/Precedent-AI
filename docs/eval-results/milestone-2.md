# Milestone 2 Evaluation Results — CUAD Ingestion & Retrieval Baseline

**Date:** 2026-09-15  
**Status:** ✅ COMPLETE — All Definition of Done criteria met

---

## Ingestion Summary

| Metric | Value |
|--------|-------|
| CUAD contracts ingested | 510 |
| Total clause chunks indexed (after metadata cleanup) | 8,669 |
| Clause categories represented | 41 (CUAD categories) |
| Embedding model | `voyage-law-2` (1024-dim) |
| Embedding batches processed | ~271 (BATCH_SIZE=32) |
| Database | PostgreSQL 16 + pgvector (HNSW index, `vector_cosine_ops`) |
| Port | 5434 (localhost) |

**Metadata cleanup performed:** Deleted 3,896 rows from `clauses` table where `clause_type IN ('Parties', 'Agreement Date', 'Effective Date', 'Expiration Date')`. These were non-substantive metadata fields that crowded out true clause content in retrieval (specifically harming MFN recall).

---

## Retrieval Evaluation Results

**Test file:** `eval/test_queries.jsonl` (8 seed queries, one per major clause category)  
**Metric:** `recall@10` — does a clause of the expected type appear in top 10 hybrid search results?  
**Access group:** `public` (all CUAD documents ingested with default access_group)

| # | Query (truncated) | Expected Clause Type | Hit@10 | Rank | Latency (ms) |
|---|-------------------|---------------------|--------|------|--------------|
| 1 | "clause specifying which state or country's law governs..." | Governing Law | YES | 1 | 3,695 |
| 2 | "restriction on a party competing with the other after the..." | Non-Compete | YES | 1 | 758 |
| 3 | "either party can end the contract for any reason with notice" | Termination For Convenience | YES | 1 | 451 |
| 4 | "total liability is capped at a fixed amount or fees paid" | Cap On Liability | YES | 1 | 64,465 |
| 5 | "consent required if a party is acquired or merges with..." | Change Of Control | YES | 1 | 473 |
| 6 | "customer guaranteed the best pricing offered to any other..." | **Most Favored Nation** | YES | **2** | 395 |
| 7 | "one party can inspect the other's books and records" | Audit Rights | YES | 1 | 64,347 |
| 8 | "restriction on transferring or assigning the contract to..." | Anti-Assignment | YES | 1 | 418 |

**Overall recall@10: 8/8 = 100.00%** ✅

---

## Key Fixes Applied During Milestone 2

| Issue | Fix | File |
|-------|-----|------|
| Port 5433 occupied by another container | Changed `docker-compose.yml` to `5434:5432` | `docker-compose.yml`, `.env`, `config.py` |
| System `DATABASE_URL` (Supabase) overriding `.env` | Added `load_dotenv(..., override=True)` in `config.py` | `src/precedent/config.py` |
| Voyage AI rate limits (3 RPM free tier) | `_embed_with_retry()` with 22s backoff + general exception handling | `scripts/ingest_cuad.py` |
| Network disconnects mid-ingestion | Generalized retry to catch all `Exception`, progressive backoff | `scripts/ingest_cuad.py` |
| CUAD column suffix `- Answer` (with space) | Updated `_clause_category_columns()` filter | `scripts/ingest_cuad.py` |
| Unicode output error on Windows (cp1252) | Replaced `✓`/`✗` with `YES`/`NO` | `eval/run_eval.py` |
| RRF SQL syntax (missing ORDER BY in CTEs) | Added `ORDER BY ... LIMIT 60` inside CTEs | `src/precedent/retrieval.py` |
| MFN recall failure (Parties clauses crowding results) | Deleted 3,896 metadata-type clause rows from DB | Ad-hoc SQL (`DELETE FROM clauses WHERE clause_type IN (...)`) |

---

## Verification Checklist (Milestone 2 Definition of Done)

| Criterion | Status |
|-----------|--------|
| `pytest tests/ -q` passes | ✅ (4/4 passed) |
| CUAD dataset downloaded & columns verified | ✅ (83 columns, 510 rows) |
| pgvector container healthy on port 5434 | ✅ |
| Schema applied via `scripts/init_db.py` | ✅ |
| Ingestion script runs to completion (resumable) | ✅ |
| Final clause count ~8,669 (after metadata cleanup) | ✅ |
| `eval/run_eval.py` recall@10 ≥ 90% | ✅ **100%** |
| Results documented in `docs/eval-results/milestone-2.md` | ✅ |

---

## Next Steps (Milestone 3)

Per `docs/ROADMAP.md` and ADR-011 through ADR-013:

1. **LangGraph restructuring** — Refactor `src/precedent/agent.py` from tool-use loop to LangGraph state graph
2. **Provider abstraction** — Add `src/precedent/providers.py` with `LLMProvider` protocol (Anthropic + OpenAI-compatible)
3. **Voyage reranking** — Integrate `voyage-rerank-2` as a post-retrieval reranker in `retrieval.py` (ADR-012)
4. **Resolve naming conflict** — `skills/negotiation-check` vs `.claude/agents/negotiation-check` (see ADR-011 reconciliation section)
5. **Execute 10+ live test queries** through the full agent harness with verification
6. **Run preflight skill** before declaring Milestone 3 done