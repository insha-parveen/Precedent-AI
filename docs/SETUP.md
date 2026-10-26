# Setup — VS Code + Claude Code CLI

Two separate credentials are involved here and it's worth keeping them straight:
**Claude Code itself** authenticates with your Anthropic account (subscription login
or a Console account) to run as your coding agent. **Precedent's own runtime**
(`agent.py`, `mcp_server.py`) needs its own `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY`
in `.env` regardless — that's the app calling the API, not Claude Code calling it on
your behalf.

## 1. Install Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

(Windows: use WSL2, or the PowerShell installer from the same install page — the
native installer is the current recommended method; `npm install -g
@anthropic-ai/claude-code` still works but is the older path.)

Verify:

```bash
claude --version
```

## 2. Choose how you'll run it in VS Code

Both are fully supported; pick based on preference, not correctness:

- **VS Code extension (recommended if you want inline diffs and a GUI):** Extensions
  view (`Cmd+Shift+X` / `Ctrl+Shift+X`) → search "Claude Code" → Install. Requires VS
  Code 1.98+. Sign in with your Anthropic account when the panel first opens — no
  separate API key needed for this. Open the panel via the Spark icon in the sidebar.
- **CLI in the integrated terminal (recommended if you want every flag/scripting
  option):** open the terminal (`` Ctrl+` ``/`` Cmd+` ``) and run `claude` directly.
  It auto-integrates with VS Code for diff viewing and diagnostics. If you start a
  session in an external terminal and want to attach it to an open VS Code window
  later, run `/ide` inside that session.

Either way: **open the `precedent/` folder as the VS Code workspace root**, and make
sure the workspace is trusted (Claude Code doesn't run in Restricted Mode).

## 3. Unzip both drops into one repo

```bash
unzip precedent-starter.zip
unzip precedent-docs.zip -d precedent   # merges docs/ and the updated CLAUDE.md in
cd precedent
code .
```

## 4. Project-level setup

```bash
cp .env.example .env
# edit .env: add ANTHROPIC_API_KEY and VOYAGE_API_KEY (Precedent's runtime keys,
# not your Claude Code login)

docker compose up -d
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
pytest tests/ -q
```

All of the above should succeed before you open a Claude Code session and hand it any
milestone work — it's Milestone 1's own definition of done, already met by the
starter package, but re-verify on your machine since environments differ.

## 5. Register the MCP server (once you reach Milestone 4)

```bash
claude mcp add --transport stdio --scope project precedent -- python -m src.precedent.mcp_server
```

`--scope project` writes this to a project-level config so it's available to anyone
who opens this repo with Claude Code, not just your global config. Confirm it
registered with `/mcp` inside a Claude Code session.

## 6. Start Claude Code against this repo

From the integrated terminal (or the extension panel), run `claude`, and give it the
autonomous build prompt in `docs/prompts/00-autonomous-full-build.md` — see that file
for the exact text to paste.
