"""The index layer.

Two rules for anything added to this file:
1. Every query filters on access_group. There is no code path that bypasses it, even
   for convenience during debugging — that's the entire point of this project.
2. This module does retrieval only. It never calls Claude and never decides what an
   answer should say — that's agent.py's job. Keeping this boundary is what lets the
   eval harness score retrieval in isolation from generation quality.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import asyncpg
import voyageai

from .config import settings

_voyage = voyageai.Client(api_key=settings.voyage_api_key)


@dataclass
class ClauseResult:
    clause_id: int
    document_id: int
    clause_type: str
    clause_text: str
    doc_title: str
    doc_type: str | None
    parties: list[str] = field(default_factory=list)
    score: float = 0.0


def embed_query(text: str) -> list[float]:
    """Embed a query string. input_type='query' matters — Voyage prepends a different
    instruction prefix for queries vs. documents, and mixing them up quietly degrades
    retrieval quality without throwing an error, which makes it an easy mistake to miss.
    """
    result = _voyage.embed([text], model=settings.embedding_model, input_type="query")
    return result.embeddings[0]


async def hybrid_search(
    pool: asyncpg.Pool,
    query_text: str,
    *,
    access_groups: list[str],
    clause_type: str | None = None,
    doc_type: str | None = None,
    parties: list[str] | None = None,
    limit: int = 10,
) -> list[ClauseResult]:
    """Combine vector similarity and keyword (full-text) search via reciprocal rank
    fusion, then apply structured filters. access_groups is required and non-optional —
    callers must pass the caller's actual entitlements, never a wildcard.
    """
    if not access_groups:
        return []

    query_embedding = embed_query(query_text)

    conditions = ["c.access_group = ANY($3::text[])"]
    params: list = [query_embedding, query_text, access_groups]

    if clause_type:
        params.append(clause_type)
        conditions.append(f"c.clause_type = ${len(params)}")
    if doc_type:
        params.append(doc_type)
        conditions.append(f"d.doc_type = ${len(params)}")
    if parties:
        params.append(parties)
        conditions.append(f"d.parties && ${len(params)}::text[]")

    where_clause = " AND ".join(conditions)
    params.append(limit)
    limit_param = f"${len(params)}"

    # Reciprocal rank fusion (k=60, the standard default): rank by vector distance and
    # by full-text rank separately, then combine the reciprocal ranks. This is a simple,
    # well-established way to blend semantic and keyword search without having to tune
    # a fragile weighted-sum coefficient by hand.
    sql = f"""
        WITH vector_ranked AS (
            SELECT c.id, ROW_NUMBER() OVER (ORDER BY c.embedding <=> $1) AS rnk
            FROM clauses c
            JOIN documents d ON d.id = c.document_id
            WHERE {where_clause}
        ),
        text_ranked AS (
            SELECT c.id, ROW_NUMBER() OVER (
                ORDER BY ts_rank(c.tsv, plainto_tsquery('english', $2)) DESC
            ) AS rnk
            FROM clauses c
            JOIN documents d ON d.id = c.document_id
            WHERE {where_clause} AND c.tsv @@ plainto_tsquery('english', $2)
        ),
        fused AS (
            SELECT id, SUM(1.0 / (60 + rnk)) AS score
            FROM (
                SELECT id, rnk FROM vector_ranked
                UNION ALL
                SELECT id, rnk FROM text_ranked
            ) both_ranks
            GROUP BY id
        )
        SELECT
            c.id AS clause_id, c.document_id, c.clause_type, c.clause_text,
            d.title AS doc_title, d.doc_type, d.parties, f.score
        FROM fused f
        JOIN clauses c ON c.id = f.id
        JOIN documents d ON d.id = c.document_id
        ORDER BY f.score DESC
        LIMIT {limit_param};
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)

    return [
        ClauseResult(
            clause_id=r["clause_id"],
            document_id=r["document_id"],
            clause_type=r["clause_type"],
            clause_text=r["clause_text"],
            doc_title=r["doc_title"],
            doc_type=r["doc_type"],
            parties=list(r["parties"] or []),
            score=float(r["score"]),
        )
        for r in rows
    ]


async def get_document(
    pool: asyncpg.Pool, document_id: int, *, access_groups: list[str]
) -> dict | None:
    """Fetch a full document plus all its labeled clauses, permission-checked."""
    async with pool.acquire() as conn:
        doc = await conn.fetchrow(
            """
            SELECT id, source, external_id, title, doc_type, parties, filing_date,
                   raw_text, access_group
            FROM documents
            WHERE id = $1 AND access_group = ANY($2::text[])
            """,
            document_id,
            access_groups,
        )
        if doc is None:
            return None

        clauses = await conn.fetch(
            """
            SELECT id AS clause_id, clause_type, clause_text, char_start, char_end
            FROM clauses
            WHERE document_id = $1
            ORDER BY char_start NULLS LAST
            """,
            document_id,
        )

    return {**dict(doc), "clauses": [dict(c) for c in clauses]}
