# Prompt 03 — Milestone 4: MCP live (standalone)

```
Read CLAUDE.md and docs/ROADMAP.md's Milestone 4 section before starting. Milestones
2-3 should already be done.

Goal: the system is usable from outside its own repo, live, over MCP.

1. Register the server: claude mcp add --transport stdio --scope project precedent
   -- python -m src.precedent.mcp_server. Confirm it shows up via /mcp.
2. Run a real query through ask_precedent from within this Claude Code session (or
   Claude Desktop if available) and confirm it returns a cited answer end-to-end.
3. Independently test search_contracts and get_document as raw tools.
4. If anything about the tool schemas, descriptions, or error messages would confuse
   an external caller that isn't you, fix it — you're the first real test of this
   interface from the outside.
5. Note down the exact query used for the successful ask_precedent demo — this becomes
   the basis for the README's demo GIF, which is a manual step for the person to record,
   not something you need to produce yourself.

Check Milestone 4's Definition of Done in ROADMAP.md, then stop and report a full
summary of Milestones 2-4: what was built, key numbers, any new ADRs added, anything
that deviated from the original plan and why. This is the checkpoint called out in the
autonomous prompt — wait for confirmation before moving into Milestone 5 or 6.
```
