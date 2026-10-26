# Prompt 02 — Milestone 3: Agent harness hardening (standalone)

```
Read CLAUDE.md, docs/ARCHITECTURE_DECISIONS.md (ADR-005, ADR-009, and ADR-011 through
014), and docs/ROADMAP.md's Milestone 3 section before starting. Milestone 2 (data
ingested, eval passing) should already be done — confirm that before proceeding.

Delegate to the project's subagents rather than doing everything in the main session:
agent-architect for the LangGraph rewrite and provider abstraction, retrieval-engineer
for the reranking stage, eval-auditor for before/after numbers, adr-scribe to log any
new decisions made along the way.

Part A — restructuring (do this first, per ADR-011/012/013):
1. Have agent-architect rewrite the tool-use loop in src/precedent/agent.py as a
   LangGraph state graph. Preserve route_skill()'s behavior and the citation
   regex/retry semantics exactly — this is a restructuring, not new behavior.
2. Have agent-architect add src/precedent/providers.py (an LLMProvider protocol, one
   AnthropicProvider implementation) and wire agent.py/the graph nodes to depend on it.
3. Have retrieval-engineer add a rerank() step to retrieval.py using Voyage's rerank
   endpoint, and have eval-auditor run eval/run_eval.py before and after to confirm it
   actually helps before keeping it.
4. Resolve the negotiation-check / negotiate-like-we-have naming conflict — pick one
   name, update the skill folder, its frontmatter, agent.py's routing, and
   tests/test_skills_loader.py's EXPECTED_SKILLS in the same commit.

Part B — live verification (as originally scoped):
Goal: prove the agent harness works end-to-end against live infrastructure, not just
unit tests against parsing logic.

1. Run at least 10 real queries through src/precedent/agent.py's run_query(), covering
   all three skills (find-precedent, negotiation-check, risk-flag). Use real questions
   about the ingested CUAD data, not synthetic placeholders.
2. For each, record: which skill was routed to, whether grounded=true, cost, latency —
   pull these from skill_runs rather than just eyeballing the printed answer.
3. Deliberately try to trigger the citation-retry path (ADR-005) with a query likely to
   produce an ungrounded first pass, and confirm the retry behaves as designed.
4. For negotiation-check specifically, find or construct a case where a party name
   appears in the corpus without actually being a contracting party on the relevant
   side, and confirm step 2 (verification) correctly excludes it rather than treating
   the text match as evidence.
5. Compare the resulting cost/latency numbers against PRD §6 targets and note any gap.
6. Write findings to docs/eval-results/milestone-3.md, including the 2 queries (if any)
   that didn't come back grounded and what you determined was the cause.

If any of this reveals agent.py's citation logic or retrieval.py's access_group
filtering needs a change, flag it for review rather than committing directly — see
BEST_PRACTICES.md.
```
