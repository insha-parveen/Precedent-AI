"""FastAPI endpoint unit tests (offline, no database or network needed)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.precedent.agent import AgentResult
from src.precedent.retrieval import ClauseResult


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from src.precedent.api import app
    return TestClient(app)


def test_chat_endpoint_returns_grounded_answer(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.agent.run_query", new_callable=AsyncMock) as mock_run_query:
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

        response = client.post("/api/chat", json={"query": "What is the governing law?"})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Governing law is Delaware [doc:42]."
        assert data["skill_used"] == "find-precedent"
        assert data["cited_doc_ids"] == [42]
        assert data["grounded"] is True
        assert data["input_tokens"] == 150
        assert data["output_tokens"] == 60
        assert data["latency_ms"] == 450


def test_chat_endpoint_ungrounded_answer(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.agent.run_query", new_callable=AsyncMock) as mock_run_query:
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

        response = client.post("/api/chat", json={"query": "Explain general concepts."})

        assert response.status_code == 200
        data = response.json()
        assert data["grounded"] is False
        assert data["cited_doc_ids"] == []


def test_ask_endpoint_alias(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.agent.run_query", new_callable=AsyncMock) as mock_run_query:
        mock_pool.return_value = MagicMock()
        mock_run_query.return_value = AgentResult(
            answer="Answer [doc:1].",
            skill_used="negotiation-check",
            cited_doc_ids=[1],
            grounded=True,
            input_tokens=100,
            output_tokens=50,
            latency_ms=300,
        )

        response = client.post("/api/ask", json={"query": "How did Party X negotiate?"})

        assert response.status_code == 200
        data = response.json()
        assert data["skill_used"] == "negotiation-check"


def test_search_endpoint_returns_results(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.retrieval.hybrid_search", new_callable=AsyncMock) as mock_search:
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
            ),
            ClauseResult(
                clause_id=102,
                document_id=43,
                clause_type="Governing Law",
                clause_text="The laws of California shall apply.",
                doc_title="License Agreement.pdf",
                doc_type="License Agreement",
                parties=["Gamma Inc", "Delta LLC"],
                score=0.87,
            ),
        ]

        response = client.post("/api/search", json={
            "query": "governing law",
            "clause_type": "Governing Law",
            "limit": 5
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["clause_id"] == 101
        assert data["results"][0]["document_id"] == 42
        assert data["results"][0]["clause_type"] == "Governing Law"
        assert "Delaware" in data["results"][0]["clause_text"]
        assert data["results"][0]["score"] == 0.95
        assert data["results"][1]["score"] == 0.87


def test_search_endpoint_empty_results(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.retrieval.hybrid_search", new_callable=AsyncMock) as mock_search:
        mock_pool.return_value = MagicMock()
        mock_search.return_value = []

        response = client.post("/api/search", json={"query": "nonexistent clause"})

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []


def test_search_endpoint_with_filters(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.retrieval.hybrid_search", new_callable=AsyncMock) as mock_search:
        mock_pool.return_value = MagicMock()
        mock_search.return_value = [
            ClauseResult(
                clause_id=201,
                document_id=50,
                clause_type="Non-Compete",
                clause_text="Non-compete clause text...",
                doc_title="Employment Agreement.pdf",
                doc_type="Employment Agreement",
                parties=["Employer Inc", "Employee Name"],
                score=0.92,
            )
        ]

        response = client.post("/api/search", json={
            "query": "non-compete",
            "clause_type": "Non-Compete",
            "doc_type": "Employment Agreement",
            "parties": ["Employer Inc"],
            "limit": 10
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        mock_search.assert_called_once()
        # Verify filters were passed
        call_args = mock_search.call_args
        assert call_args.kwargs["clause_type"] == "Non-Compete"
        assert call_args.kwargs["doc_type"] == "Employment Agreement"
        assert call_args.kwargs["parties"] == ["Employer Inc"]
        assert call_args.kwargs["limit"] == 10


def test_document_endpoint_returns_document(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.retrieval.get_document", new_callable=AsyncMock) as mock_get_doc:
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

        response = client.get("/api/document/42")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == 42
        assert data["doc_title"] == "Test Contract"
        assert data["doc_type"] == "License Agreement"
        assert data["parties"] == ["Party A", "Party B"]
        assert data["source"] == "cuad"
        assert len(data["clauses"]) == 1
        assert data["clauses"][0]["clause_id"] == 101
        assert data["clauses"][0]["clause_type"] == "Governing Law"
        assert data["jurisdiction"] is None


def test_document_endpoint_not_found(client):
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.retrieval.get_document", new_callable=AsyncMock) as mock_get_doc:
        mock_pool.return_value = MagicMock()
        mock_get_doc.return_value = None

        response = client.get("/api/document/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found"


# --- Auth integration tests: token-derived access_groups must reach retrieval ---

def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _valid_token(roles: list[str]) -> str:
    import jwt
    return jwt.encode(
        {"sub": "user123", "username": "tester", "roles": roles},
        "test-secret",
        algorithm="HS256",
    )


def test_chat_propagates_token_access_groups_to_agent(client):
    """access_groups from the JWT must reach agent.run_query — never client input."""
    token = _valid_token(["legal_team"])
    with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
         patch("src.precedent.api.agent.run_query", new_callable=AsyncMock) as mock_run_query, \
         patch("src.precedent.auth.settings") as mock_settings:
        mock_pool.return_value = MagicMock()
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        mock_settings.jwt_resource_identifier = "precedent"
        mock_settings.default_role = "public"
        mock_settings.role_to_access_groups = {"legal_team": ["public", "internal"]}
        mock_settings.always_include_public = True
        mock_run_query.return_value = AgentResult(
            answer="ok [doc:1].", skill_used="find-precedent",
            cited_doc_ids=[1], grounded=True,
            input_tokens=10, output_tokens=5, latency_ms=10,
        )

        response = client.post(
            "/api/chat", json={"query": "governing law?"},
            headers=_auth_headers(token),
        )

        assert response.status_code == 200
        call_args = mock_run_query.call_args
        assert call_args.kwargs["access_groups"] == ["public", "internal"]


def test_production_mode_requires_token(client):
    """Without PRECEDENT_ENV=dev, a missing/invalid token must be 401, not a mock user."""
    from src.precedent import api as api_module

    token = _valid_token(["legal_team"])
    with patch.object(api_module.settings, "precedent_env", "production"), \
         patch("src.precedent.auth.settings") as mock_auth_settings:
        mock_auth_settings.jwt_secret_key = "test-secret"
        mock_auth_settings.jwt_algorithm = "HS256"
        mock_auth_settings.jwt_issuer = None
        mock_auth_settings.jwt_audience = None
        mock_auth_settings.jwt_resource_identifier = "precedent"
        mock_auth_settings.default_role = "public"
        mock_auth_settings.role_to_access_groups = {"legal_team": ["public", "internal"]}
        mock_auth_settings.always_include_public = True

        # No token at all
        response = client.post("/api/chat", json={"query": "q"})
        assert response.status_code == 401

        # Invalid token also 401
        response = client.post(
            "/api/chat", json={"query": "q"},
            headers=_auth_headers("not-a-jwt"),
        )
        assert response.status_code == 401

        # Valid token passes through to the agent (mock pool so no DB hit)
        with patch("src.precedent.api.get_pool", new_callable=AsyncMock) as mock_pool, \
             patch("src.precedent.api.agent.run_query", new_callable=AsyncMock) as mock_run_query:
            mock_pool.return_value = MagicMock()
            mock_run_query.return_value = AgentResult(
                answer="ok [doc:1].", skill_used="find-precedent",
                cited_doc_ids=[1], grounded=True,
                input_tokens=10, output_tokens=5, latency_ms=10,
            )
            response = client.post(
                "/api/chat", json={"query": "q"},
                headers=_auth_headers(token),
            )
            assert response.status_code == 200


def test_invalid_token_signature_gets_401(client):
    """A token signed with the wrong secret must be a 401 at the API boundary."""
    import jwt as jwt_mod
    bad = jwt_mod.encode({"sub": "attacker", "roles": ["admin"]}, "wrong-secret", algorithm="HS256")

    with patch("src.precedent.api.get_pool", new_callable=AsyncMock), \
         patch("src.precedent.api.agent.run_query", new_callable=AsyncMock) as mock_run_query:
        response = client.post(
            "/api/chat", json={"query": "q"},
            headers=_auth_headers(bad),
        )
        # Real settings loads the real .env JWT secret, so signature check actually runs.
        assert response.status_code == 401
        mock_run_query.assert_not_called()