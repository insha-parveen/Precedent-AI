# Precedent

A retrieval-first contract-intelligence agent, architecturally modeled on DeepJudge's
platform: a permission-aware hybrid search index, reusable Agent Skills, a verifying
agent loop, and an MCP server so any MCP client (Claude Desktop, Claude Code, a browser
chat) can use it. Domain data is public — the [CUAD dataset](https://www.atticusprojectai.org/cuad)
(510 commercial contracts, 13k+ expert-labeled clauses, CC BY 4.0) plus SEC EDGAR filings —
so it's safe to build, demo, and put in a portfolio.

## Architecture

```
CUAD + EDGAR --> ingest (clause-aware chunking, taxonomy tags)
             --> hybrid index (Postgres + pgvector: vectors + keywords + access_group)
             --> 3 Agent Skills (find-precedent / negotiation-check / risk-flag)
             --> agent harness (Claude: route -> retrieve -> verify -> cite -> log)
             --> MCP server --> Claude Desktop / Claude Code / web chat
                              (governance & eval log runs alongside every step)
```

Why each layer exists is explained in `CLAUDE.md`. Read that before making changes —
it's the project's memory, not just a config file.

## Prerequisites

- Python 3.11+
- Docker (for local Postgres + pgvector)
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))
- A Voyage AI API key ([dash.voyageai.com](https://dash.voyageai.com)) — the first
  50M tokens on `voyage-law-2` are free, which covers this entire corpus many times over

## Setup

```bash
# 1. Environment
cp .env.example .env
# edit .env: add ANTHROPIC_API_KEY and VOYAGE_API_KEY

# 2. Local database
docker compose up -d
python scripts/init_db.py          # applies db/schema.sql

# 3. Dependencies
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4. Verify the scaffold before touching data
pytest tests/ -q

# 5. Ingest data (takes a few minutes; well inside free API tiers)
python scripts/ingest_cuad.py

# 6. Evaluate retrieval quality against CUAD's own labels
python eval/run_eval.py

# 7. Run the MCP server
python -m src.precedent.mcp_server

## CLI

The same Precedent capabilities (search, ask, document lookup) are available via the terminal:

```bash
precedent search "governing law in IP agreements"
precedent ask "Find precedent for governing law in IP agreements."
precedent document <document_id>
```

The CLI, Web UI, and MCP server all reuse the same core Precedent services for retrieval, agency, and governance.
```

## License note

CUAD is CC BY 4.0 (free for commercial and non-commercial use). SEC filings are public
record. No confidential data is used anywhere in this project.
