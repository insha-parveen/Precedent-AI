"""MCP server. Run with: python -m src.precedent.mcp_server

Built on `mcp` 2.x's MCPServer (the v2 rename of what used to be called FastMCP —
if you're reading a tutorial that imports `from mcp.server.fastmcp import FastMCP`,
it's written against mcp 1.x; `pip show mcp` on this project's installed version first
if anything here stops matching what you see in the SDK's own error messages, they're
unusually good about pointing at the migration guide).

Exposes FIVE tools:
- ask_precedent   Runs the full agent harness (route -> retrieve -> verify -> cite).
                   This is the primary tool — prefer it. It returns an answer that has
                   already been through the citation-or-refuse check, regardless of
                   which external model is calling it.
- search_contracts / get_document   Raw retrieval, for a caller that wants to reason
                   over sources itself rather than trust our harness's synthesis.
- ingest_directory   Ingest contracts from a local directory (local-first or cloud)
- watch_folder       Register a folder for background watching (local-first daemon)

access_groups is hardcoded to ["public"] here because this demo corpus only has one
group. A real deployment resolves access_groups from the authenticated MCP session,
the same way DeepJudge resolves permissions from the firm's actual DMS/SharePoint ACLs
rather than trusting the client to say who it is — see CLAUDE.md rule 3.

Local-first mode (LOCAL_MODE=true): Uses SQLite + sentence-transformers embeddings.
Cloud mode (default): Uses PostgreSQL/pgvector + Voyage AI embeddings.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

server = MCPServer(
    name="precedent",
    version="0.1.0",
    instructions=(
        "A retrieval-first agent over a commercial-contracts corpus. "
        "Prefer ask_precedent for natural-language questions — it routes to the right "
        "skill and returns a cited, grounding-checked answer. Use search_contracts / "
        "get_document directly only if you want to reason over raw sources yourself. "
        "ingest_directory / watch_folder add client contracts to the index (local-first "
        "or cloud); ingested documents are only visible to the access groups they are "
        "tagged with."
    ),
)

from . import agent, retrieval
from .auth import get_current_user, AuthenticatedUser
from .config import settings
from .db import get_pool
from .exceptions import AuthenticationError
from .ingestion.chunking import ClauseChunk, chunk_into_clauses
from .ingestion.parsers import extract_text, discover_contract_files
from .classifier import classify_batch as classify_clauses_batch
from .local_store import (
    init_local_db,
    local_hybrid_search,
    local_get_document,
    local_upsert_document,
    local_get_existing_external_ids,
    _compute_external_id,
)

logger = logging.getLogger(__name__)

# In stdio MCP mode, we check for token in environment variable
# For production MCP servers over network, this would come from the authentication context
def get_mcp_access_groups() -> list[str]:
    """Get access groups for MCP connection based on token or development fallback.

    Returns:
        List of access group strings for the current MCP session

    Raises:
        AuthenticationError: If PRECEDENT_MCP_TOKEN is set but invalid. Never
            silently downgrades a bad token to public access — a revoked or
            mistyped token must fail loudly, not quietly become "public".
    """
    # Check for MCP token in environment (for testing/manual invocation)
    mcp_token = os.environ.get("PRECEDENT_MCP_TOKEN")
    if mcp_token:
        # A configured token MUST validate — no fallback on failure (fail closed).
        user = get_current_user(mcp_token)
        return user.access_groups

    # Development mode fallback (same env names api.py accepts: dev/development)
    if settings.precedent_env in ("development", "dev"):
        from .auth import create_mock_user_for_dev
        return create_mock_user_for_dev().access_groups

    # Production fallback to public (secure default)
    return ["public"]


@server.tool()
async def ask_precedent(query: str) -> str:
    """Ask a question about the contract corpus in natural language. Routes to the
    right specialized skill (precedent lookup, negotiation history, or risk flagging),
    retrieves, verifies grounding, and returns a cited answer with [doc:ID] markers.
    """
    pool = await get_pool()
    access_groups = get_mcp_access_groups()
    result = await agent.run_query(pool, query, access_groups=access_groups)
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
    access_groups = get_mcp_access_groups()
    results = await retrieval.hybrid_search(
        pool,
        query,
        access_groups=access_groups,
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
    """Fetch a full document plus all its labeled clauses by document_id in structured JSON format."""
    pool = await get_pool()
    access_groups = get_mcp_access_groups()
    doc = await retrieval.get_document(pool, document_id, access_groups=access_groups)
    if doc is None:
        return "Not found or not accessible."
    return json.dumps(doc, indent=2, default=str)


def _validate_path(path: str) -> Path:
    """Validate that a path is within allowed ingest roots."""
    resolved = Path(path).resolve()

    if settings.allowed_ingest_roots:
        allowed = False
        for root in settings.allowed_ingest_roots:
            try:
                resolved.relative_to(Path(root).resolve())
                allowed = True
                break
            except ValueError:
                continue
        if not allowed:
            raise ValueError(f"Path not in allowed ingest roots: {path}")

    if not resolved.exists():
        raise ValueError(f"Path does not exist: {path}")

    if not resolved.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    return resolved


@server.tool()
async def ingest_directory(
    path: str,
    access_group: str = "public",
    doc_type: str = "agreement",
    party: str = "",
    recursive: bool = True,
    dry_run: bool = False,
) -> str:
    """Ingest all contract files from a local directory.

    Supports PDF, DOCX, and TXT files. Uses local-first mode (SQLite + local embeddings)
    when LOCAL_MODE=true, otherwise uses PostgreSQL + Voyage AI.

    Args:
        path: Directory path to ingest from
        access_group: Access group for permission filtering (will be overridden by MCP auth in production)
        doc_type: Document type (e.g., 'agreement', 'msa', 'nda')
        party: Party name for metadata
        recursive: Whether to search subdirectories
        dry_run: If true, only report what would be ingested

    Returns:
        Summary of ingestion results
    """
    # In MCP context, override access_group with authenticated user's groups
    # For direct script usage, the provided access_group is used
    mcp_access_groups = get_mcp_access_groups()
    final_access_group = access_group if not settings.precedent_env == "production" or "PRECEDENT_MCP_TOKEN" not in os.environ else mcp_access_groups[0] if mcp_access_groups else "public"

    try:
        resolved_path = _validate_path(path)
    except ValueError as e:
        return f"Error: {e}"

    files = discover_contract_files(resolved_path, recursive=recursive)

    if not files:
        return f"No supported contract files found in {path}"

    results = {
        "total_files": len(files),
        "processed": 0,
        "skipped": 0,
        "errors": 0,
        "details": [],
    }

    if settings.local_mode:
        # Initialize local DB
        await init_local_db()

        for filepath in files:
            try:
                external_id = _compute_external_id(filepath)
                existing_ids = await local_get_existing_external_ids("custom")

                if external_id in existing_ids:
                    results["skipped"] += 1
                    results["details"].append(f"Skipped (already ingested): {filepath.name}")
                    continue

                if dry_run:
                    results["processed"] += 1
                    results["details"].append(f"Would ingest: {filepath.name}")
                    continue

                text = extract_text(filepath)
                if not text.strip():
                    results["errors"] += 1
                    results["details"].append(f"Error (empty text): {filepath.name}")
                    continue

                chunks = chunk_into_clauses(text)
                if not chunks:
                    results["errors"] += 1
                    results["details"].append(f"Error (no chunks): {filepath.name}")
                    continue

                chunk_types = await classify_clauses_batch([c.text for c in chunks])

                await local_upsert_document(
                    source="custom",
                    external_id=external_id,
                    title=filepath.stem,
                    doc_type=doc_type,
                    parties=[party] if party else [],
                    raw_text=text,
                    access_group=final_access_group,
                    chunks=chunks,
                    chunk_types=chunk_types,
                )

                results["processed"] += 1
                results["details"].append(f"Ingested: {filepath.name} ({len(chunks)} clauses)")

            except Exception as e:
                results["errors"] += 1
                results["details"].append(f"Error ingesting {filepath.name}: {e}")
    else:
        # Cloud mode - use existing ingestion pipeline
        from .ingestion.db import insert_document, insert_clauses
        from .ingestion.embed import embed_batch_async
        pool = await get_pool()

        for filepath in files:
            try:
                external_id = _compute_external_id(filepath)
                existing = await local_get_existing_external_ids("custom")

                if external_id in existing:
                    results["skipped"] += 1
                    results["details"].append(f"Skipped (already ingested): {filepath.name}")
                    continue

                if dry_run:
                    results["processed"] += 1
                    results["details"].append(f"Would ingest: {filepath.name}")
                    continue

                text = extract_text(filepath)
                if not text.strip():
                    results["errors"] += 1
                    results["details"].append(f"Error (empty text): {filepath.name}")
                    continue

                chunks = chunk_into_clauses(text)
                if not chunks:
                    results["errors"] += 1
                    results["details"].append(f"Error (no chunks): {filepath.name}")
                    continue

                chunk_types = await classify_clauses_batch([c.text for c in chunks])
                chunk_texts = [c.text for c in chunks]
                embeddings = await embed_batch_async(chunk_texts)

                doc_id = await insert_document(
                    pool,
                    source="custom",
                    external_id=external_id,
                    title=filepath.stem,
                    doc_type=doc_type,
                    parties=[party] if party else [],
                    raw_text=text,
                    access_group=final_access_group,
                )

                clause_dicts = []
                for chunk, emb, ctype in zip(chunks, embeddings, chunk_types):
                    clause_dicts.append({
                        "clause_type": ctype,
                        "clause_text": chunk.text,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                        "embedding": emb,
                    })

                await insert_clauses(pool, document_id=doc_id, clauses=clause_dicts, access_group=final_access_group)

                results["processed"] += 1
                results["details"].append(f"Ingested: {filepath.name} ({len(chunks)} clauses)")

            except Exception as e:
                results["errors"] += 1
                results["details"].append(f"Error ingesting {filepath.name}: {e}")

    # Format summary
    mode = "local" if settings.local_mode else "cloud"
    summary = [
        f"Ingestion complete ({mode} mode):",
        f"  Total files: {results['total_files']}",
        f"  Processed: {results['processed']}",
        f"  Skipped: {results['skipped']}",
        f"  Errors: {results['errors']}",
        "",
        "Details:",
    ] + [f"  - {d}" for d in results["details"]]

    return "\n".join(summary)


@server.tool()
async def watch_folder(
    path: str,
    access_group: str = "public",
    doc_type: str = "agreement",
    party: str = "",
) -> str:
    """Register a folder for background watching (local-first mode only).

    Adds the folder to the watch list. The watcher daemon (started via `precedent watch`)
    will monitor for file changes and automatically ingest new/modified contracts.

    Args:
        path: Directory path to watch
        access_group: Access group for permission filtering
        doc_type: Document type (e.g., 'agreement', 'msa', 'nda')
        party: Party name for metadata

    Returns:
        Status message
    """
    if not settings.local_mode:
        return "Error: watch_folder only available in local-first mode (LOCAL_MODE=true)"

    try:
        resolved_path = _validate_path(path)
    except ValueError as e:
        return f"Error: {e}"

    # Format for settings.watch_folders
    watch_spec = f"{resolved_path}|{access_group}|{doc_type}|{party}|true"

    if watch_spec in settings.watch_folders:
        return f"Folder already being watched: {path}"

    settings.watch_folders.append(watch_spec)

    return (
        f"Added to watch list: {path}\n"
        f"  access_group: {access_group}\n"
        f"  doc_type: {doc_type}\n"
        f"  party: {party or '(none)'}\n"
        f"  recursive: true\n\n"
        f"Start the watcher daemon with: `precedent watch`\n"
        f"Note: This persists only for the current session. For permanent watching, "
        f"add to WATCH_FOLDERS in .env"
    )


def main() -> None:
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
