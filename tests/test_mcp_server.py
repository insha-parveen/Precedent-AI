"""MCP server unit and contract tests (offline, no database or network needed)."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.precedent.mcp_server import (
    server,
    ask_precedent,
    search_contracts,
    get_document,
)
from src.precedent.retrieval import ClauseResult
from src.precedent.agent import AgentResult


def test_mcp_server_initialization_and_tools():
    assert server.name == "precedent"
    assert "retrieval-first" in server.instructions


@pytest.mark.asyncio
async def test_search_contracts_empty():
    with patch("src.precedent.mcp_server.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.mcp_server.retrieval.hybrid_search", new_callable=AsyncMock) as mock_search:
        mock_pool.return_value = MagicMock()
        mock_search.return_value = []

        result = await search_contracts("nonexistent clause")
        assert result == "No matching clauses found."
        mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_search_contracts_formatted_results():
    with patch("src.precedent.mcp_server.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.mcp_server.retrieval.hybrid_search", new_callable=AsyncMock) as mock_search:
        mock_pool.return_value = MagicMock()
        mock_search.return_value = [
            ClauseResult(
                clause_id=101,
                document_id=42,
                clause_type="Governing Law",
                clause_text="This agreement is governed by the laws of Delaware.",
                doc_title="Sample Master Agreement.pdf",
                doc_type="Master Services Agreement",
                parties=["Acme Corp", "Beta LLC"],
                score=0.95,
            )
        ]

        result = await search_contracts("governing law", clause_type="Governing Law", limit=5)
        assert "[doc:42]" in result
        assert "clause_id=101" in result
        assert "type=Governing Law" in result
        assert "Sample Master Agreement.pdf" in result
        assert "laws of Delaware" in result


@pytest.mark.asyncio
async def test_get_document_not_found():
    with patch("src.precedent.mcp_server.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.mcp_server.retrieval.get_document", new_callable=AsyncMock) as mock_get_doc:
        mock_pool.return_value = MagicMock()
        mock_get_doc.return_value = None

        result = await get_document(99999)
        assert result == "Not found or not accessible."


@pytest.mark.asyncio
async def test_get_document_json_structure():
    with patch("src.precedent.mcp_server.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.mcp_server.retrieval.get_document", new_callable=AsyncMock) as mock_get_doc:
        mock_pool.return_value = MagicMock()
        mock_get_doc.return_value = {
            "id": 42,
            "source": "cuad",
            "external_id": "test_contract.pdf",
            "title": "Test Contract",
            "doc_type": "License Agreement",
            "parties": ["Party A", "Party B"],
            "filing_date": "2020-01-01",
            "raw_text": "Full text of contract...",
            "clauses": [
                {
                    "clause_id": 101,
                    "clause_type": "Governing Law",
                    "clause_text": "Delaware law applies.",
                }
            ],
        }

        result = await get_document(42)
        parsed = json.loads(result)
        assert parsed["id"] == 42
        assert parsed["title"] == "Test Contract"
        assert len(parsed["clauses"]) == 1
        assert parsed["clauses"][0]["clause_id"] == 101


@pytest.mark.asyncio
async def test_ask_precedent_grounded_answer():
    with patch("src.precedent.mcp_server.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.mcp_server.agent.run_query", new_callable=AsyncMock) as mock_run_query:
        mock_pool.return_value = MagicMock()
        mock_run_query.return_value = AgentResult(
            answer="Governing law is Delaware [doc:42].",
            skill_used="find-precedent",
            cited_doc_ids=[42],
            grounded=True,
            input_tokens=150,
            output_tokens=60,
            latency_ms=450,
        )

        result = await ask_precedent("What is the governing law?")
        assert "[doc:42]" in result
        assert "[note: this answer did not pass the citation check" not in result


@pytest.mark.asyncio
async def test_ask_precedent_ungrounded_answer_appends_warning():
    with patch("src.precedent.mcp_server.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.mcp_server.agent.run_query", new_callable=AsyncMock) as mock_run_query:
        mock_pool.return_value = MagicMock()
        mock_run_query.return_value = AgentResult(
            answer="General answer without validated citations.",
            skill_used="find-precedent",
            cited_doc_ids=[],
            grounded=False,
            input_tokens=150,
            output_tokens=40,
            latency_ms=400,
        )

        result = await ask_precedent("Explain general concepts.")
        assert "General answer without validated citations." in result
        assert "[note: this answer did not pass the citation check — verify independently]" in result
