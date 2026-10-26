"""Database insert helpers for ingestion pipelines."""
from __future__ import annotations

import asyncpg
from datetime import date
from typing import Optional


async def insert_document(
    pool: asyncpg.Pool,
    *,
    source: str,
    external_id: str,
    title: str,
    doc_type: Optional[str] = None,
    parties: Optional[list[str]] = None,
    filing_date: Optional[date] = None,
    raw_text: str = "",
    access_group: str = "public",
    source_url: Optional[str] = None,
) -> int:
    """Insert or update a document and return its ID.

    Args:
        pool: Database connection pool
        source: Source identifier ('cuad', 'edgar', 'custom')
        external_id: Unique identifier within the source
        title: Document title
        doc_type: Document type (e.g., 'MSA', 'NDA', 'Credit Agreement')
        parties: List of party names
        filing_date: Filing/effective date
        raw_text: Full document text (truncated if needed)
        access_group: Access group for permission filtering
        source_url: Optional URL to source

    Returns:
        Document ID
    """
    async with pool.acquire() as conn:
        doc_id = await conn.fetchval(
            """
            INSERT INTO documents (source, external_id, title, doc_type, parties, filing_date, raw_text, access_group, source_url)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (source, external_id) DO UPDATE SET
                title = EXCLUDED.title,
                doc_type = EXCLUDED.doc_type,
                parties = EXCLUDED.parties,
                filing_date = EXCLUDED.filing_date,
                raw_text = EXCLUDED.raw_text,
                access_group = EXCLUDED.access_group,
                source_url = EXCLUDED.source_url
            RETURNING id
            """,
            source,
            external_id,
            title,
            doc_type,
            parties or [],
            filing_date,
            raw_text,
            access_group,
            source_url,
        )
    return doc_id


async def insert_clauses(
    pool: asyncpg.Pool,
    *,
    document_id: int,
    clauses: list[dict],
    access_group: str = "public",
) -> int:
    """Insert multiple clauses for a document.

    Args:
        pool: Database connection pool
        document_id: Parent document ID
        clauses: List of dicts with keys: clause_type, clause_text, char_start, char_end, embedding
        access_group: Access group for permission filtering

    Returns:
        Number of clauses inserted
    """
    if not clauses:
        return 0

    async with pool.acquire() as conn:
        async with conn.transaction():
            for clause in clauses:
                await conn.execute(
                    """
                    INSERT INTO clauses (document_id, clause_type, clause_text, char_start, char_end, embedding, access_group)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    document_id,
                    clause["clause_type"],
                    clause["clause_text"],
                    clause.get("char_start"),
                    clause.get("char_end"),
                    clause.get("embedding"),
                    access_group,
                )
    return len(clauses)


async def get_existing_external_ids(pool: asyncpg.Pool, source: str) -> set[str]:
    """Get all external_ids already ingested for a source (for resumption).

    Args:
        pool: Database connection pool
        source: Source identifier

    Returns:
        Set of external_ids
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT external_id FROM documents WHERE source = $1",
            source,
        )
    return {row["external_id"] for row in rows}