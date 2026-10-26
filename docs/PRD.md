# PRD — Precedent

**A retrieval-first contract-intelligence agent, architecturally modeled on DeepJudge**

Status: active | Owner: Insha | Last updated: this planning pass

> **Portfolio context.** This is written with the rigor of a real product PRD on
> purpose — that rigor is itself part of what the finished project demonstrates. The
> "customer" is a hypothetical law-firm ops/knowledge-management buyer; the actual
> constraints (public data, solo builder, demo-oriented) are called out explicitly
> below rather than hidden.

## 1. One-liner

Given a natural-language question about a corpus of commercial contracts, return a
grounded, cited answer — never a guess — by routing through the right specialized
skill, retrieving from a permission-aware hybrid index, and verifying the answer
against what was actually retrieved before it's shown to anyone.

## 2. Problem statement

Mirrors the problem DeepJudge is built to solve, restated for this project's scope:

- A firm's most useful knowledge — how a clause type has been negotiated, what a
  contract type typically contains, whether a counterparty has ever agreed to a given
  position — is locked inside individual documents with no systematic way to query
  across them.
- General-purpose LLM chat doesn't fix this: it either refuses (no access to the
  corpus) or hallucinates a plausible-sounding answer with no basis in any real
  document — the single worst failure mode for anything touching contract language.
- Manual "deal points" tracking doesn't scale: it depends on someone deciding in
  advance which clauses were worth tagging, so it's always incomplete.

## 3. Goals

**Product goals**
- Answer precedent-lookup, negotiation-history, and risk-flagging questions over the
  corpus with an enforced citation-or-refuse guarantee (see NFR-1).
- Make the system usable from Claude Desktop, Claude Code, or a browser — not locked
  to one interface — via MCP.
- Make retrieval quality a *measured* property of the system, not a claimed one.

**Portfolio goals**
- Demonstrate a faithful, working analog of a real legal-AI company's architecture
  (retrieval-first index, Agent Skills, MCP, agent-operations logging) rather than a
  generic RAG chatbot.
- Produce artifacts a reviewer can actually exercise live (MCP-connected Claude
  Desktop session), not just read about.

## 4. Non-goals (v1)

- No contract *drafting* or redlining — this is a lookup/analysis system, not an
  authoring tool.
- No real client/firm data, ever. Public corpora only (CUAD, later SEC EDGAR).
- No multi-tenant auth/user management UI — access_group is modeled at the schema
  level to demonstrate the *pattern*, not built out as a full identity system.
- No fine-tuning. Retrieval quality and skill design carry the system, not a
  custom-trained model — this is also the more honest comparison to how DeepJudge
  itself is positioned (retrieval-first, model-agnostic).
- Not legal advice, anywhere, in any output. Every skill's output format says so
  where relevant (see `risk-flag`'s disclaimer requirement).

## 5. Users / personas

1. **Portfolio reviewer** (recruiter, hiring manager, legal-AI company engineer) —
   primary audience. Wants to see working software and real numbers in under 10
   minutes, ideally live.
2. **Hypothetical end user** (in-house counsel, associate, contracts manager) — used
   to keep feature design honest. If a feature wouldn't help this persona do their
   actual job, it doesn't belong in v1 regardless of how impressive it looks.

## 6. Success metrics

| Metric | Target | Measured by |
|---|---|---|
| Recall@10 on seed eval queries | ≥ 90% | `eval/run_eval.py` |
| Citation-pass-rate (grounded=true where a search occurred) | ≥ 95% | `skill_runs` table |
| P50 query latency | ≤ 8s | `skill_runs.latency_ms` |
| P95 query latency | ≤ 20s | `skill_runs.latency_ms` |
| Avg. cost per query | ≤ $0.05 | `skill_runs.cost_usd` |
| Ungrounded factual claims in the 3 skill demo transcripts used publicly | 0 | manual review before publishing |

These are working targets, not vanity numbers — if Milestone 3's first eval run comes
back at 65% recall, that's useful signal to fix chunking or the fusion weighting, not
a reason to quietly lower the bar in this document.

## 7. Functional requirements

| ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-1 | Hybrid search over clause-level chunks | Returns ranked results combining vector + keyword match, filtered by access_group |
| FR-2 | `find-precedent` skill | Given a document/clause description, returns cited prior matches or an honest "not found" |
| FR-3 | `negotiation-check` skill | Given a party + clause type, runs locate→verify→extract→synthesize and returns a yes/no/mixed verdict with citations |
| FR-4 | `risk-flag` skill | Given a target document, flags missing/unusual clauses vs. the corpus baseline for that doc_type, with citations and a non-legal-advice disclaimer |
| FR-5 | MCP server | Exposes `ask_precedent`, `search_contracts`, `get_document`; connects to Claude Desktop/Code via stdio |
| FR-6 | Governance log | Every agent run writes one row to `skill_runs` with cost, latency, grounding status |
| FR-7 | Eval harness | Recall@k report runnable on demand, reproducible, checked into the repo |

## 8. Non-functional requirements

- **NFR-1 (grounding):** no code path may return a substantive factual claim about
  contract content without a `[doc:ID]` citation traceable to a tool result in the
  same run. Enforced in `agent.py`, not only in prompts.
- **NFR-2 (permissions):** every retrieval query filters on `access_group`, even
  though the demo corpus is entirely public — the pattern is the point.
- **NFR-3 (cost discipline):** ingestion/classification prefers the cheapest model
  that meets the quality bar (Haiku over Sonnet, Batch API for bulk one-time jobs).
- **NFR-4 (observability):** any query's full lifecycle (skill routed to, tool calls
  made, sources cited, cost, latency) must be reconstructable from `skill_runs` alone.
- **NFR-5 (licensing):** only CC-BY-4.0 or public-record data sources. No exceptions.

## 9. Milestones

See `ROADMAP.md` for full detail and definitions of done. Summary: (1) scaffold —
done; (2) CUAD ingestion + first eval numbers; (3) agent harness hardened against a
live DB/API; (4) MCP connected, live demo works; (5) SEC EDGAR extension (stretch);
(6) portfolio polish (README numbers, optional CI, optional write-up).

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| CUAD CSV column names don't match assumptions | `ingest_cuad.py` fails loudly with the exact inspection command to run first |
| MCP SDK breaking changes (already hit once: FastMCP → MCPServer in v2) | Pin `mcp` in `requirements.txt`; re-verify against the installed package, not memory/tutorials, before any MCP code change |
| Embedding model swap silently breaks retrieval (dimension mismatch) | `EMBEDDING_DIM` lives in one place (`.env`/`config.py`) and `schema.sql` calls out that it must match |
| Scope creep toward "rebuild DeepJudge" instead of "clone its architecture at demo scale" | Non-goals section above is the tie-breaker in any prioritization debate |
| Two half-finished portfolio projects dilute the narrative | See §11 — sequencing decision |

## 10.5. Reconciliation note

An expanded product brief (`docs/CONTEXT_BRIEF.md`) arrived after Milestone 1 shipped,
requesting LangGraph orchestration, an explicit reranking stage, a model-provider
abstraction, and a promoted (required, not optional) browser UI. All four are adopted;
none change this PRD's non-goals (§4) or success metrics (§6) — they change *how*
FR-2/FR-3/FR-4 and NFR-1 get implemented at Milestone 3, and elevate what was already
a nice-to-have at Milestone 6. Full reasoning in `docs/ARCHITECTURE_DECISIONS.md`
ADR-011 through ADR-014.

## 11. Open question, resolved: how does this relate to the Indian Legal AI Agent project?

**Decision: sequence, don't parallelize.** Take Precedent through Milestone 4 (live
MCP demo working) before resuming the Indian Legal AI Agent's regulatory research.
Reasoning: a working, measured, demoable system is a stronger portfolio asset than
two half-built ones, the Bar Council of India research doesn't go stale while paused,
and the architecture built here (retrieval-first index, Agent Skills, MCP, eval
harness, governance log) is directly portable — the second project should move faster
in its first month than this one did, precisely because the pattern is now proven.
Revisit this call after Milestone 4, not before.
