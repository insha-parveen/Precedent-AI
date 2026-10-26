# Precedent

A retrieval-first contract-intelligence agent, architecturally modeled on DeepJudge's
platform: a permission-aware hybrid search index, reusable Agent Skills, a verifying
agent loop, and an MCP server so any MCP client (Claude Desktop, Claude Code, a browser
chat) can use it. Domain data is public — the [CUAD dataset](https://www.atticusprojectai.org/cuad)
(510 commercial contracts, 13k+ expert-labeled clauses, CC BY 4.0) plus SEC EDGAR filings —
so it's safe to build, demo, and put in a portfolio.

## 🎯 Live Demo
<!-- Insert demo GIF here after recording: `docs/demo.gif` -->
<!-- ![Precedent Demo](docs/demo.gif) -->

**Try it:** `docker compose up --build` → open [http://localhost:3000](http://localhost:3000)

### One-Click Deploy
[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FInshaParveen%2Fprecedent-AI&project-name=precedent&repository-name=precedent-AI)
[![Deploy to Railway](https://railway.app/button.svg)](https://railway.app/template/precedent?referralCode=precedent)

## 📊 Evaluation Results

### Milestone 2 — CUAD Ingestion & Retrieval Baseline
- **Recall@10:** 100% (8/8 seed queries)
- **Contracts ingested:** 510 | **Clauses indexed:** 8,669
- **Embedding model:** `voyage-law-2` (1024-dim)
- **Database:** PostgreSQL 16 + pgvector (HNSW index, `vector_cosine_ops`) on port 5435
- **Key fix:** Metadata cleanup deleted 3,896 non-substantive clause rows (Parties, Agreement Date, Effective Date, Expiration Date) that crowded out true clause content
- **Full results:** [`docs/eval-results/milestone-2.md`](docs/eval-results/milestone-2.md)

### Milestone 3 — Agent Harness Hardening
- **Architecture:** LangGraph state graph (route → generate → tools → check_citations → retry) — ADR-011
- **Provider abstraction:** `LLMProvider` protocol with Gemini primary + Grok fallback — ADR-013
- **Voyage reranking:** `voyage-rerank-2` integrated post-retrieval — ADR-012
- **Recall@10 (post-reranking):** 100% (8/8)
- **Groundedness rate:** 91.7% (11/12 live queries) — exceeds DoD target of ≥80%
- **Skill routing accuracy:** 83.3% (10/12)
- **Avg latency:** 24.99s (multi-turn + reranking)
- **Total tokens:** 85,165 input / 5,214 output across 12 live executions
- **Citation enforcement:** Hard-coded regex `\[doc:(\d+)\]` verified before any answer returns; retry with `GROUNDING_RETRY_PROMPT` on failure — ADR-005
- **Full results:** [`docs/eval-results/milestone-3.md`](docs/eval-results/milestone-3.md)

### Milestone 4 — MCP Integration (Live & Standalone)
- **Transport:** Standard input/output (`stdio`) via `python -m src.precedent.mcp_server`
- **Primary Tool:** `ask_precedent(query: str)` — executes full LangGraph state graph
- **Secondary Tools:** `search_contracts`, `get_document` for raw retrieval access
- **Test Coverage:** 7 dedicated unit tests in `tests/test_mcp_server.py`; total suite 17/17 passing
- **Demo query:** `"Find precedent for governing law in Intellectual Property agreements."`
- **Full results:** [`docs/eval-results/milestone-4.md`](docs/eval-results/milestone-4.md)

### Milestone 5 — SEC EDGAR Extension
- **Primary document parsing:** 10-K, 10-Q, 8-K filings with section extraction
- **EDGAR clauses added:** 13 clauses across 2 sample filings
- **Cross-source search:** CUAD + EDGAR unified in single hybrid index
- **Full results:** [`docs/eval-results/milestone-5.md`](docs/eval-results/milestone-5.md)

### Milestone 6 — Web UI Complete
- **Frontend:** Next.js 16 + Tailwind + GSAP (marketing page animations only)
- **API:** FastAPI backend with `/api/chat`, `/api/ask`, `/api/search`, `/api/document/{id}`
- **Components:** CitationChip (clickable `[doc:ID]`), RiskCard (Low/Medium/High), DocumentDrawer (slide-in with Merriweather serif clauses), MarkdownRenderer (citation links + risk readout extraction)
- **Verified flows:** Chat → skill badge → grounded status → citation chips → drawer with clause text
- **Full results:** [`docs/eval-results/milestone-6.md`](docs/eval-results/milestone-6.md)

## Architecture

```
CUAD + EDGAR --> ingest (clause-aware chunking, taxonomy tags)
             --> hybrid index (Postgres + pgvector: vectors + keywords + access_group)
             --> 3 Agent Skills (find-precedent / negotiation-check / risk-flag)
             --> agent harness (LangGraph: route -> retrieve -> verify -> cite -> log)
             --> MCP server --> Claude Desktop / Claude Code / web chat
                              (governance & eval log runs alongside every step)
```

Why each layer exists is explained in `CLAUDE.md` and `docs/ARCHITECTURE_DECISIONS.md`.
Read those before making changes.

## Prerequisites

- Python 3.11+
- Node.js 20+ (only for the web UI in `web/`)
- Docker (for local Postgres + pgvector)
- API keys: Anthropic, Voyage AI (embeddings), and optionally Gemini / OpenAI / Grok
  depending on which provider you set in `AGENT_MODEL`

## Setup

Run everything from the repository root. **Create and activate the virtual environment
first** — every later step needs the installed dependencies.

```bash
# 1. Virtual environment + dependencies
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                     # required for `precedent serve` and the `precedent` command

# 2. Environment
cp .env.example .env                 # then fill in your API keys

# 3. Local database (Postgres + pgvector on host port 5435)
docker compose up -d db
python scripts/init_db.py            # applies db/schema.sql

# 4. Verify before touching data (no DB or API keys needed)
pytest tests/ -q

# 5. Ingest data
python scripts/ingest_cuad.py

# 6. Evaluate retrieval quality against CUAD's own labels
python eval/run_eval.py

# 7. Run the MCP server (stdio)
python -m src.precedent.mcp_server
```

`DATABASE_URL` in `.env` must match the port in `docker-compose.yml`
(`postgresql://precedent:precedent@localhost:5435/precedent`).

## Usage

CLI:

```bash
precedent search "governing law in IP agreements"
precedent ask "Which governing law clauses select Nevada?"
precedent document <document_id>
precedent serve --port 8000          # FastAPI backend for the web UI
```

API (after `precedent serve`):

- `POST /api/chat` with `{"query": "..."}` — grounded answer with citations
- `GET /api/document/{doc_id}` — document metadata and clauses

Web UI: `cd web && npm install && npm run dev`.

## MCP Server Usage

The MCP (Model Context Protocol) server allows any MCP-compatible client (Claude Desktop, Claude Code, custom MCP hosts) to access Precedent's contract intelligence capabilities.

### Starting the MCP Server

```bash
# From the project root with virtual environment activated
python -m src.precedent.mcp_server
```

### Client Configuration

Configure your MCP host (e.g., Claude Desktop) to connect to the server:

```json
{
  "mcpServers": {
    "precedent": {
      "command": "python",
      "args": ["-m", "src.precedent.mcp_server"],
      "cwd": "ABSOLUTE_PATH_TO_PROJECT_ROOT",
      "env": {
        "LOCAL_MODE": "true",
        "ALLOWED_INGEST_ROOTS": "C:/Users/YourName/Documents/Contracts;D:/LegalDocs"
      }
    }
  }
}
```

### Available MCP Tools

#### Query Tools (Safe - No File System Access)
- **`ask_precedent`**: Natural language questions about contracts
  - Returns grounded answer with `[doc:ID]` citations
  - Example: `{"query": "What are standard termination clauses in SaaS agreements?"}`

- **`search_contracts`**: Raw hybrid search for client-side reasoning
  - Returns matching clauses with `[doc:ID]` markers
  - Example: `{"query": "liability cap", "clause_type": "limitation of liability", "limit": 5}`

- **`get_document`**: Fetch full document by ID
  - Returns structured JSON document with all clauses
  - Example: `{"document_id": 42}`

#### Local Ingestion Tools (Require Path Configuration)
⚠️ **Security Note**: These tools require proper `ALLOWED_INGEST_ROOTS` configuration to prevent unauthorized file system access.

- **`ingest_directory`**: Process local contract folders
  - Arguments: `path`, `access_group` (default: "public"), `doc_type`, `party`, `recursive` (default: true), `dry_run` (default: false)
  - Example: 
    ```json
    {
      "tool": "ingest_directory",
      "arguments": {
        "path": "C:/Users/YourName/Documents/Contracts/NDAs",
        "access_group": "legal_team",
        "doc_type": "nda",
        "party": "Acme Corp",
        "recursive": true
      }
    }
    ```

- **`watch_folder`**: Set up background monitoring (local-mode only)
  - Arguments: `path`, `access_group`, `doc_type`, `party`
  - Returns confirmation and instructions to start watcher daemon with `precedent watch`

### Security Best Practices

To prevent unauthorized file system access:

1. **Always configure `ALLOWED_INGEST_ROOTS`**:
   - Never leave it empty/default (this disables path validation)
   - Specify exact directories allowed (e.g., `C:/Users/<user>/Documents/Contracts`)
   - Use semicolon-separated list for multiple roots: `"C:/Contracts;D:/LegalDocs"`

2. **Prefer local-mode for sensitive data**:
   - Set `LOCAL_MODE=true` to keep data on user's machine
   - Avoids transmitting contracts to external APIs

3. **Use specific access groups**:
   - Rather than default "public", use meaningful groups like "legal_team", "executive", etc.
   - Implement proper authentication in production deployments

4. **Validate paths before use**:
   - Ensure `path` arguments point to intended directories only
   - Avoid system directories, user profile roots, or other sensitive locations

### Example Secure Workflow

1. **Setup** (one-time):
   - Create dedicated folder: `C:\Contracts\`
   - Set `ALLOWED_INGEST_ROOTS=C:\Contracts\` in `.env`
   - Set `LOCAL_MODE=true`

2. **Initial Ingestion**:
   ```json
   {
     "tool": "ingest_directory",
     "arguments": {
       "path": "C:/Contracts",
       "access_group": "client_legal_team",
       "recursive": true
     }
   }
   ```

3. **Regular Usage**:
   ```json
   {
     "tool": "ask_precedent",
     "arguments": {
       "query": "What are the standard payment terms in our MSAs?"
     }
   }
   ```

4. **Automatic Updates** (optional):
   ```json
   {
     "tool": "watch_folder",
     "arguments": {
       "path": "C:/Contracts/Active",
       "access_group": "client_legal_team"
     }
   }
   // Then run: precedent watch
   ```

The CLI, API, web UI, and MCP server all reuse the same retrieval, agent, and governance
code.

## Issues found and fixed

This project was handed over in a broken state. The problems below were diagnosed and
fixed; the test suite (20 tests), the web build, and an end-to-end run
(DB → ingest → search → ask → API) now all work.

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | `ModuleNotFoundError` on every import; tests would not run | The committed `venv/` was created on another machine (`C:\Users\HP\Anaconda3`). Virtual environments are not portable. | Deleted it, created a fresh `.venv/`, documented the setup order. |
| 2 | `No module named 'langgraph'` | `agent.py` moved to LangGraph but `langgraph` and `langchain-core` were never added to `requirements.txt` (nor `api/requirements.txt`, so the Vercel deploy would also fail). | Added both to both files. |
| 3 | `precedent serve` crashed with `No module named 'precedent'` | The package was never installed, but `uvicorn` imports `precedent.api`. | `pip install -e .` added to setup. |
| 4 | Insecure CORS | `allow_origins=["*"]` combined with `allow_credentials=True`, in both `api.py` and `vercel.json`. | Credentials disabled. Use explicit origins if cookies/auth are added later. |
| 5 | Docker container would fail to start | `Dockerfile` ran `python -m precedent.cli` without `src/` on the Python path. | Added `ENV PYTHONPATH=/app/src`. |
| 6 | Postgres would not start on port 5434 | Port already used by another local container. | Moved this project's DB to host port 5435. |
| 7 | MCP server showed "Connection closed" | `.mcp.json` runs `python`, which resolved to a global interpreter without the project's dependencies. | Start Claude Code with the project `.venv` activated (or point `command` at `.venv/Scripts/python`). |
| 8 | Docs and `CLAUDE.md` silently untracked | `.gitignore` listed `CLAUDE.md`, `docs/`, `.claude/`. | Removed those entries; added `node_modules/`, `.next/`, `*.tsbuildinfo`. |
| 9 | Constant CRLF/LF warnings | No line-ending policy on Windows. | Added `.gitattributes` (`* text=auto`). |
| 10 | README setup was wrong | `init_db.py` ran before dependencies were installed; code fences were broken. | Rewrote this README. |

## Known limitations

- **Ingestion speed:** Voyage's free tier rate-limits embeddings (about one batch of 32
  every ~22 seconds), so a full CUAD ingest takes hours. Add a payment method to Voyage
  for normal throughput. Ingestion can be stopped and resumed.
- **Eval:** `eval/run_eval.py` is only meaningful after a full ingest.
- **Untested:** the Docker image build, the Vercel deployment, and the web UI talking to
  the live API.
- `precedent serve` runs uvicorn with `reload=True`; disable that for production.
- `AGENT_MODEL` in `.env.example` uses a non-standard `aiml/...` model ID — set it to a
  model your configured provider actually serves.

## License note

CUAD is CC BY 4.0 (free for commercial and non-commercial use). SEC filings are public
record. No confidential data is used anywhere in this project.
