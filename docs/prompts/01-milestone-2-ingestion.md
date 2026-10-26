# Prompt 01 — Milestone 2: Data ingestion (standalone)

Use this if you're starting a fresh Claude Code session scoped to just this milestone,
rather than running the full autonomous prompt.

```
Read CLAUDE.md and docs/ROADMAP.md's Milestone 2 section before starting.

Goal: get real CUAD data into the index and produce the first real eval numbers.

1. Inspect data/raw/CUAD_v1_master_clauses.csv's actual columns and compare against
   scripts/ingest_cuad.py's METADATA_COLUMNS and CONTEXT_COLUMN_SUFFIX assumptions.
   Adjust the script if they don't match — explain what changed and why.
2. Bring up the database (docker compose + scripts/init_db.py) if not already running.
3. Run the ingestion script. Report how many documents and clauses were ingested, and
   sanity-check that against CUAD's known size (510 contracts, 13k+ labeled clauses) —
   investigate if the numbers look far off rather than assuming it's fine.
4. Run eval/run_eval.py. If recall@10 is below 90% (PRD §6), investigate before
   reporting done — check clause_type values actually in the DB against
   eval/test_queries.jsonl's expected_clause_type strings first (see run_eval.py's
   own docstring for the exact query to run).
5. Write a short report to docs/eval-results/milestone-2.md: what was ingested, the
   eval numbers, and any adjustments made to the ingestion script and why.

Check Milestone 2's Definition of Done in ROADMAP.md explicitly before calling this
done.
```
