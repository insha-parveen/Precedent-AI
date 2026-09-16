"""Scores retrieval quality against eval/test_queries.jsonl.

Metric: recall@k — for each seed query, does a clause of the expected_clause_type
appear anywhere in the top k hybrid_search results? This is checkable without hand
-labeling specific document IDs, because CUAD's own expert clause-type labels are
already the ground truth (see scripts/ingest_cuad.py — clause_type comes straight from
the dataset, it isn't model-generated).

NOTE: expected_clause_type strings in test_queries.jsonl must match whatever category
names actually landed in the `clauses` table after ingestion (see the column-name
caveat in ingest_cuad.py's docstring). This script does a case-insensitive substring
match specifically to absorb minor naming differences between CUAD releases — if a
query still scores 0 after that, check the actual clause_type values in the DB
(`SELECT DISTINCT clause_type FROM clauses;`) before assuming retrieval is broken.

Usage: python eval/run_eval.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.precedent.db import get_pool  # noqa: E402
from src.precedent.retrieval import hybrid_search  # noqa: E402

QUERIES_PATH = Path(__file__).resolve().parent / "test_queries.jsonl"


def _matches(expected: str, actual: str) -> bool:
    return expected.strip().lower() in actual.strip().lower()


async def main() -> None:
    queries = [json.loads(line) for line in QUERIES_PATH.read_text().splitlines() if line.strip()]
    pool = await get_pool()
    console = Console()

    table = Table(title="Precedent retrieval eval")
    table.add_column("query")
    table.add_column("expected type")
    table.add_column("hit@k")
    table.add_column("rank")
    table.add_column("latency (ms)")

    hits = 0
    for q in queries:
        start = time.monotonic()
        results = await hybrid_search(
            pool, q["query"], access_groups=["public"], limit=q.get("k", 10)
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        rank = next(
            (i + 1 for i, r in enumerate(results) if _matches(q["expected_clause_type"], r.clause_type)),
            None,
        )
        hit = rank is not None
        hits += hit

        table.add_row(
            q["query"][:60] + ("..." if len(q["query"]) > 60 else ""),
            q["expected_clause_type"],
            "YES" if hit else "NO",
            str(rank) if rank else "-",
            str(latency_ms),
        )

    console.print(table)
    recall = hits / len(queries) if queries else 0.0
    console.print(f"\nrecall@k: {hits}/{len(queries)} = {recall:.2%}")

    if recall < 1.0:
        console.print(
            "[yellow]Less than 100%: check clause_type values in the DB before "
            "assuming retrieval is at fault — see this script's module docstring.[/yellow]"
        )


if __name__ == "__main__":
    asyncio.run(main())
