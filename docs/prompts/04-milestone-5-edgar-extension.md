# Milestone 5: SEC EDGAR Extension — Professional Engineer Prompt

## Context

Precedent has successfully completed Milestones 1–4: a production-grade retrieval-first contract intelligence agent with CUAD data ingested, a LangGraph agent harness with citation-or-refuse enforcement, an MCP server exposing three tools, and a CLI. All tests pass (20/20).

**Milestone 5 is a stretch goal** (per ROADMAP.md) to prove the architecture generalizes beyond a single pre-labeled dataset. The goal: pull real SEC EDGAR filings (merger agreements, credit agreements), classify their clauses against the CUAD 41-category taxonomy using a classifier model (Haiku), and demonstrate a cross-source `negotiation-check` query that pulls from both CUAD and EDGAR in one answer.

---

## Non-Negotiable Constraints (from CLAUDE.md)

1. **Retrieval before generation, always** — No parametric knowledge answers.
2. **Citation-or-refuse enforced in code** — Checked before any answer returns.
3. **Permissions are real** — Every retrieval query filters on `access_group`.
4. **Skills are data, not code** — Behavioral differences live in SKILL.md; no `if skill.name == ...` branching.
5. **Every change to retrieval/chunking/embeddings/skill gets an eval run** — Regression needs documented reason.
6. **Reranking/orchestration changes must be measured** — Report before/after numbers.

Additional Milestone 5 constraints:
- **NFR-3 (cost discipline):** Ingestion/classification prefers cheapest model meeting quality bar (Haiku over Sonnet, Batch API for bulk).
- **NFR-5 (licensing):** Only CC-BY-4.0 or public-record data. SEC EDGAR is public record.
- **No confidential data** — Public corpora only.

---

## Architecture Decisions Already Made (Reference)

- **ADR-001:** Retrieval-first index (hybrid search + reranking)
- **ADR-009:** Access-group filtering on every query
- **ADR-011:** LangGraph state graph (route → generate → tools → check_citations → retry)
- **ADR-012:** Voyage reranking over hybrid search top-20/30
- **ADR-013:** Provider abstraction (Gemini primary, Grok fallback)
- **ADR-014:** Web UI (Milestone 6) reuses MCP server functions — no parallel logic

The schema already supports EDGAR: `documents.source` has CHECK constraint `('cuad', 'edgar')`.

---

## Deliverables

### 1. EDGAR Connector (`scripts/ingest_edgar.py`)
- Pull a **small, curated set** of real filed contracts from SEC EDGAR
- Focus: **Merger agreements** (DEFM14A exhibits) and **Credit agreements** (8-K exhibits, 10-K exhibits)
- Use SEC's public API (no auth required, rate limit: 10 req/sec)
- Extract exhibit text, chunk at clause boundaries (heuristic: section headers, numbered clauses)
- Store with `source='edgar'`, `external_id` = accession number, `filing_date`, `source_url`

### 2. Clause Classifier (`src/precedent/classifier.py`)
- **New module** — classifies raw EDGAR clause text into CUAD's 41 categories
- Uses **Haiku (Anthropic)** via existing `providers.py` abstraction — first time this model is exercised
- Batch API for cost efficiency on bulk classification
- Output: `clause_type` (one of 41 CUAD categories or "Other")
- Spot-check a sample against source text for quality validation

### 3. Unified Ingestion Pipeline
- Extend `scripts/ingest_cuad.py` patterns for EDGAR or create parallel `scripts/ingest_edgar.py`
- Both pipelines write to the **same tables** (`documents`, `clauses`) with `source` distinguishing them
- Reuse existing `hybrid_search` and `rerank` — no retrieval changes needed

### 4. Cross-Source Verification
- Run a `negotiation-check` query that demonstrably pulls from **both CUAD and EDGAR** documents
- Verify the skill's 4-stage pipeline (locate → verify → extract → synthesize) works across sources
- Log the run in `skill_runs` with citations showing both `source='cuad'` and `source='edgar'` doc IDs

### 5. Evaluation Update
- Extend `eval/run_eval.py` and `eval/test_queries.jsonl` to include EDGAR-sourced queries
- Run recall@10 evaluation on the combined corpus
- Save report to `docs/eval-results/milestone-5.md`

### 6. Tests
- Unit tests for EDGAR connector (mocked HTTP)
- Unit tests for classifier (mocked LLM)
- Integration test: end-to-end ingest → search → ask with EDGAR data

---

## Technical Approach Details

### EDGAR Connector
```python
# scripts/ingest_edgar.py
# - Use SEC's submissions endpoint: https://data.sec.gov/submissions/CIK{cik}.json
# - Filter for filing types: 8-K (exhibits 10.1, 10.2 for material agreements), 
#   DEFM14A (merger agreement exhibits), 10-K/10-Q (credit agreement exhibits)
# - Download exhibit text via: https://www.sec.gov/Archives/{accession_no}/{exhibit_file}
# - Parse with heuristic: split on "Section", "Article", numbered clauses (1., 2., (a), (i))
# - Store minimal metadata: CIK, company name, filing_date, accession, exhibit_number
```

### Classifier
```python
# src/precedent/classifier.py
# - Input: clause_text (str), returns: clause_type (str)
# - Prompt includes all 41 CUAD category definitions
# - Use existing LLMProvider (AnthropicProvider with Haiku)
# - Batch classification for cost control
# - Confidence threshold: if < 0.7, label "Other"
```

### Database
- No schema changes needed — existing tables support `source='edgar'`
- `filing_date` and `source_url` columns already exist for EDGAR metadata

### Retrieval
- `hybrid_search` already filters on `access_groups` — EDGAR docs use `access_group='public'`
- No changes to `retrieval.py` required

---

## Acceptance Criteria (Definition of Done from ROADMAP.md)

- [ ] EDGAR full-text search connector pulls a small set of real filed contracts (merger agreements, credit agreements)
- [ ] Classifier model (Haiku) exercises for first time — tags clauses against CUAD's 41-category taxonomy, spot-check sample against source text
- [ ] Cross-source `negotiation-check` query demonstrably pulls from both CUAD and EDGAR in one answer
- [ ] All existing tests pass + new EDGAR/classifier tests pass
- [ ] Eval report saved to `docs/eval-results/milestone-5.md`

---

## Estimated Effort

| Component | Est. Files | Est. LoC | Complexity |
|---|---|---|---|
| EDGAR connector | 1 new script | ~150 | Medium (HTTP, parsing) |
| Classifier | 1 new module | ~80 | Medium (prompt engineering) |
| Ingestion orchestration | 1 script | ~100 | Low (reuses patterns) |
| Tests | 2 new test files | ~100 | Medium |
| Eval extension | 2 modified files | ~50 | Low |
| **Total** | **~5 files** | **~480** | **~2-3 sessions** |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| SEC rate limits / HTML changes | Medium | Medium | Respect 10 req/sec; parse robustly; cache downloads |
| Classifier accuracy on EDGAR text | Medium | High | Spot-check 20+ samples; fallback to "Other"; log confidence |
| Exhibit text extraction fails (PDFs, scanned) | Medium | Medium | Skip non-text exhibits; focus on text exhibits first |
| Cross-source retrieval quality degrades | Low | Medium | Run eval before/after; hybrid search fusion is source-agnostic |

---

## Execution Order

1. **Create `scripts/ingest_edgar.py`** — SEC API client, exhibit downloader, text extractor
2. **Create `src/precedent/classifier.py`** — Haiku-based clause classifier with CUAD taxonomy
3. **Run pilot ingestion** — ~20-50 EDGAR documents, classify, load to DB
4. **Verify retrieval** — `hybrid_search` returns EDGAR clauses mixed with CUAD
5. **Run cross-source `negotiation-check`** — verify skill pipeline works
6. **Extend eval harness** — add EDGAR queries, run recall@10
7. **Write tests** — connector, classifier, integration
8. **Document results** — `docs/eval-results/milestone-5.md`

---

## Handoff Note for Next Session

If this prompt is given to a fresh session:
- Read `CLAUDE.md` fully first
- Read `docs/ROADMAP.md` Milestone 5 section
- Read `docs/ARCHITECTURE_DECISIONS.md` for ADR-011 through 014 context
- Run `pytest tests/ -q` to confirm baseline (20/20)
- Start with EDGAR connector (`scripts/ingest_edgar.py`)

---

*This prompt is intended for a professional AI systems engineer. Execute with the same rigor as Milestones 1–4: measure, verify, document. No silent regressions.*