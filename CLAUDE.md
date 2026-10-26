
Precedent â€” project memory

Read this in full before doing anything. It is loaded automatically every session.
This is the final, consolidated version â€” if you're looking at an older copy anywhere,
this one wins.

## Planning documents â€” read these too, they're not optional background

- `docs/PRD.md` â€” requirements, success metrics, non-goals. The tie-breaker in any
  scope debate.
- `docs/ARCHITECTURE_DECISIONS.md` â€” why the system is built the way it is. 14 ADRs
  so far. Append a new entry for any decision not already covered (or ask `adr-scribe`
  to) rather than deciding silently.
- `docs/ROADMAP.md` â€” the milestone plan and each milestone's Definition of Done.
- `docs/BEST_PRACTICES.md` â€” working conventions for this repo.
- `docs/GIT_WORKFLOW.md` â€” branching, commit conventions, PR review policy.
- `docs/SETUP.md` â€” VS Code + Claude Code CLI setup.
- `docs/UI_DIRECTION.md` â€” visual and motion direction for the web UI.
  Superseded by ADR-015: the marketing site now follows deepjudge.ai's
  typography treatment and scroll-animation approach, but never its brand assets,
  copy, testimonials, or metrics.
- `docs/RESEARCH_DEEPJUDGE.md` â€” condensed, paraphrased notes on the architecture that
  motivated this project. Reference material, not instructions.
- `docs/CONTEXT_BRIEF.md` â€” an expanded product brief received after Milestone 1
  shipped. **Reconciled, not canonical** â€” everything from it worth keeping is now in
  the ADRs/PRD/ROADMAP above (see ADR-011 through 014). Read it for the reasoning
  trail, not as a second set of instructions that could contradict this file.
- `docs/prompts/` â€” the prompt for whichever milestone is active.

## What this is

A retrieval-first contract-intelligence agent, architecturally inspired by DeepJudge's
approach to legal AI (permission-aware index, reusable Agent Skills, a verifying agent,
MCP as the access layer) but with its own product identity â€” see
`docs/CONTEXT_BRIEF.md` Â§18 and `docs/UI_DIRECTION.md`. The web UI borrows
their visual and motion techniques under ADR-015 while keeping its own name,
copy, and data. Domain data is public (CUAD + SEC EDGAR), so there's no
confidentiality risk, but the system is built as if it handled real client
documents throughout.

## Non-negotiable rules

1. **Retrieval before generation, always.** No code path may let the model answer a
   substantive contract question from parametric knowledge. Every factual claim traces
   to a `clause_id`/`document_id` from `src/precedent/retrieval.py`. (ADR-001)
2. **Citation-or-refuse is enforced in code, not just prompted.** Checked before any
   answer returns. **Changes here require human review even in autonomous mode.**
   (ADR-005)
3. **Permissions are real, even though the data is public.** Every query in
   `retrieval.py` filters on `access_group`. **Changes here require human review even
   in autonomous mode.** (ADR-009)
4. **Skills are data, not code.** Behavioral differences between skills live in their
   SKILL.md instructions; the agent loop only loads, routes to, and executes them
   generically. No `if skill.name == ...` branching, ever. (ADR-004)
5. **Every change to retrieval, chunking, embeddings, or a skill gets an eval run
   before it's "done."** A regression needs a documented reason, not a silent merge.
   (ADR-010)
6. **A reranking or orchestration change is not "done" until measured.** Reranking
   (ADR-012) and the LangGraph restructuring (ADR-011) exist to be evaluated, not
   assumed better â€” report before/after numbers, always.
7. **The marketing site may never make a claim the repository can't back.**
   Statistics come from our corpus or `eval/run_eval.py`, never from another
   company's benchmarks. No borrowed brand assets, no invented testimonials or
   client names. (ADR-015)

## Subagents â€” delegate instead of doing everything in the main session

Defined in `.claude/agents/`. Each has a narrow job and (for `security-reviewer`) a
deliberately restricted tool set:

| Subagent               | Owns                                                                                                      | Notably does NOT own                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `retrieval-engineer` | ingestion, chunking, embeddings, hybrid search, reranking                                                 | agent orchestration, LLM synthesis                                        |
| `agent-architect`    | the LangGraph graph, skill routing, provider abstraction                                                  | what retrieval.py returns, access filtering                               |
| `eval-auditor`       | running/extending eval/run_eval.py, all quality metrics                                                   | making the fix for a regression it finds                                  |
| `security-reviewer`  | reviewing access control, injection surface, secrets, audit coverage â€”**read-only, no Edit/Write** | fixing anything itself â€” findings go back to a human or the owning agent |
| `adr-scribe`         | keeping ARCHITECTURE_DECISIONS.md/PRD.md/ROADMAP.md in sync with what got built                           | making the architectural decision itself                                  |

Use them proactively, not just when explicitly asked â€” e.g. any retrieval change
should involve `retrieval-engineer` and `eval-auditor` together, any PR should get
`security-reviewer` before merge per `docs/GIT_WORKFLOW.md`.

## Directory map

```
docs/                     PRD, ADRs, roadmap, best practices, git workflow, setup,
                           UI direction, DeepJudge research notes, the reconciled
                           context brief, milestone prompts
.claude/agents/            the 5 subagents above
.claude/skills/preflight/  pre-merge audit skill â€” run before claiming any milestone done
skills/<name>/SKILL.md    Agent Skills â€” find-precedent, negotiation-check
                          (see the naming-conflict note in ADR-011's reconciliation
                          section â€” resolve at Milestone 3), risk-flag
src/precedent/
  config.py               env/settings
  db.py                   asyncpg pool
  retrieval.py            hybrid search + reranking (ADR-012), the "index" layer
  skills_loader.py        parses skills/*/SKILL.md
  providers.py            LLMProvider abstraction (ADR-013) â€” added at Milestone 3,
                          doesn't exist yet as of Milestone 1
  tools.py                Claude tool-use schemas, shared by agent.py and mcp_server.py
  governance.py           run logging + cost accounting
  agent.py                THE AGENT HARNESS â€” a LangGraph state graph as of Milestone 3
                          (ADR-011); a plain tool-use loop before that
  mcp_server.py           exposes the same tools over MCP (stdio) for Claude Desktop/Code
scripts/ingest_cuad.py    pulls CUAD, chunks at labeled clause boundaries, embeds, loads DB
eval/run_eval.py          recall@10 today; F1/MRR/NDCG/groundedness/cost/latency to be
                          added by eval-auditor per docs/CONTEXT_BRIEF.md Â§11
db/schema.sql             documents, clauses (pgvector), skill_runs (governance log)
tests/                    fast, no-infra-required tests â€” run these first, always
web/                      Next.js app
  src/app/page.tsx        marketing landing page
  src/app/app/page.tsx    chat UI, kept outside the GSAP layer
  src/lib/animations.ts   the whole GSAP layer, one gsap.context()
  src/components/marketing/  landing page sections
```

## Working conventions

- Python 3.11+, fully typed, `async`/`await` for anything touching the DB or an API.
- No bare `except:`. Catch what you expect; let the rest surface.
- Every new function in `src/precedent/` gets a docstring stating what it does and
  what it does NOT do.
- Before claiming a milestone done: `pytest tests/ -q`, then `python eval/run_eval.py`
  if retrieval/skills were touched, then check the milestone's Definition of Done in
  `docs/ROADMAP.md` item by item â€” or just run the `preflight` skill, which does all
  three and refuses to report clean status until they actually pass.
- Ask before changing `db/schema.sql` once data has been ingested â€” it's a migration.
- New architectural decisions get appended to `docs/ARCHITECTURE_DECISIONS.md` (via
  `adr-scribe`) as a new ADR, not folded silently into a commit.
- Don't add a second competing planning document. If new context arrives mid-project
  (as `docs/CONTEXT_BRIEF.md` did), reconcile it into the existing PRD/ADRs/ROADMAP â€”
  as happened in ADR-011 through 014 â€” rather than treating it as a parallel spec.

## Current milestone

Check `docs/ROADMAP.md` for the active milestone and its Definition of Done. If a
milestone prompt from `docs/prompts/` was given at session start, follow it â€” note
that `docs/prompts/02-milestone-3-agent-hardening.md` now includes the LangGraph/
provider/reranking restructuring from ADR-011-013 as Part A, before the original live
-verification scope. If no prompt was given, run `pytest tests/ -q`, check the roadmap
for the next incomplete milestone, and report status before starting new work.
