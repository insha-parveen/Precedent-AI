# Milestone 3 Evaluation Results — Agent Harness Hardening

**Date:** 2026-09-20
**Status:** ✅ COMPLETE — Architecture Restructuring, Provider Normalization & Live Verification

---

## 1. Architecture Restructuring & Provider System

- **LangGraph State Graph (ADR-011):** Replaced the inline tool loop with explicit graph nodes (`route`, `generate`, `tools`, `check_citations`, `retry`) using `langgraph.graph.message.add_messages`.
- **Decoupled LLMProvider System (ADR-013):**
  - Web/Hosted Engine: `GeminiProvider` (Primary) with multi-turn tool-calling and thought-signature preservation.
  - Fallback Engine: `GrokProvider` (xAI Grok / OpenAI-compatible client) for transparent recovery on transient rate limits (429), timeouts, and 503 errors.
  - Optional Direct Provider: `AnthropicProvider` preserved with tool-use formatting.
  - Client-Agnostic MCP: `mcp_server.py` exposes Precedent RAG and tools directly without forcing clients through vendor-locked providers.
- **Voyage Reranking (ADR-012):** Integrated `rerank()` in `src/precedent/retrieval.py` using Voyage AI.
- **Skill Naming Resolution:** Standardized on `negotiation-check` across `skills/`, routing, and tests.

---

## 2. Retrieval Evaluation Results (Post-Reranking)

**Test file:** `eval/test_queries.jsonl` (8 seed queries against CUAD 510 documents / 8,669 clauses)
**Metric:** `recall@10`

| Query Category | Expected Clause Type | Hit@k | Rank | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- |
| Governing Law | Governing Law | YES | 1 | 1701 |
| Non-Compete | Non-Compete | YES | 1 | 407 |
| Termination | Termination For Convenience | YES | 1 | 418 |
| Liability Cap | Cap On Liability | YES | 1 | 65898 |
| Change Of Control | Change Of Control | YES | 1 | 474 |
| Most Favored Nation | Most Favored Nation | YES | 2 | 1231 |
| Audit Rights | Audit Rights | YES | 1 | 66403 |
| Anti-Assignment | Anti-Assignment | YES | 1 | 494 |

**Recall@10:** 8/8 = **100.00%**

---

## 3. Live Verification Suite (12 Live Executions)

| # | User Query | Routed Skill | Grounded? | Cited Doc IDs | Tokens (In/Out) | Latency (ms) |
|---|---|---|---|---|---|---|
| 1 | "Show me governing law clauses from California or Delaware contracts" | `find-precedent` | YES | [157, 412, 429, 464, 515, 534] | 3,769 / 443 | 10,615 |
| 2 | "Find non-compete clauses restricting business activities" | `find-precedent` | YES | [106, 166, 194, 213, 281, 336] | 7,568 / 734 | 9,076 |
| 3 | "Find audit rights and inspection clauses" | `find-precedent` | YES | [141, 471] | 7,308 / 825 | 13,118 |
| 4 | "What limitations on liability are present in commercial contracts?" | `find-precedent` | YES | [58, 104, 225, 237, 248, 481, 529] | 7,783 / 495 | 52,547 |
| 5 | "Find termination for convenience notice requirements" | `find-precedent` (None) | YES | [34, 61, 74, 243, 259, 402, 488, 518, 531] | 2,547 / 317 | 5,111 |
| 6 | "How has Monsanto negotiated limitation of liability in its agreements?" | `negotiation-check` | YES | [513] | 3,593 / 256 | 70,761 |
| 7 | "What governing law provisions did PivX Solutions agree to?" | `negotiation-check` | YES | [531] | 13,013 / 226 | 9,682 |
| 8 | "What is Biocept's position on governing law in its contracts?" | `negotiation-check` | YES | [413] | 6,624 / 184 | 52,749 |
| 9 | "How did Clickstream Corporation handle non-compete clauses?" | `negotiation-check` | YES | [125] | 7,214 / 148 | 7,257 |
| 10 | "Check document 413 for governing law and liability risks" | `risk-flag` | YES | [413] | 7,400 / 511 | 8,677 |
| 11 | "Analyze document 9 for one-sided provisions or risk flags" | `risk-flag` | NO (Retry triggered) | [] | 16,100 / 1020 | 56,962 |
| 12 | "Find quantum computing teleportation licensing terms with SpaceY" | `negotiation-check` | YES (Refusal) | [] | 2,246 / 55 | 3,299 |

**Summary Statistics:**
- **Skill Routing Accuracy:** 10/12 (83.3%)
- **Groundedness Rate:** **11/12 (91.7%)** — Exceeds the DoD target of ≥ 80% (8/10).
- **Average Latency:** 24.99s across multi-turn tool calling, reciprocal rank fusion, and Voyage reranking passes.
- **Total Token Consumption:** 85,165 input / 5,214 output.

---

## 4. Citation-Retry Verification (ADR-005)

The citation-or-refuse verification path in `agent.py` was tested and confirmed:
- When the model retrieves documents (`seen_doc_ids` is non-empty) but fails to output citations in `[doc:ID]` format on the first pass, `check_citations_node` routes to `retry_node` with `GROUNDING_RETRY_PROMPT`.
- If citations are added on retry, `grounded = True` is assigned.
- If the model still fails to ground the factual claims after retry (as observed in Query 11), `[unverified — could not confirm citations against retrieved sources]` is prepended to the final answer and `grounded = False` is recorded in `skill_runs`.

---

## 5. Negotiation-Check Verification

`negotiation-check` was tested across multiple actual counterparties in CUAD (Monsanto, PivX Solutions, Biocept, Clickstream Corporation).
- Verifies that specific clauses (e.g. document 513 for Monsanto, document 413 for Biocept) are accurately surfaced and attributed to counterparty roles rather than plain keyword hallucination.


