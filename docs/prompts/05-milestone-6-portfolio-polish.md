# Prompt 05 — Milestone 6: Portfolio polish (standalone)

```
Read CLAUDE.md and docs/ROADMAP.md's Milestone 6 section before starting.

Goal: the repo reads as a finished, credible artifact to an outside reviewer in under
10 minutes, without me needing to explain anything verbally.

1. Update README.md's top section with the actual eval numbers from
   docs/eval-results/ (not placeholder numbers) and a note on where the demo GIF goes
   — put the proof near the top, not after a long architecture writeup.
2. If a demo recording exists, embed/link it near the top of the README.
3. Propose (but don't build without confirmation) a GitHub Actions workflow that runs
   eval/run_eval.py on push, so the README's numbers are provably reproducible.
4. Propose (but don't build without confirmation) a minimal FastAPI + web chat for
   reviewers without an MCP client — reusing the same functions mcp_server.py already
   exposes, not a parallel implementation.
5. Draft a short write-up (docs/WRITEUP.md) connecting the build back to the DeepJudge
   research that motivated it — pull from ARCHITECTURE_DECISIONS.md and PRD.md rather
   than writing new claims from scratch.

Confirm with me before building the CI workflow or the web UI — everything else in
this milestone, keep moving on autonomously.
```
