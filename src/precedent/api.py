from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from .middleware.rate_limiting import RateLimitingMiddleware
from .middleware.metrics import metrics_endpoint
from .middleware.logging import LoggingMiddleware
from . import agent, retrieval
from .auth import get_current_user, AuthenticatedUser
from .config import settings
from .db import get_pool
from .exceptions import AuthenticationError

# Security
security = HTTPBearer(auto_error=False)

app = FastAPI(title="Precedent API", description="API backing the Milestone 6 Web UI")

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=settings.rate_limit_requests_per_minute)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local Next.js dev
    allow_credentials=False,  # "*" origin + credentials is unsafe
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics endpoint
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """Extract and validate user from Bearer token.

    Args:
        credentials: HTTP authorization credentials from request

    Returns:
        AuthenticatedUser object

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        # In development mode, we allow no auth for local testing (dev/development)
        if settings.precedent_env in ("development", "dev"):
            from .auth import create_mock_user_for_dev
            return create_mock_user_for_dev()
        raise HTTPException(
            status_code=401,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return get_current_user(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

class ChatRequest(BaseModel):
    query: str

class ClauseResponse(BaseModel):
    clause_id: int
    clause_type: str | None
    clause_text: str


class DocumentResponse(BaseModel):
    document_id: int
    doc_title: str
    doc_type: str | None
    parties: list[str]
    jurisdiction: str | None
    filing_date: str | None
    source: str
    clauses: list[ClauseResponse]


class ChatResponse(BaseModel):
    answer: str
    skill_used: str | None
    cited_doc_ids: list[int]
    grounded: bool
    input_tokens: int
    output_tokens: int
    latency_ms: int


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


class SearchRequest(BaseModel):
    query: str
    clause_type: str | None = None
    doc_type: str | None = None
    parties: list[str] | None = None
    limit: int = 10


class SearchResult(BaseModel):
    clause_id: int
    document_id: int
    clause_type: str
    clause_text: str
    doc_title: str
    doc_type: str | None
    parties: list[str]
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


@app.get("/health", response_model=HealthResponse)
async def health_endpoint():
    """Health check endpoint for container orchestration."""
    return HealthResponse(status="healthy")


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_from_token),
):
    """Answers a contract question in natural language."""
    pool = await get_pool()
    result = await agent.run_query(pool, req.query, access_groups=current_user.access_groups)
    return {
        "answer": result.answer,
        "skill_used": result.skill_used,
        "cited_doc_ids": result.cited_doc_ids,
        "grounded": result.grounded,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "latency_ms": result.latency_ms
    }


# Alias for /api/ask to match MCP tool naming
@app.post("/api/ask", response_model=ChatResponse)
async def ask_endpoint(
    req: ChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_from_token),
):
    """Alias for /api/chat - answers a contract question in natural language."""
    pool = await get_pool()
    result = await agent.run_query(pool, req.query, access_groups=current_user.access_groups)
    return {
        "answer": result.answer,
        "skill_used": result.skill_used,
        "cited_doc_ids": result.cited_doc_ids,
        "grounded": result.grounded,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "latency_ms": result.latency_ms
    }


@app.post("/api/search", response_model=SearchResponse)
async def search_endpoint(
    req: SearchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user_from_token),
):
    """Hybrid semantic + keyword search over clause-level contract text."""
    pool = await get_pool()
    results = await retrieval.hybrid_search(
        pool,
        req.query,
        access_groups=current_user.access_groups,
        clause_type=req.clause_type,
        doc_type=req.doc_type,
        parties=req.parties,
        limit=req.limit,
    )
    return {
        "results": [
            SearchResult(
                clause_id=r.clause_id,
                document_id=r.document_id,
                clause_type=r.clause_type,
                clause_text=r.clause_text,
                doc_title=r.doc_title,
                doc_type=r.doc_type,
                parties=r.parties,
                score=r.score,
            )
            for r in results
        ]
    }

@app.get("/api/document/{doc_id}", response_model=DocumentResponse)
async def get_document_endpoint(
    doc_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user_from_token),
):
    """Fetch a document by ID, shaped to what the web UI expects.

    retrieval.get_document returns raw DB column names (id, title, ...), but the
    frontend's DocumentResponse contract uses document_id/doc_title. Mapping here
    keeps the wire format stable and stops the drawer rendering "undefined".

    jurisdiction is not a column on documents, so it is always null; the field
    stays in the contract so the client can show it if a source gains one.
    """
    pool = await get_pool()
    doc = await retrieval.get_document(pool, doc_id, access_groups=current_user.access_groups)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "document_id": doc["id"],
        "doc_title": doc["title"],
        "doc_type": doc.get("doc_type"),
        "parties": doc.get("parties") or [],
        "jurisdiction": None,
        "filing_date": doc.get("filing_date"),
        "source": doc["source"],
        "clauses": doc.get("clauses") or [],
    }
