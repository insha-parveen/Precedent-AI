"""Local SQLite storage for local-first mode.

Mirrors the retrieval.py interface but uses SQLite + local embeddings.

Importers/callers: None yet (new file). Will be called from:
- src/precedent/mcp_server.py (new MCP tools: ingest_directory, watch_folder)
- src/precedent/watcher.py (folder watcher daemon)
- src/precedent/cli.py (watch command)

Affected API (new functions):
- init_local_db() - initialize schema
- local_hybrid_search() - hybrid vector + full-text search
- local_get_document() - fetch document with clauses
- local_upsert_document() - insert/update document with chunks
- local_get_existing_external_ids() - for resumption
- local_delete_document() - delete with permission check
- _compute_external_id() - stable ID from file path + mtime

Data schemas:
- documents table: id, source, external_id, title, doc_type, parties (JSON), filing_date, raw_text, access_group, source_url, created_at
- clauses table: id, document_id, clause_type, clause_text, char_start, char_end, embedding (BLOB float32), access_group, created_at
- clauses_fts virtual table for full-text search

User instruction: "To let a client 'point Claude at their desktop folders': 1. New MCP tools — ingest_directory(path, access_group), watch_folder(path) 2. File watcher/ingestion pipeline — Background process that monitors folders 3. Local-first mode — SQLite + local embeddings (no Supabase) for air-gapped use 4. Security model — The MCP server runs with the user's file permissions; dangerous if exposed remotely"
"""

import json
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from .local_embed import embed_local, embed_local_async
from .config import settings
from .ingestion.chunking import ClauseChunk
from .classifier import classify_batch as classify_clauses_batch
from .db import get_pool  # For type compatibility only


# Document and clause data structures (matching retrieval.py)
class DocumentWithClauses:
    def __init__(
        self,
        document_id: int,
        source: str,
        external_id: str,
        title: str,
        doc_type: str,
        parties: List[str],
        filing_date: Optional[str],
        raw_text: str,
        access_group: str,
        source_url: Optional[str],
        clauses: List["ClauseResult"],
    ):
        self.document_id = document_id
        self.source = source
        self.external_id = external_id
        self.title = title
        self.doc_type = doc_type
        self.parties = parties
        self.filing_date = filing_date
        self.raw_text = raw_text
        self.access_group = access_group
        self.source_url = source_url
        self.clauses = clauses


class ClauseResult:
    def __init__(
        self,
        clause_id: int,
        document_id: int,
        clause_type: str,
        clause_text: str,
        char_start: int,
        char_end: int,
        access_group: str,
        score: float,
        doc_title: str,
    ):
        self.clause_id = clause_id
        self.document_id = document_id
        self.clause_type = clause_type
        self.clause_text = clause_text
        self.char_start = char_start
        self.char_end = char_end
        self.access_group = access_group
        self.score = score
        self.doc_title = doc_title


class DocumentInput:
    def __init__(
        self,
        source: str,
        external_id: str,
        title: str,
        doc_type: str,
        parties: List[str],
        raw_text: str,
        access_group: str,
    ):
        self.source = source
        self.external_id = external_id
        self.title = title
        self.doc_type = doc_type
        self.parties = parties
        self.raw_text = raw_text
        self.access_group = access_group


def _get_connection() -> sqlite3.Connection:
    """Get a connection to the local SQLite database."""
    db_path = Path(settings.local_db_path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


async def init_local_db() -> None:
    """Initialize the local SQLite database schema."""
    conn = _get_connection()
    try:
        # Documents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                parties JSON,
                filing_date TEXT,
                raw_text TEXT NOT NULL,
                access_group TEXT NOT NULL,
                source_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Clauses table with BLOB for embeddings
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clauses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                clause_type TEXT NOT NULL,
                clause_text TEXT NOT NULL,
                char_start INTEGER NOT NULL,
                char_end INTEGER NOT NULL,
                embedding BLOB NOT NULL,  -- Float32 array as BLOB
                access_group TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)

        # Indexes for performance
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_clauses_document_id ON clauses(document_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_clauses_access_group ON clauses(access_group)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_access_group ON documents(access_group)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_external_id ON documents(external_id)
        """)

        # FTS5 virtual table for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS clauses_fts USING fts5(
                clause_text,
                content='clauses',
                content_rowid='id'
            )
        """)

        # Triggers to keep FTS in sync
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS clauses_ai AFTER INSERT ON clauses BEGIN
                INSERT INTO clauses_fts(rowid, clause_text) VALUES (new.id, new.clause_text);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS clauses_ad AFTER DELETE ON clauses BEGIN
                INSERT INTO clauses_fts(clauses_fts, rowid, clause_text) VALUES('delete', old.id, old.clause_text);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS clauses_au AFTER UPDATE ON clauses BEGIN
                INSERT INTO clauses_fts(clauses_fts, rowid, clause_text) VALUES('delete', old.id, old.clause_text);
                INSERT INTO clauses_fts(rowid, clause_text) VALUES (new.id, new.clause_text);
            END
        """)

        conn.commit()
    finally:
        conn.close()


def _blob_to_embedding(blob: bytes) -> List[float]:
    """Convert BLOB back to list of floats."""
    import array
    return list(array.array('f', blob))


def _embedding_to_blob(embedding: List[float]) -> bytes:
    """Convert list of floats to BLOB for storage."""
    import array
    return array.array('f', embedding).tobytes()


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


async def local_hybrid_search(query: str, access_group: str, k: int = 10) -> List[ClauseResult]:
    """Perform hybrid search (vector + full-text) using reciprocal rank fusion."""
    # Get vector search results
    vector_results = await _local_vector_search(query, access_group, k * 2)  # Get more for fusion

    # Get full-text search results
    fts_results = await _local_fts_search(query, access_group, k * 2)

    # Combine using reciprocal rank fusion
    combined = _reciprocal_rank_fusion(vector_results, fts_results, k)

    return combined


async def _local_vector_search(query: str, access_group: str, k: int) -> List[ClauseResult]:
    """Vector search using local embeddings."""
    # Embed the query
    query_embedding = embed_local([query])[0]

    conn = _get_connection()
    try:
        # Get all clauses for the access group (for small corpora, we can do brute force)
        # In production, we might want to use sqlite-vec or similar for better performance
        rows = conn.execute("""
            SELECT c.id, c.document_id, c.clause_type, c.clause_text,
                   c.char_start, c.char_end, c.embedding, c.access_group,
                   d.title as doc_title
            FROM clauses c
            JOIN documents d ON c.document_id = d.id
            WHERE c.access_group = ?
        """, (access_group,)).fetchall()

        # Compute similarities
        scored_results = []
        for row in rows:
            embedding_blob = row['embedding']
            embedding = _blob_to_embedding(embedding_blob)
            similarity = _cosine_similarity(query_embedding, embedding)

            scored_results.append((
                similarity,
                ClauseResult(
                    clause_id=row['id'],
                    document_id=row['document_id'],
                    clause_type=row['clause_type'],
                    clause_text=row['clause_text'],
                    char_start=row['char_start'],
                    char_end=row['char_end'],
                    access_group=row['access_group'],
                    score=similarity,
                    doc_title=row['doc_title']
                )
            ))

        # Sort by score descending and take top k
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [result for _, result in scored_results[:k]]
    finally:
        conn.close()


async def _local_fts_search(query: str, access_group: str, k: int) -> List[ClauseResult]:
    """Full-text search using FTS5."""
    conn = _get_connection()
    try:
        # Use FTS5 to search for the query
        rows = conn.execute("""
            SELECT c.id, c.document_id, c.clause_type, c.clause_text,
                   c.char_start, c.char_end, c.access_group,
                   d.title as doc_title,
                   bm25(clauses_fts) as rank_score
            FROM clauses_fts
            JOIN clauses c ON clauses_fts.rowid = c.id
            JOIN documents d ON c.document_id = d.id
            WHERE clauses_fts MATCH ? AND c.access_group = ?
            ORDER BY rank_score
            LIMIT ?
        """, (query, access_group, k)).fetchall()

        results = []
        for row in rows:
            # Convert BM25 score to a positive similarity score (lower BM25 is better)
            # We'll use a simple transformation for now
            score = 1.0 / (1.0 + abs(row['rank_score']))

            results.append(ClauseResult(
                clause_id=row['id'],
                document_id=row['document_id'],
                clause_type=row['clause_type'],
                clause_text=row['clause_text'],
                char_start=row['char_start'],
                char_end=row['char_end'],
                access_group=row['access_group'],
                score=score,
                doc_title=row['doc_title']
            ))

        return results
    finally:
        conn.close()


def _reciprocal_rank_fusion(
    vector_results: List[ClauseResult],
    fts_results: List[ClauseResult],
    k: int,
    k_const: int = 60
) -> List[ClauseResult]:
    """Combine ranked results using reciprocal rank fusion."""
    # Create maps for fast lookup
    vector_ranks = {result.clause_id: i + 1 for i, result in enumerate(vector_results)}
    fts_ranks = {result.clause_id: i + 1 for i, result in enumerate(fts_results)}

    # Get all unique clause IDs
    all_ids = set(vector_ranks.keys()) | set(fts_ranks.keys())

    # Compute RRF scores
    scored_results = []
    for clause_id in all_ids:
        vector_rank = vector_ranks.get(clause_id, len(vector_results) + k_const + 1)
        fts_rank = fts_ranks.get(clause_id, len(fts_results) + k_const + 1)

        rrf_score = 1/(k_const + vector_rank) + 1/(k_const + fts_rank)

        # Find the result object (prefer vector result if available, otherwise FTS)
        result_obj = None
        for result in vector_results:
            if result.clause_id == clause_id:
                result_obj = result
                break
        if result_obj is None:
            for result in fts_results:
                if result.clause_id == clause_id:
                    result_obj = result
                    break

        if result_obj:
            # Update score with fused score
            result_obj.score = rrf_score
            scored_results.append((rrf_score, result_obj))

    # Sort by RRF score descending and take top k
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [result for _, result in scored_results[:k]]


async def local_get_document(document_id: int, access_group: str) -> Optional[DocumentWithClauses]:
    """Fetch a document with its clauses by ID."""
    conn = _get_connection()
    try:
        # Get document
        doc_row = conn.execute("""
            SELECT id, source, external_id, title, doc_type, parties,
                   filing_date, raw_text, access_group, source_url, created_at
            FROM documents
            WHERE id = ? AND access_group = ?
        """, (document_id, access_group)).fetchone()

        if not doc_row:
            return None

        # Get clauses for this document
        clause_rows = conn.execute("""
            SELECT id, document_id, clause_type, clause_text, char_start, char_end, access_group
            FROM clauses
            WHERE document_id = ? AND access_group = ?
            ORDER BY char_start
        """, (document_id, access_group)).fetchall()

        # Build clauses list
        clauses = []
        for clause_row in clause_rows:
            clauses.append(ClauseResult(
                clause_id=clause_row['id'],
                document_id=clause_row['document_id'],
                clause_type=clause_row['clause_type'],
                clause_text=clause_row['clause_text'],
                char_start=clause_row['char_start'],
                char_end=clause_row['char_end'],
                access_group=clause_row['access_group'],
                score=0.0,  # Score not relevant for direct fetch
                doc_title=doc_row['title']
            ))

        return DocumentWithClauses(
            document_id=doc_row['id'],
            source=doc_row['source'],
            external_id=doc_row['external_id'],
            title=doc_row['title'],
            doc_type=doc_row['doc_type'],
            parties=json.loads(doc_row['parties']) if doc_row['parties'] else [],
            filing_date=doc_row['filing_date'],
            raw_text=doc_row['raw_text'],
            access_group=doc_row['access_group'],
            source_url=doc_row['source_url'],
            clauses=clauses
        )
    finally:
        conn.close()


async def local_upsert_document(
    source: str,
    external_id: str,
    title: str,
    doc_type: str,
    parties: List[str],
    raw_text: str,
    access_group: str,
    chunks: List[ClauseChunk],
    chunk_types: List[str],
) -> int:
    """Insert or update a document with its clauses.

    Returns the document ID.
    """
    conn = _get_connection()
    try:
        # Check if document already exists
        existing = conn.execute(
            "SELECT id FROM documents WHERE external_id = ? AND source = ?",
            (external_id, source)
        ).fetchone()

        if existing:
            # Update existing document
            document_id = existing['id']

            # Delete existing clauses
            conn.execute("DELETE FROM clauses WHERE document_id = ?", (document_id,))

            # Update document metadata
            conn.execute("""
                UPDATE documents
                SET title = ?, doc_type = ?, parties = ?, raw_text = ?,
                    access_group = ?, created_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                title, doc_type, json.dumps(parties), raw_text,
                access_group, document_id
            ))
        else:
            # Insert new document
            cursor = conn.execute("""
                INSERT INTO documents (
                    source, external_id, title, doc_type, parties,
                    raw_text, access_group
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                source, external_id, title, doc_type, json.dumps(parties),
                raw_text, access_group
            ))
            document_id = cursor.lastrowid

        # Insert clauses with embeddings
        if chunks:
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await embed_local_async(chunk_texts)

            clause_data = []
            for i, (chunk, embedding, chunk_type) in enumerate(zip(chunks, embeddings, chunk_types)):
                clause_data.append((
                    document_id,
                    chunk_type,
                    chunk.text,
                    chunk.char_start,
                    chunk.char_end,
                    _embedding_to_blob(embedding),
                    access_group
                ))

            conn.executemany("""
                INSERT INTO clauses (
                    document_id, clause_type, clause_text, char_start, char_end,
                    embedding, access_group
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, clause_data)

        conn.commit()
        return document_id
    finally:
        conn.close()


async def local_get_existing_external_ids(source: str) -> List[str]:
    """Get all existing external IDs for a source (used for deduplication)."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT external_id FROM documents WHERE source = ?",
            (source,)
        ).fetchall()
        return [row['external_id'] for row in rows]
    finally:
        conn.close()


async def local_delete_document(document_id: int, access_group: str) -> bool:
    """Delete a document and its clauses if access_group matches.

    Returns True if deleted, False if not found or access mismatch.
    """
    conn = _get_connection()
    try:
        # Check if document exists and matches access_group
        doc = conn.execute(
            "SELECT id FROM documents WHERE id = ? AND access_group = ?",
            (document_id, access_group)
        ).fetchone()

        if not doc:
            return False

        # Delete document (cascades to clauses via foreign key)
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def _compute_external_id(filepath: Path) -> str:
    """Compute a stable external ID from file path, modification time, and size."""
    stat = filepath.stat()
    # Use path + mtime + size for stability across moves but sensitivity to changes
    content = f"{filepath.resolve()}:{stat.st_mtime}:{stat.st_size}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()