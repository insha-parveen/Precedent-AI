"""MCP server. Run with: python -m src.precedent.mcp_server

Built on `mcp` 2.x's MCPServer (the v2 rename of what used to be called FastMCP —
if you're reading a tutorial that imports `from mcp.server.fastmcp import FastMCP`,
it's written against mcp 1.x; `pip show mcp` on this project's installed version first
if anything here stops matching what you see in the SDK's own error messages, they're
unusually good about pointing at the migration guide).

Exposes THREE tools:
- ask_precedent   Runs the full agent harness (route -> retrieve -> verify -> cite).
                   This is the primary tool — prefer it. It returns an answer that has
                   already been through the citation-or-refuse check, regardless of
                   which external model is calling it.
- search_contracts / get_document   Raw retrieval, for a caller that wants to reason
                   over sources itself rather than trust our harness's synthesis.

access_groups is hardcoded to ["public"] here because this demo corpus only has one
group. A real deployment resolves access_groups from the authenticated MCP session,
the same way DeepJudge resolves permissions from the firm's actual DMS/SharePoint ACLs
rather than trusting the client to say who it is — see CLAUDE.md rule 3.
"""
from __future__ import annotations

import asyncio

from mcp.server.mcpserver import MCPServer

from . import agent, retrieval
from .db import get_pool

ACCESS_GROUPS = ["public"]  # see module docstring

server = MCPServer(
    name="precedent",
    instructions=(
        "A retrieval-first agent over a public commercial-contracts corpus (CUAD). "
        "Prefer ask_precedent for natural-language questions — it routes to the right "
        "skill and returns a cited, grounding-checked answer. Use search_contracts / "
        "get_document directly only if you want to reason over raw sources yourself."
    ),
)


@server.tool()
async def ask_precedent(query: str) -> str:
    """Ask a question about the contract corpus in natural language. Routes to the
    right specialized skill (precedent lookup, negotiation history, or risk flagging),
    retrieves, verifies grounding, and returns a cited answer.
    """
    pool = await get_pool()
    result = await agent.run_query(pool, query, access_groups=ACCESS_GROUPS)
    text = result.answer
    if not result.grounded:
        text += "\n\n[note: this answer did not pass the citation check — verify independently]"
    return text


@server.tool()
async def search_contracts(
    query: str,
    clause_type: str | None = None,
    doc_type: str | None = None,
    parties: list[str] | None = None,
    limit: int = 10,
) -> str:
    """Hybrid semantic + keyword search over clause-level contract text. Returns raw
    results with [doc:ID] citation markers for the caller to reason over directly.
    """
    pool = await get_pool()
    results = await retrieval.hybrid_search(
        pool,
        query,
        access_groups=ACCESS_GROUPS,
        clause_type=clause_type,
        doc_type=doc_type,
        parties=parties,
        limit=limit,
    )
    if not results:
        return "No matching clauses found."
    return "\n\n".join(
        f"[doc:{r.document_id}] clause_id={r.clause_id} type={r.clause_type} "
        f"({r.doc_title}): {r.clause_text[:400]}"
        for r in results
    )


@server.tool()
async def get_document(document_id: int) -> str:
    """Fetch a full document plus all its labeled clauses by document_id."""
    pool = await get_pool()
    doc = await retrieval.get_document(pool, document_id, access_groups=ACCESS_GROUPS)
    if doc is None:
        return "Not found or not accessible."
    return str(doc)


def main() -> None:
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
