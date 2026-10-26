---
name: preflight
description: Use before merging any milestone branch, or whenever asked to verify the system is actually ready rather than "looks done". Runs an exhaustive, skeptical audit against CLAUDE.md's rules and the active milestone's Definition of Done, and refuses to report clean status until every check genuinely passes.
---

# preflight

Act as a principal systems architect doing a pre-merge audit — not the engineer who
just wrote the code. Your job is to find the reason this isn't actually done, not to
confirm it is. Report only what you actually ran and observed.

## 1. Repo & documentation alignment

- CLAUDE.md, docs/PRD.md, docs/ROADMAP.md, and docs/ARCHITECTURE_DECISIONS.md agree
  with each other and with what's actually in the code (no stale claims, no ADR
  missing for a decision that's clearly been made in the diff).
- `.env.example` still matches every field `Settings` in `src/precedent/config.py`
  actually reads — no env var used in code that isn't documented there, and vice versa.

## 2. Static checks

- `python -m py_compile src/precedent/*.py scripts/*.py eval/*.py tests/*.py`
- `pytest tests/ -q` — full pass, not just the tests touched by this change.

## 3. Database & schema integrity

- `db/schema.sql` applies cleanly to a fresh database.
- `EMBEDDING_DIM` in `.env`/`config.py` matches the actual dimension of whatever
  `EMBEDDING_MODEL` is currently set to, and matches `clauses.embedding`'s declared
  width in `schema.sql`.
- Required indexes exist: `idx_clauses_embedding`, `idx_clauses_tsv`,
  `idx_clauses_access_group`.

## 4. Architecture guarantees (the non-negotiables in CLAUDE.md)

- No skill-specific branching (`if skill.name == ...`) anywhere in `agent.py` —
  ADR-004.
- Every query in `retrieval.py` filters on `access_group` — no exceptions, including
  anything added since the last audit — ADR-009.
- The citation regex and retry logic in `agent.py` are unchanged from their last
  reviewed state, or any change is flagged explicitly rather than folded in quietly —
  ADR-005.
- `skill_runs` receives a row on both success and failure paths (check the `except`
  branch actually logs, don't just check the happy path) — governance requirement.

## 5. Real verification, not simulated

- Run `eval/run_eval.py` for real against the live database — report the actual
  recall@10 number, not the last known one.
- Pull the last 10 rows of `skill_runs` and report grounded-rate, average cost, and
  average latency from them — not from memory of what they were expected to be.
- If any of this can't actually be run (no DB up, no API key set), say so explicitly —
  do not report a check as passed because it was skipped.

## Output format

End with a verdict table, and nothing marked PASS unless it was actually executed
this session:

| Check | Result |
|---|---|
| Static checks (py_compile + pytest) | PASS / FAIL |
| Schema integrity | PASS / FAIL |
| Architecture guarantees (§4) | PASS / FAIL |
| Recall@10 (live) | e.g. 92% |
| Grounded-rate, last 10 runs | e.g. 9/10 |
| Avg cost / avg latency, last 10 runs | e.g. $0.03 / 6.2s |

Only say "ready to merge" if every row above is either a real PASS or a real number
inside the PRD §6 target range. A partial audit is a reported partial audit, not a
rounded-up clean bill of health.
