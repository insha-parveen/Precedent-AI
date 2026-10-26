# Prompt 00 — Autonomous full build (Milestones 2 through 6)

Use this as your primary prompt. It authorizes Claude Code to move through the whole
roadmap without stopping for approval at each phase, per the project's working style —
it only needs to stop for the specific reasons listed at the end.

Paste this after `claude` is running with `precedent/` as the workspace root:

```
Read CLAUDE.md, docs/PRD.md, docs/ARCHITECTURE_DECISIONS.md, and docs/ROADMAP.md in
full before doing anything. These are the project's memory, requirements, and decision
record — not background reading, the actual spec.

Work through Milestones 2, 3, and 4 in docs/ROADMAP.md sequentially and autonomously.
For each milestone:
1. State your plan for that milestone in 3-5 bullets before starting it.
2. Do the work.
3. Check it against that milestone's Definition of Done checklist explicitly, item by
   item.
4. If everything passes, commit with a message referencing the milestone and any ADR
   numbers it touches, then move directly to the next milestone without waiting for
   me.
5. If a Definition of Done item fails and you can fix it yourself within the
   milestone's stated scope, fix it and re-check before moving on.

Make any reasonable engineering decision within what CLAUDE.md, the PRD, and the
existing ADRs already establish, without asking me first. Document any new
architectural decision (anything not already covered by an existing ADR) as a new
entry appended to docs/ARCHITECTURE_DECISIONS.md before moving on from the milestone
where you made it.

Two files get flagged for my review rather than auto-committed even in this mode:
any change to the citation-check/retry logic in src/precedent/agent.py, and any
change to access_group filtering in src/precedent/retrieval.py. Everything else,
keep moving.

Stop and tell me, rather than proceeding, only if:
- You need a credential, download, or paid resource I haven't provided (say exactly
  what and why).
- A Definition of Done item fails and the fix would mean deviating from an existing
  ADR or the PRD's non-goals (propose the deviation as a new ADR draft instead of
  just doing it).
- An eval regression (recall@10 drops from a prior milestone's number) can't be
  explained after a reasonable investigation.

Milestone 5 (SEC EDGAR) and Milestone 6 (polish) are lower priority — after Milestone
4's Definition of Done is fully met, stop, report a summary of all decisions made and
ADRs added across Milestones 2-4, and wait for me before continuing into 5/6. That's
a deliberate checkpoint, not a contradiction of "keep moving" — Milestone 4 is the
point where the system is demoable, which is worth a real look before going further.
```
