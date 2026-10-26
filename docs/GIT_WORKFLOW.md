# Git workflow — Precedent(do not add authored by claude or @claude))

## Setup (once)

```bash
git init
git add -A
git commit -m "Milestone 1: scaffold verified"
```

Public, deliberately — this is a portfolio piece, and a public repo with a readable
history is part of the deliverable, not just the code.

`.gitignore` already excludes `.env`, `data/raw/` (CUAD is large and redistributable
from source, no reason to commit it), and cache dirs. Don't relax these.

## Branch strategy: one branch per milestone

```bash
git checkout -b milestone-2-ingestion
# Claude Code works, commits as it goes
gh pr create --fill
# you review, merge to main
git checkout main && git pull
```

Why a PR per milestone rather than committing straight to `main`: it gives each
milestone's Definition of Done (docs/ROADMAP.md) a natural review checkpoint, and it
gives the two flagged files (agent.py's citation logic, retrieval.py's access_group
filtering — CLAUDE.md rule 2/3) an actual moment of human review instead of an honor
system. It also makes the git log itself legible to a portfolio reviewer: six PRs
mapping to six milestones is a much clearer story than sixty small unstructured
commits.

Tag the state after Milestone 4 (working MCP demo) — that's the version you'll
actually point people at:

```bash
git tag v0.1-demo && git push --tags
```

## Commit message convention

`<milestone>: <what> (ADR-<n> if applicable)`, e.g.:

```
Milestone 3: add citation-retry path exercise + negotiation-check verification test (ADR-005, ADR-009)
```

This makes `git log` a second, cross-checkable copy of the decision record in
`docs/ARCHITECTURE_DECISIONS.md`.

## Optional: Claude's GitHub App

From inside a Claude Code session, once the GitHub remote exists:

```
/install-github-app
```

This installs the Claude GitHub App and (optionally) a `.github/workflows/claude.yml`
that lets you `@claude` a PR or issue comment to have it analyze, implement, or push
changes directly from GitHub — and there's a separate automatic Code Review feature
that can run on every PR with no workflow file needed at all. Two ways to use this
here:

1. **CI eval gate (Milestone 6's optional item, now concrete):** a workflow that runs
   `pytest tests/ -q` and `eval/run_eval.py` on every PR, so the README's numbers stay
   provably reproducible rather than just claimed.
2. **A second reviewer on the two flagged files:** tag `@claude` on any PR touching
   `agent.py` or `retrieval.py` asking it to specifically check against ADR-005 and
   ADR-009 before you merge — a cheap second pass on exactly the two places a quiet
   regression matters most.

Needs repo admin access and either `ANTHROPIC_API_KEY` or a Claude Pro/Max OAuth token
in repo secrets — see the app's own setup flow, it walks through this.
