# Best practices — Precedent

## Working with Claude Code on this repo

1. **CLAUDE.md is the contract, not a suggestion.** If a session seems to have
   forgotten a rule from it (e.g. starts branching skill-specific logic into
   `agent.py`), the fix is "re-read CLAUDE.md," not re-explaining the rule from
   scratch in the chat.
2. **Never let `/init` overwrite the hand-written CLAUDE.md.** If you ever run it in
   this repo, diff the result — it's meant for bootstrapping a fresh project's memory,
   not regenerating one that already encodes specific architectural decisions.
3. **Give every milestone a verifiable check before calling it done** — `pytest`,
   `eval/run_eval.py`, or a specific manual query to run and inspect in `skill_runs`.
   "It looks right" is not a milestone gate anywhere in this project.
4. **Two files get human diff review even in autonomous mode:** `agent.py`'s citation
   check/retry logic, and `retrieval.py`'s access_group filtering. These are the two
   places where a quiet regression breaks a stated guarantee (ADR-005, ADR-009) rather
   than just a feature. Everything else can move fast; these two get a second look.
5. **Commit after each milestone, not each file.** Reference the relevant ADR number
   in the commit message when a commit implements or touches one — it turns the git
   log into a second, cross-checkable copy of the decision record.
6. **When Claude Code proposes an architecture change** (different chunking strategy,
   different fusion approach, a new table), it should land as a new ADR appended to
   `ARCHITECTURE_DECISIONS.md`, not a silent code change. Ask for the ADR in the same
   turn as the change if it doesn't offer one.
7. **Update PRD.md/ROADMAP.md when a decision changes** — e.g. if Milestone 2's eval
   numbers come back low and the fix is switching embedding models (ADR-008 already
   anticipates this), update the ADR status and PRD §6 if the target itself needs to
   move, rather than letting the documents drift out of sync with what actually
   shipped.

## Engineering practices specific to this kind of system

- **Pin embedding model and dimension together, and change them together.**
  `EMBEDDING_MODEL` and `EMBEDDING_DIM` live in one place (`config.py`/`.env`) on
  purpose — a silent mismatch between the model actually called and the column's
  vector width is a runtime error you want at ingestion, not a confusing failure
  three layers up.
- **Ingestion fails loudly, never silently skips.** `ingest_cuad.py` is written to
  raise on a column-name mismatch rather than proceed with a partially-wrong parse —
  keep that posture for the EDGAR ingestion path too (Milestone 5).
- **Batch, don't stream, for one-time bulk jobs.** Any bulk classification pass over
  the whole corpus (Milestone 5's EDGAR tagging) is a Batch API candidate — half the
  cost, and it's not latency-sensitive work.
- **Log every run, including failures.** `skill_runs` gets a row even when `agent.py`
  hits an exception (see the `except` branch) — a governance log with survivorship
  bias (only successes logged) tells you less than no log at all.
- **Treat eval regressions as findings, not obstacles.** A change that drops recall@10
  from 92% to 84% is information about the corpus or the change, not something to
  re-run until it passes. Write down what you learned in the milestone's eval report.
- **Resist adding scope that doesn't map to a PRD functional requirement.** Multi-user
  auth, a fancy web UI, fine-tuning — all reasonable ideas for a real product, all
  explicitly out of scope here (PRD §4). If it's tempting mid-build, it's most likely
  time pressure talking, not a requirement that got missed.

## Portfolio-specific practices

- **Keep commit history readable.** A reviewer skimming the git log should be able to
  follow the milestone structure without opening every diff.
- **The README's numbers section should always reflect the latest eval run** — stale
  claimed metrics are worse than no metrics section at all for a project whose whole
  point is measured rigor.
- **Don't bury the live demo.** The MCP-connected Claude Desktop screen recording
  (Milestone 4) belongs near the top of the README, not at the bottom after a wall of
  architecture prose — a reviewer deciding whether to keep reading needs the proof
  first.
