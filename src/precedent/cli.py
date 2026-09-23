import argparse
import asyncio
import sys
import json
from precedent import retrieval, agent
from precedent.db import get_pool

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

    args = parser.parse_args()

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
