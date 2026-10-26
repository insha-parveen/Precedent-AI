# Milestone 6 — Deployable Demo (Web Chat + FastAPI + Deploy)

**Goal:** A reviewer can visit a URL, type a contract question, get a cited answer — no CLI, no MCP setup, no local Docker.

**Definition of Done:**
- [ ] `src/precedent/api.py` → FastAPI app with `/api/ask`, `/api/search`, `/api/document` endpoints that **reuse the exact same functions** as `mcp_server.py` (no parallel logic)
- [ ] `web/src/hooks/useChat.ts` → calls `/api/ask`, streams response, handles citations, opens document drawer
- [ ] `docker-compose.yml` → `api`, `web`, `db` services; `docker compose up` works locally
- [ ] `web/vercel.json` + `Dockerfile` → deploys to Vercel (web) + Railway/Render (api) with one env var each
- [ ] `README.md` → shows Milestone 2/3 eval numbers, Milestone 4 demo GIF, one-click deploy buttons
- [ ] **Smoke test:** `docker compose up` → open `localhost:3000` → ask "Find governing law clauses in merger agreements" → get cited answer in <10s

**Constraints:**
- Do not add new business logic in `api.py` — wrap `agent.run_query`, `retrieval.hybrid_search`, `retrieval.get_document`
- Keep `useChat` simple: POST → stream text → parse `[doc:ID]` → fetch document on click
- No auth yet (Phase 1 pilot handles that); `access_groups=["public"]` hardcoded is fine for demo
- Tailwind/GSAP UI already exists — don't redesign, just wire it

**Run order:**
1. `python scripts/init_db.py` (if needed)
2. `python scripts/ingest_cuad.py` (if DB empty)
3. `docker compose up --build`
4. Verify at `http://localhost:3000`