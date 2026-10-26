# Architecture Decision Records — Precedent

Lightweight ADR format: Context / Decision / Consequences / Alternatives considered.
New decisions get appended, never rewritten in place — if a decision changes, add a
new ADR that supersedes the old one and say so.

---

### ADR-001: Retrieval-first, not LLM-first

**Context.** The alternative is letting Claude answer contract questions from general
training knowledge, optionally "enriched" by a token search. That's the architecture
of most portfolio RAG projects, and it's exactly the failure mode DeepJudge positions
against.

**Decision.** No answer path exists that doesn't go through `retrieval.py`. The system
prompt in `agent.py` explicitly forbids answering from parametric knowledge, and that
prohibition is checked in code (see ADR-005), not just requested.

**Consequences.** Every new capability has to be expressed as "what would we need to
retrieve to answer this," which is a harder design constraint but the entire point of
the project.

---

### ADR-002: Hybrid search via Postgres + pgvector, not a dedicated vector DB

**Context.** Qdrant/Pinecone/Weaviate are all viable and arguably more "expected."

**Decision.** One Postgres database holds vectors (`pgvector`), full-text search
(`tsvector`), and relational metadata (parties, doc_type, access_group) together.

**Consequences.** Reciprocal rank fusion across vector + keyword search is a single
SQL query instead of a merge across two systems. Filtering by access_group is a WHERE
clause, not a second permissions layer bolted onto an external vector store. Trade-off:
won't scale past a few million vectors as gracefully as a dedicated vector DB — not a
real constraint at this corpus size (thousands of clauses).

**Alternatives considered.** Qdrant (rejected: adds a second system to operate for no
benefit at this scale, and DeepJudge's own "holistic search across clients, matters,
documents, people" framing is inherently relational, which Postgres expresses more
directly than a pure vector store).

---

### ADR-003: Clause-aware chunking from CUAD's own labeled offsets

**Context.** The default RAG chunking strategy is a fixed-size sliding window, which
routinely splits a clause across chunk boundaries.

**Decision.** For CUAD, each chunk is exactly one expert-labeled clause span from the
dataset itself — no chunking heuristic invented.

**Consequences.** Free, defensible eval ground truth (see ADR-010). Doesn't generalize
to sources without pre-existing labels — SEC EDGAR ingestion (Milestone 5) will need
an actual chunking + classification strategy, which is exactly where `classifier_model`
(Haiku) earns its place in the config, unused until then.

---

### ADR-004: Skills are data, not code

**Context.** Pressure to hardcode skill-specific logic into `agent.py` will show up
the moment a skill needs "just one more special case."

**Decision.** `agent.py` only loads, routes to, and executes skills generically. All
behavioral differences between `find-precedent`, `negotiation-check`, and `risk-flag`
live in their SKILL.md instructions.

**Consequences.** Adding a fourth skill is "write a SKILL.md," not "modify the agent
loop." This is also the most direct, literal clone of DeepJudge's actual Agent Skills
pitch — worth protecting even under time pressure. If you ever write
`if skill.name == "risk-flag":` in `agent.py`, that's the signal this ADR is being
violated.

---

### ADR-005: Citation-or-refuse enforced in code

**Context.** "Always cite your sources" in a system prompt is routinely ignored under
model sampling variance, especially in longer tool-use loops.

**Decision.** `agent.py` regexes the final answer for `[doc:ID]` markers. If sources
were retrieved but none are cited, one bounded retry runs with an explicit correction
instruction; if that still fails, the answer ships with a visible
`[unverified — could not confirm citations...]` prefix and `grounded=false` in the log.

**Consequences.** The system can still fail to ground an answer, but it can never fail
*silently* — every ungrounded answer is flagged to both the user and the governance
log. This is the single most important guarantee in the project; treat any change to
`CITATION_PATTERN` or the retry logic as requiring the same scrutiny as a database
migration.

---

### ADR-006: MCP exposes the full harness, not just raw search

**Context.** The simpler MCP design exposes `search_contracts`/`get_document` only and
lets the calling client's own model reason over raw hits.

**Decision.** `ask_precedent` (wrapping the entire route→retrieve→verify→cite harness)
is the primary MCP tool; raw search/get_document are secondary, for callers that want
to reason over sources themselves.

**Consequences.** Grounding and skill-routing guarantees hold regardless of which
external model calls the server — this matches DeepJudge's own MCP demo pattern
("Claude gets back exactly what it needs," already synthesized) rather than punting
synthesis quality to whatever client happens to connect.

---

### ADR-007: MCP SDK v2 (`MCPServer`), confirmed against the installed package

**Context.** Most public tutorials and even prior drafts of this project's own code
referenced `mcp.server.fastmcp.FastMCP` — that's the v1 API. `mcp>=2.0` renamed it to
`mcp.server.mcpserver.MCPServer` with a decorator-based `@server.tool()` API.

**Decision.** Build against v2, verified by actually installing `mcp` and inspecting
it (the package's own `ModuleNotFoundError` message names the migration guide) rather
than trusting training-data memory or a tutorial's publish date.

**Consequences.** Anyone (including Claude Code) reaching for `FastMCP` syntax from
habit will hit an immediate, clear error — treat that error as "check the installed
version," not "revert to the old API by pinning `mcp<2`."

---

### ADR-008: Domain-specific embeddings (`voyage-law-2`) as the default, not a fixed choice

**Context.** A general-purpose embedding model (`voyage-4`) is cheaper and has a
larger free-token allowance.

**Decision.** Default to `voyage-law-2` for now, but treat this as an empirical
question the eval harness should actually answer once real data is in, not a permanent
commitment: re-run `eval/run_eval.py` against both models before locking it in.

**Consequences.** `EMBEDDING_MODEL` and `EMBEDDING_DIM` are both env-driven for exactly
this reason — swapping requires re-ingestion, so decide with eval numbers, not
intuition, and do it once.

---

### ADR-009: Permission simulation is enforced at the query layer even though all data is public

**Context.** Nothing in this corpus is actually confidential, so it would be easy to
skip access control entirely.

**Decision.** Every row carries `access_group`; every retrieval query filters on it.

**Consequences.** The project demonstrates the *pattern* DeepJudge's real permission
architecture requires (permissions synced from source systems, enforced on every
query) even though there's nothing to actually protect here — this is a deliberate
signal for anyone technical reviewing the repo, not incidental complexity.

---

### ADR-010: Eval-gated development

**Context.** It's easy to "eyeball" a retrieval change as an improvement.

**Decision.** No change to chunking, embeddings, or fusion logic ships without a fresh
`eval/run_eval.py` run; a regression needs a stated reason in the commit message.

**Consequences.** This is the project's own agent-operations discipline applied to its
development process, not just its runtime — see `BEST_PRACTICES.md`.

---

## Reconciliation with the expanded product brief (docs/CONTEXT_BRIEF.md)

A more detailed project brief was supplied after Milestone 1 shipped (see
`docs/CONTEXT_BRIEF.md` for the full, unedited text). It overlaps heavily with
ADR-001 through ADR-010 but introduces four real conflicts with what's already built
and verified. ADRs 011-014 resolve them. None of Milestones 1-2's shipped work is
invalidated by these — they land at Milestone 3, the point already scheduled for
hardening the agent loop against live infrastructure.

### ADR-011: Formalize the agent loop as a LangGraph state machine, starting at Milestone 3

**Context.** `agent.py`'s current tool-use loop (a bounded `for` loop calling the
Anthropic API directly) works and is already verified, but the brief calls for
explicit states, branching, and retry loops — genuinely useful for a verification step
that's more than "did the regex find a citation," and a well-recognized orchestration
pattern in the target job market for this portfolio.

**Decision.** Don't touch the working Milestone 1 harness now. Rewrite it as a
LangGraph graph as the *first task* of Milestone 3 (agent hardening), with explicit
nodes matching the brief's §8 outline: understand request -> select skill -> retrieve
-> rerank (ADR-012) -> extract -> verify -> synthesize -> citation validation
(ADR-005's check, now a graph node instead of inline code) -> respond.

**Consequences.** Milestone 2 (ingestion) doesn't touch `agent.py` at all, so there's
no wasted work from sequencing it this way. `route_skill()`'s logic and the
citation-check regex both survive as-is, moved into graph nodes rather than rewritten
from scratch — this is a restructuring, not a rebuild. **The citation-check node and
the retry-loop node still require human review per CLAUDE.md rule 2, same as today.**

**Alternatives considered.** Rewriting immediately (rejected: Milestone 2 doesn't need
it and CLAUDE.md rule 3/BEST_PRACTICES already warn against unverified rewrites of
working guarantees). Never adopting LangGraph (rejected: the brief's reasoning about
explicit verification loops and portfolio signal value is sound).

### ADR-012: Add an explicit reranking stage using Voyage's rerank model

**Context.** Current retrieval does reciprocal rank fusion of vector + keyword search
in one SQL query — good hybrid retrieval, but no dedicated reranking pass over the
fused candidates, which the brief correctly calls out as a distinct pipeline stage.

**Decision.** Add a reranking step in `retrieval.py` (a new `rerank()` function) using
Voyage's rerank endpoint over `hybrid_search()`'s top ~20-30 candidates before
returning the final top-k. Voyage, not a second vendor (Cohere, etc.) — we're already
a Voyage customer for embeddings, and adding a second embedding/reranking vendor for
one extra pipeline stage fails the brief's own §15 rule ("every major dependency must
have a reason").

**Consequences.** `eval/run_eval.py` needs a before/after comparison once this lands —
reranking that doesn't measurably improve recall@10 or MRR isn't worth the added
latency and cost, and the eval harness (ADR-010) is exactly what answers that
empirically rather than by assumption.

### ADR-013: A thin model-provider abstraction, Anthropic as the only implementation for now

**Context.** `agent.py` calls `anthropic.Anthropic` directly throughout. The brief
wants provider-agnosticism so an organization could substitute OpenAI or a
self-hosted model.

**Decision.** Introduce `src/precedent/providers.py`: a small `LLMProvider` protocol
(methods: something like `complete(messages, tools, system) -> ProviderResponse`) with
one concrete `AnthropicProvider`. Do not build an OpenAI or local-model provider now —
the brief's own §16 (cost constraint) and §19 (don't over-engineer) argue against
building unused code paths. The abstraction is the deliverable; a second
implementation is not needed to prove it's real, and can be added later as evidence
the seam works.

**Consequences.** `agent.py` and the LangGraph nodes (ADR-011) depend on the
`LLMProvider` protocol, not on `anthropic` directly. `classifier_model` and
`agent_model` in `config.py` already being plain strings makes this a low-cost
retrofit, not a rewrite of the config layer.

### ADR-014: Web UI promoted from optional to a scoped milestone; visual identity decision (docs/UI_DIRECTION.md) unchanged

**Context.** The brief's §14 describes a real browser product experience (a question
box, a risk verdict, an evidence list) as core to the "public portfolio demo" mode,
not an afterthought. `docs/ROADMAP.md` currently lists this as "(Optional) minimal
FastAPI + web chat" under Milestone 6.

**Decision.** Keep the sequencing already decided in `docs/UI_DIRECTION.md` — original
visual identity, not a DeepJudge clone, built after the backend is demoable — but
promote it from optional to a required Milestone 6 deliverable, and take the brief's
§14 mockup (question box -> risk verdict -> evidence list with per-document citations)
as the actual UI spec rather than inventing a different one. `docs/UI_DIRECTION.md`'s
reasoning already lines up with the brief's own §18 ("do not build a clone of
DeepJudge") — no conflict there, just more detail now than existed before.

**Consequences.** FastAPI serves the same functions `mcp_server.py` already exposes
(no parallel business logic — consistent with the brief's own MCP layering rule in
§12) behind a small React/Next.js frontend. `docs/ROADMAP.md`'s Milestone 6 section
gets amended accordingly, not rewritten.

### Naming conflict, flagged not resolved: `negotiation-check` vs. the brief's `negotiate-like-we-have`

Same skill, two names. Left unresolved deliberately rather than renamed here —
renaming touches the skill's folder, its `name:` frontmatter, `agent.py`'s routing,
and `tests/test_skills_loader.py`'s `EXPECTED_SKILLS` set simultaneously, which is
exactly the kind of multi-file mechanical change that belongs inside a real work
session (Milestone 3, alongside ADR-011's rewrite) rather than a docs-only pass.
Whoever does that session picks one name and updates every reference in the same
commit.

---

## ADR-015: Marketing site adopts deepjudge.ai's visual and motion language (not its identity)

**Status:** Accepted 2026-10-05. Supersedes the visual-identity half of ADR-008 and
rewrites `docs/UI_DIRECTION.md`.

**Context.** `docs/UI_DIRECTION.md` originally decided against replicating
deepjudge.ai's visual design, animations, or brand identity, on three grounds: that
we only had fetched page text rather than their source, that cloning a live
company's specific visual identity undercuts this project's "demonstrates the
builder's own judgment" framing, and that a marketing site was out of scope for
Milestone 6.

The owner reviewed that decision and reversed it, asking for the marketing site to
follow deepjudge.ai's typography treatment and scroll-animation approach as closely
as the technology allows, aligned with Precedent's own product. Scope is no longer
an objection: the site is being built now. The other two grounds needed a real
answer rather than a dismissal, which is what this ADR records.

**Decision.** The marketing site adopts deepjudge.ai's *technique set* — warm
neutral palette, grotesque/mono/serif type roles, and a GSAP ScrollTrigger motion
language (split-text staggered headline reveals, staggered section reveals,
count-up statistics, infinite marquee, background parallax) — reimplemented in
`web/`.

Three lines are drawn firmly:

1. **No brand assets.** No logo, wordmark, illustration, photograph, customer logo,
   or Lottie animation is taken. All iconography is `lucide-react`.
2. **No copy and no social proof.** All text is written for Precedent. No client
   testimonials, partner names, or firm logos are invented to imitate their
   credibility sections.
3. **No borrowed metrics.** The deepjudge.ai figures (+65h saved per user per year,
   +85% adoption, 4x ROI) are theirs and are never used. Every statistic on the page
   comes from this repository's own corpus or its own `eval/run_eval.py` run.

Two substitutions are accepted and documented rather than hidden:

- **Fonts.** Suisse Intl is commercially licensed. Open equivalents with a similar
  role are used instead: Archivo, IBM Plex Mono, and Merriweather.
- **Runtime.** Webflow's `webflow.js` is not loaded. It is proprietary, coupled to
  Webflow's generated markup, and has no place in a Next.js app. The equivalent
  effects are written directly against GSAP.

**Consequences.** `docs/UI_DIRECTION.md` is rewritten around "match the craft, never
the identity." GSAP becomes a frontend dependency. The motion lives in a single
`gsap.context()` in `web/src/lib/animations.ts` and is reverted on unmount, so no
scroll listener or ScrollTrigger survives navigation. The non-negotiable interaction
patterns from the previous UI decision survive this reversal unchanged — inline
citation chips, a visible skill indicator, chat-first interaction — because they
express ADR-005's guarantee rather than a style preference. The chat UI was moved
to `/app` and kept outside the GSAP layer so that message rendering never depends
on an animation timeline completing; under `prefers-reduced-motion: reduce` the
marketing page renders in its final state with no motion at all.
