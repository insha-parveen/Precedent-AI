"""Tool schemas, defined once and shared by agent.py (native Anthropic tool use) and
mcp_server.py (MCP tool registration) so the two surfaces can never drift apart.
"""
from __future__ import annotations

SEARCH_CONTRACTS_SCHEMA = {
    "name": "search_contracts",
    "description": (
        "Search the contract corpus with a hybrid of semantic and keyword matching. "
        "Returns clause-level results with document context, ranked by relevance. "
        "Always filtered to the caller's access groups — never returns unauthorized "
        "content."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural-language description of what to find, e.g. "
                "'limitation of liability capped at fees paid'.",
            },
            "clause_type": {
                "type": "string",
                "description": "Optional: restrict to one CUAD clause category, e.g. "
                "'Governing Law', 'Indemnification', 'Non-Compete'.",
            },
            "doc_type": {
                "type": "string",
                "description": "Optional: restrict to one contract type, e.g. "
                "'License Agreement'.",
            },
            "parties": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: restrict to documents naming one or more of "
                "these parties.",
            },
            "limit": {
                "type": "integer",
                "description": "Max results, default 10. Use 15-20 when casting a wide "
                "net before narrowing.",
            },
        },
        "required": ["query"],
    },
}

GET_DOCUMENT_SCHEMA = {
    "name": "get_document",
    "description": (
        "Fetch a full document plus all its labeled clauses by document_id. Use this "
        "to verify a party's role in a deal, or to pull the complete text around a "
        "clause returned by search_contracts."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "document_id": {"type": "integer"},
        },
        "required": ["document_id"],
    },
}

ALL_TOOLS = [SEARCH_CONTRACTS_SCHEMA, GET_DOCUMENT_SCHEMA]
