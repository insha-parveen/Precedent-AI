import argparse
import asyncio
import json
import sys

from . import agent, retrieval
from .config import settings
from .db import get_pool
from .watcher import create_watcher_from_settings

# Brand logo - legal-adjacent professional identity (ASCII-compatible)
LOGO = r"""
============================================================
   PRECEDENT
   Retrieval-First Contract Intelligence
============================================================
"""


ACCESS_GROUPS = ["public"]

async def search_cmd(args):
    """Execute hybrid retrieval search and print formatted results."""
    pool = await get_pool()
    results = await retrieval.hybrid_search(pool, args.query, access_groups=ACCESS_GROUPS)
    if not results:
        print("No matching clauses found.")
        return
    for r in results:
        print(f"[doc:{r.document_id}] clause_id={r.clause_id} type={r.clause_type} ({r.doc_title}): {r.clause_text[:400]}...")

async def ask_cmd(args):
    """Execute LangGraph agent query and print cited answer."""
    pool = await get_pool()
    result = await agent.run_query(pool, args.query, access_groups=ACCESS_GROUPS)
    print(result.answer)
    if not result.grounded:
        print("\n[note: this answer did not pass the citation check — verify independently]")

async def doc_cmd(args):
    """Fetch and print structured document JSON."""
    pool = await get_pool()
    doc = await retrieval.get_document(pool, args.document_id, access_groups=ACCESS_GROUPS)
    if not doc:
        print(f"Document {args.document_id} not found or not accessible.")
        sys.exit(1)
    print(json.dumps(doc, indent=2))

def serve_cmd(args):
    """Serve the FastAPI backend for the web UI."""
    import uvicorn
    print(f"Starting Precedent API on {args.host}:{args.port}...")
    uvicorn.run("precedent.api:app", host=args.host, port=args.port, reload=True)


async def watch_cmd(args):
    """Start the folder watcher daemon for local-first ingestion."""
    if not settings.local_mode:
        print("Error: watch command only available in local-first mode (LOCAL_MODE=true)")
        sys.exit(1)

    if not settings.watch_folders:
        print("No folders configured to watch.")
        print("Add folders via MCP tool `watch_folder` or set WATCH_FOLDERS in .env")
        print("Format: path|access_group|doc_type|party|recursive")
        sys.exit(1)

    print("Starting folder watcher daemon...")
    print(f"Watching {len(settings.watch_folders)} folder(s):")
    for spec in settings.watch_folders:
        parts = spec.split("|")
        print(f"  - {parts[0]} (access_group={parts[1]}, doc_type={parts[2]}, party={parts[3] or 'none'})")

    watcher = await create_watcher_from_settings()

    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down watcher...")
        await watcher.stop()
        print("Watcher stopped.")


def main():
    print(LOGO)
    parser = argparse.ArgumentParser(description="Precedent AI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Precedent search command
    search = subparsers.add_parser("search", help="Hybrid semantic + keyword search")
    search.add_argument("query", help="Query text")

    # Precedent ask command
    ask = subparsers.add_parser("ask", help="Natural language contract analysis")
    ask.add_argument("query", help="Question text")

    # Precedent document lookup command
    doc = subparsers.add_parser("document", help="Retrieve structured document/clauses")
    doc.add_argument("document_id", type=int, help="Document ID")

    # Serve the API
    serve = subparsers.add_parser("serve", help="Start the FastAPI backend server")
    serve.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve.add_argument("--port", type=int, default=8000, help="Port to bind to")

    # Watch folders (local-first mode)
    watch = subparsers.add_parser("watch", help="Start folder watcher daemon (local-first mode)")
    watch.add_argument("--folder", action="append", help="Folder to watch (can specify multiple)")

    args = parser.parse_args()

    if args.command == "serve":
        serve_cmd(args)
        return

    if args.command == "watch":
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(watch_cmd(args))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            loop.close()
        return

    loop = asyncio.get_event_loop()
    try:
        if args.command == "search":
            loop.run_until_complete(search_cmd(args))
        elif args.command == "ask":
            loop.run_until_complete(ask_cmd(args))
        elif args.command == "document":
            loop.run_until_complete(doc_cmd(args))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        loop.close()

if __name__ == "__main__":
    main()
