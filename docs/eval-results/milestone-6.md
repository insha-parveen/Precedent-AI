# Milestone 6 Evaluation Results — Web UI Complete

**Date:** 2026-10-14  
**Status:** ✅ COMPLETE — Full Stack Verified End-to-End

---

## 1. Executive Summary

Milestone 6 delivers the complete web interface for Precedent-AI: a Next.js frontend proxied to a FastAPI backend, with real-time chat, citation chips, document drawer, and risk visualization — all backed by the same retrieval-first agent harness used by the CLI and MCP server.

- **Frontend:** Next.js 16 (App Router) + Tailwind CSS + GSAP (marketing page only)
- **Backend:** FastAPI with endpoints `/api/chat`, `/api/ask`, `/api/search`, `/api/document/{id}`
- **Proxy:** Next.js rewrites `/api/*` → `BACKEND_URL` (Docker: `http://api:8000`, local: `http://localhost:8000`)
- **Components:** CitationChip, RiskCard, DocumentDrawer, MarkdownRenderer with custom citation handling

---

## 2. Architecture

```
┌─────────────────┐     /api/* rewrite      ┌──────────────────┐
│   Next.js 16    │ ──────────────────────► │   FastAPI API    │
│   (port 3000)   │                         │   (port 8000)    │
│                 │                         │                  │
│  - Marketing    │                         │  - /api/chat     │
│  - Chat UI      │                         │  - /api/ask      │
│  - GSAP anim    │                         │  - /api/search   │
└─────────────────┘                         │  - /api/document │
                                            └────────┬─────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────┐
                                            │   Agent Harness  │
                                            │   (LangGraph)    │
                                            └────────┬─────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────┐
                                            │  Hybrid Search   │
                                            │  + Reranking     │
                                            │  (pgvector)      │
                                            └──────────────────┘
```

---

## 3. Component Verification

### 3.1 Chat Flow (useChat hook)
- **Endpoint:** `POST /api/ask` (alias for `/api/chat`)
- **Request:** `{ "query": string }`
- **Response:** `ChatResponse` with `answer`, `skill_used`, `cited_doc_ids`, `grounded`, `input_tokens`, `output_tokens`, `latency_ms`
- **Verified:** All three skills route correctly:
  - `find-precedent` — "Find governing law clauses in Intellectual Property agreements"
  - `risk-flag` — "Check document 413 for governing law and liability risks"
  - `negotiation-check` — "How has Monsanto negotiated limitation of liability?"

### 3.2 CitationChip
- **Behavior:** Renders `[doc:ID]` as clickable chip with hover arrow
- **Interaction:** Click → opens DocumentDrawer with that document's clauses
- **Styling:** Navy accent, rounded, pointer cursor, subtle shadow on hover

### 3.3 DocumentDrawer
- **Position:** Right-side slide-in (fixed, z-50)
- **Content:** Document metadata (title, type, parties, source, filing date) + expandable ClauseCards
- **Typography:** Clause text in Merriweather serif (vs UI Inter sans-serif)
- **State:** Controlled by `useChat` hook via `fetchDocument(docId)` and `closeDrawer()`

### 3.4 RiskCard
- **Levels:** Low (green), Medium (amber), High (red)
- **Icons:** Shield (Low), AlertTriangle (Medium), AlertCircle (High)
- **Trigger:** Parsed from `MarkdownRenderer` via regex on `Risk: Level / Reason:` pattern
- **Note:** `risk-flag` skill currently outputs markdown tables; risk readout extraction works for explicit "Risk: Level / Reason:" format

### 3.5 MarkdownRenderer
- **Base:** `react-markdown` with custom components
- **Code handling:** Detects `[doc:ID]` in inline code → renders as CitationChip
- **Risk extraction:** Regex `Risk:\s*(Low|Medium|High)\s*[/|:]\s*([^\n]+)` extracts structured risk readouts

---

## 4. API Contract Verification

| Endpoint | Method | Request | Response | Status |
|----------|--------|---------|----------|--------|
| `/api/chat` | POST | `ChatRequest { query }` | `ChatResponse` | ✅ 200 |
| `/api/ask` | POST | `ChatRequest { query }` | `ChatResponse` | ✅ 200 |
| `/api/search` | POST | `SearchRequest { query, clause_type?, doc_type?, parties?, limit? }` | `SearchResponse { results[] }` | ✅ 200 |
| `/api/document/{id}` | GET | path param | `DocumentResponse { document_id, doc_title, doc_type, parties, jurisdiction, filing_date, source, clauses[] }` | ✅ 200 |
| `/docs` | GET | — | Swagger UI | ✅ 200 |
| `/openapi.json` | GET | — | OpenAPI 3.1 spec | ✅ 200 |

**Proxy verified:** Next.js rewrites `/api/*` → `http://localhost:8000/api/*` work correctly in dev and Docker.

---

## 5. Skill Routing Verification (Live)

| Query | Expected Skill | Actual Skill | Grounded | Citations |
|-------|---------------|--------------|----------|-----------|
| "Find governing law clauses in Intellectual Property agreements" | `find-precedent` | `find-precedent` | ✅ | 3 doc IDs |
| "Check document 413 for governing law and liability risks" | `risk-flag` | `risk-flag` | ✅ | 1 doc ID |
| "How has Monsanto negotiated limitation of liability?" | `negotiation-check` | `negotiation-check` | ✅ | 1 doc ID |

All skills return `grounded: true` with valid `cited_doc_ids` matching retrieved documents.

---

## 6. Database State

| Source | Documents | Clauses |
|--------|-----------|---------|
| CUAD | 510 | 8,669 |
| SEC EDGAR | 2 | 13 |
| **Total** | **512** | **8,682** |

Cross-source search functional: queries return mixed CUAD + EDGAR results when relevant.

---

## 7. Docker Compose Verification

```bash
docker compose up -d db    # PostgreSQL + pgvector on port 5435
docker compose up -d api   # FastAPI on port 8000
docker compose up -d web   # Next.js on port 3000
```

- **db:** Healthcheck passes (`pg_isready`)
- **api:** Depends on db:healthy; serves OpenAPI at `/docs`
- **web:** Depends on api; compiles without TypeScript errors; HMR works on `127.0.0.1:3000`

---

## 8. Definition of Done Checklist (Milestone 6)

| Criterion | Status |
|-----------|--------|
| Next.js 16 + Tailwind + GSAP marketing page | ✅ |
| Chat UI with `useChat` hook (messages, loading, error, drawer) | ✅ |
| `CitationChip` — clickable `[doc:ID]` → drawer | ✅ |
| `DocumentDrawer` — metadata + Merriweather clause cards | ✅ |
| `RiskCard` — Low/Medium/High visual cards | ✅ |
| `MarkdownRenderer` — citation links + risk extraction | ✅ |
| FastAPI endpoints: `/api/chat`, `/api/ask`, `/api/search`, `/api/document/{id}` | ✅ |
| Next.js rewrites proxy `/api/*` to backend | ✅ |
| Docker compose: db, api, web all healthy | ✅ |
| E2E verified: all three skills route, cite, ground | ✅ |
| Demo query documented for README GIF | ✅ |
| `pytest tests/ -q` passes (20/20) | ✅ |

---

## 9. Demo Recording Script

For the README demo GIF (`docs/demo.gif`), record this flow at `http://localhost:3000`:

1. **Landing page** — Show marketing page with GSAP scroll animations (2-3s)
2. **Navigate to Chat** — Click "Try the Agent" or navigate to `/app` (1s)
3. **Query 1 (find-precedent):** Type `"Find governing law clauses in Intellectual Property agreements"` → Enter
   - Show: skill badge "find-precedent", grounded ✅, 3 citation chips appear
4. **Citation interaction:** Hover citation chip → shows arrow; click first chip
   - Show: DocumentDrawer slides in with document metadata + Merriweather clause text
   - Expand/collapse a ClauseCard
5. **Close drawer** — Click backdrop or close button
6. **Query 2 (risk-flag):** Type `"Check document 413 for governing law and liability risks"` → Enter
   - Show: skill badge "risk-flag", grounded ✅, risk cards render (if parsed)
7. **Query 3 (negotiation-check):** Type `"How has Monsanto negotiated limitation of liability?"` → Enter
   - Show: skill badge "negotiation-check", grounded ✅, citation chips

Save as `docs/demo.gif` (or `web/public/demo.gif` and reference from README).

---

## 10. Known Limitations

- **Risk readout parsing:** `risk-flag` skill outputs markdown tables, not "Risk: Level / Reason:" format — RiskCard only renders for the explicit format. The skill output would need to be adjusted or the parser extended.
- **No `/health` endpoint:** FastAPI has `/docs` and `/openapi.json` but no `/health`; add if needed for container orchestration.
- **Voyage rate limits:** Free tier still rate-limits embeddings; full ingest takes hours.
- **Production hardening:** `precedent serve` uses `reload=True`; disable for production.