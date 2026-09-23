import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from src.precedent import cli

@pytest.mark.asyncio
async def test_search_cmd():
    with patch("src.precedent.cli.get_pool", new_callable=AsyncMock), \
         patch("src.precedent.cli.retrieval.hybrid_search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            MagicMock(document_id=1, clause_id=101, clause_type="Test", doc_title="Doc1", clause_text="Sample text")
        ]
        args = MagicMock(query="test query")

        await cli.search_cmd(args)
        mock_search.assert_called_once()

@pytest.mark.asyncio
async def test_ask_cmd():
    with patch("src.precedent.cli.get_pool", new_callable=AsyncMock), \
         patch("src.precedent.cli.agent.run_query", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MagicMock(answer="Sample answer", grounded=True)
        args = MagicMock(query="test question")

        await cli.ask_cmd(args)
        mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_doc_cmd_not_found():
    with patch("src.precedent.cli.get_pool", new_callable=AsyncMock), \
         patch("src.precedent.cli.retrieval.get_document", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        args = MagicMock(document_id=999)

        with pytest.raises(SystemExit):
            await cli.doc_cmd(args)
