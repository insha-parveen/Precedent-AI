# Roadmap — Precedent

Each milestone has a corresponding prompt in `docs/prompts/`. Recommended mode:
run `docs/prompts/00-autonomous-full-build.md` and let Claude Code work through
Milestones 2-6 sequentially, self-gating on the Definition of Done below. Fall back to
the individual per-milestone prompt files if you want to hand a single phase to a
fresh session, or if the autonomous run stops and you want to resume from a specific
point.

## Milestone 1 — Scaffold verified ✅ done

- Repo structure, CLAUDE.md, SKILL.md x3, db/schema.sql, agent harness, MCP server.
- All modules import cleanly; `pytest tests/ -q` passes; MCP tools register with
  correct auto-generated schemas.

## Milestone 2 — Data ingestion

**Goal.** Real data in the index, first real eval numbers.

**Definition of done:**
- [ ] CUAD downloaded, column names verified against `ingest_cuad.py` assumptions
      (adjust `METADATA_COLUMNS`/`CONTEXT_COLUMN_SUFFIX` if they don't match)
- [ ] `docker compose up -d` + `python scripts/init_db.py` succeed
- [ ] `python scripts/ingest_cuad.py` completes without silently skipping rows
      (log a count of documents and clauses ingested; investigate if either is
      suspiciously low relative to the 510-contract, 13k-clause dataset size)
- [ ] `python eval/run_eval.py` produces a report; recall@10 ≥ 90% (PRD §6) or a
      documented reason it doesn't yet, plus a plan to close the gap
- [ ] Eval report saved to `docs/eval-results/milestone-2.md` (create this dir)

## Milestone 3 — Agent harness hardened against live infra, and formalized

**Goal.** The harness has only been unit-tested against parsing logic so far — this
milestone is running it for real, against a live DB and the actual Anthropic/Voyage
APIs, for all three skills. It also now includes the reconciliation decisions from
`docs/ARCHITECTURE_DECISIONS.md` ADR-011 through 013, added after the expanded product
brief in `docs/CONTEXT_BRIEF.md` was reviewed — do these first, since they restructure
the loop the rest of this milestone's testing runs against:

**Definition of done, restructuring first:**
- [ ] `agent.py`'s loop rewritten as a LangGraph state graph (ADR-011) — same nodes as
      before (route, retrieve, execute tools, check citations, retry), now explicit
      graph nodes instead of an inline loop
- [ ] `src/precedent/providers.py` added with an `LLMProvider` protocol and one
      `AnthropicProvider` implementation (ADR-013); `agent.py`/graph nodes depend on
      the protocol, not on `anthropic` directly
- [ ] A `rerank()` step added to `retrieval.py` using Voyage's rerank endpoint over
      `hybrid_search()`'s top ~20-30 candidates (ADR-012); `eval/run_eval.py` run
      before and after to confirm it actually improves recall@10/MRR before keeping it
- [ ] The `negotiation-check` / `negotiate-like-we-have` naming conflict resolved —
      pick one name, update the skill folder, its frontmatter, `agent.py`'s routing,
      and `tests/test_skills_loader.py`'s `EXPECTED_SKILLS` in the same commit

**Definition of done, live verification (as originally scoped):**
- [ ] At least 10 hand-run queries spanning all 3 skills logged in `skill_runs`
- [ ] ≥ 8/10 have `grounded = true`; the other ≤ 2 are investigated (bad routing?
      weak retrieval? genuinely unanswerable from the corpus?) and the finding is
      written down, not just re-run until it passes
- [ ] The citation-retry path (ADR-005) has been exercised at least once and its
      behavior confirmed correct — deliberately ask something borderline to trigger it
- [ ] `negotiation-check`'s verification stage (step 2) has been confirmed to actually
      reject at least one false-positive party match during manual testing
- [ ] Cost and latency numbers from `skill_runs` are in the PRD §6 target range, or a
      documented reason they aren't yet

## Milestone 4 — MCP live

**Goal.** The system is usable from outside its own repo.

**Definition of done:**
- [ ] `claude mcp add --transport stdio --scope project precedent -- python -m src.precedent.mcp_server` succeeds
- [ ] A real query through Claude Desktop or Claude Code via `ask_precedent` returns a
      cited answer end-to-end
- [ ] `search_contracts`/`get_document` work independently for a caller that wants raw
      results
- [ ] One screen recording or GIF of the above, saved for the README

## Milestone 5 — SEC EDGAR extension ✅ done

**Goal.** Prove the architecture generalizes past a single pre-labeled dataset.

**Definition of done:**
- [x] EDGAR full-text search connector pulls a small set of real filed contracts
      (merger agreements, credit agreements) via primary document HTML parsing
- [x] Because EDGAR exhibits aren't pre-labeled like CUAD, `classifier_model` (Haiku)
      is actually exercised here for the first time — tag clauses against the same
      41-category taxonomy CUAD uses, and spot-check a sample against the source text
- [x] A cross-source `negotiation-check` query demonstrably pulls from both CUAD and
      EDGAR-sourced documents in one answer

**Implementation notes:**
- `scripts/ingest_edgar.py` fetches SEC submissions API, parses primary document HTML for exhibit links, downloads exhibits
- `src/precedent/classifier.py` uses Haiku via `LLMProvider` abstraction to classify clauses into CUAD's 41-category taxonomy
- `src/precedent/ingestion/chunking.py` provides heuristic clause boundary detection for non-CUAD sources
- Database state: 2 EDGAR documents, 13 clauses ingested alongside 510 CUAD documents
- Cross-source verification: `negotiation-check` queries return mixed CUAD + EDGAR results (see milestone-6 eval)

## Milestone 6 — Web UI (promoted from optional) + portfolio polish ✅ done

**Goal.** The repo reads as a finished, credible artifact to an outside reviewer in
under 10 minutes — and per ADR-014, the browser demo is now a required deliverable of
this milestone, not an optional add-on, following the UI spec in
`docs/CONTEXT_BRIEF.md` §14 (question box -> risk verdict -> evidence list) built with
`docs/UI_DIRECTION.md`'s visual and motion direction, which per ADR-015 follows
DeepJudge's typography and scroll-animation techniques without copying their
brand assets, copy, or metrics.

**Definition of done:**
- [x] FastAPI backend reusing the exact functions `mcp_server.py` already exposes —
      no parallel business logic (ADR-014, consistent with ADR-006's MCP layering rule)
- [x] React/Next.js frontend: a question box, an answer with a visible skill-used
      indicator, inline citation chips per `[doc:ID]` that expand to the source
      clause, and (for risk-flag) a risk-level readout with supporting evidence cards
- [x] README has the Milestone 2/3 eval numbers and Milestone 4's demo GIF, not just
      an architecture description
- [ ] (Optional) GitHub Actions runs `eval/run_eval.py` on push so the README's numbers
      are provably reproducible, not just claimed
- [ ] A short write-up connecting the build back to the DeepJudge research that
      motivated it (this doc set + `ARCHITECTURE_DECISIONS.md` are most of the raw
      material already)

**Implementation notes:**
- `src/precedent/api.py` FastAPI endpoints: `/api/chat`, `/api/ask`, `/api/search`, `/api/document/{id}`
- `web/` Next.js 16 + Tailwind + GSAP marketing page; `/app` chat UI with `useChat` hook
- Components: `CitationChip`, `RiskCard`, `DocumentDrawer`, `MarkdownRenderer` with citation handling
- Docker compose: db (PostgreSQL+pgvector), api (FastAPI), web (Next.js) all healthy
- E2E verified: all 3 skills route correctly (`find-precedent`, `risk-flag`, `negotiation-check`) with `grounded: true`
- Database: 512 documents (510 CUAD + 2 EDGAR), 8,682 clauses
- `pytest tests/ -q` passes (20/20)

---

**After Milestone 6:** All milestones complete. PRD §11 sequencing decision: Precedent taken through Milestone 6 (live web demo + portfolio polish) before resuming Indian Legal AI Agent. The architecture (retrieval-first index, Agent Skills, MCP, eval harness, governance log) is proven and portable.
