"""Ingest CUAD into the hybrid index.

DOWNLOAD FIRST (this sandbox that generated this scaffold has no network access to
atticusprojectai.org or huggingface.co, so this step is manual):

    Get CUAD v1 from https://www.atticusprojectai.org/cuad (or the mirror at
    https://huggingface.co/datasets/theatticusproject/cuad) and place the master
    clauses CSV at data/raw/CUAD_v1_master_clauses.csv, and full_contracts_txt/ (or pdf/)
    alongside it.

IMPORTANT — verify before trusting the parsing below:
    The master clauses CSV format is documented as "1 filename column + 41 categories x
    2 columns (context span + human answer)" ~83 columns total, but the exact column
    names may differ slightly across CUAD's release versions. FIRST RUN:

        python -c "import pandas as pd; print(pd.read_csv('data/raw/CUAD_v1_master_clauses.csv').columns.tolist())"

    and adjust CONTEXT_COLUMN_SUFFIX / METADATA_COLUMNS below to match what you actually
    see before running the full ingest. This script is written to fail loudly (see
    _require_columns) rather than silently ingest garbage if the column names don't match.

Clause-aware chunking: rather than a fixed-size sliding window, each clause chunk is
exactly the span CUAD's own legal-expert annotators identified for that category. This
is both more defensible than arbitrary chunking and directly usable as eval ground
truth in eval/run_eval.py.
"""
from __future__ import annotations

import ast
import asyncio
import sys
import time
from pathlib import Path

import pandas as pd
import voyageai

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.precedent.config import settings  # noqa: E402
from src.precedent.db import get_pool  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
CSV_PATH = DATA_DIR / "CUAD_v1_master_clauses.csv"

# Columns that are metadata, not a clause category. VERIFY against your actual CSV —
# see the module docstring.
METADATA_COLUMNS = {"Filename", "Document Name", "Document Name-Answer"}

# Columns ending in this suffix hold the raw labeled text span for a category; the
# category name is the column name with this suffix stripped. VERIFY against your CSV.
CONTEXT_COLUMN_SUFFIX = ""  # e.g. set to "" if context columns are the bare category
# name and answers are in "<Category>-Answer" — inspect columns first, adjust here.

BATCH_SIZE = 32  # Voyage batches embedding calls; conservative size for steady throughput


def _require_columns(df: pd.DataFrame) -> None:
    if "Filename" not in df.columns:
        raise SystemExit(
            "Expected a 'Filename' column and didn't find one. Run the column-inspection "
            "one-liner in this file's docstring and update METADATA_COLUMNS / "
            "CONTEXT_COLUMN_SUFFIX to match your actual CSV before re-running."
        )


def _clause_category_columns(df: pd.DataFrame) -> list[str]:
    return [
        c
        for c in df.columns
        if c not in METADATA_COLUMNS
        and not (c.endswith("-Answer") or c.endswith("- Answer") or c.strip().endswith("Answer"))
    ]


def _parse_span_list(cell) -> list[str]:
    """CUAD stores multiple spans per cell as a Python-list-literal string, e.g.
    "['This Agreement...', 'and shall continue...']". Falls back to treating the cell
    as a single span if it isn't list-literal syntax.
    """
    if pd.isna(cell) or not str(cell).strip():
        return []
    try:
        parsed = ast.literal_eval(cell)
        if isinstance(parsed, list):
            return [s for s in parsed if s and str(s).strip()]
    except (ValueError, SyntaxError):
        pass
    return [str(cell).strip()]


def _embed_with_retry(
    client: voyageai.Client,
    texts: list[str],
    model: str,
    input_type: str = "document",
    max_retries: int = 20,
) -> list[list[float]]:
    """Calls Voyage AI embed with backoff retry on RateLimitError and transient network errors."""
    for attempt in range(max_retries):
        try:
            res = client.embed(texts, model=model, input_type=input_type)
            return res.embeddings
        except Exception as e:
            err_msg = str(e).lower()
            if "rate" in err_msg or isinstance(e, getattr(voyageai.error, "RateLimitError", ())):
                wait_s = 22.0
                print(f"    [Rate limit on attempt {attempt + 1}/{max_retries}: sleeping {wait_s}s...]", flush=True)
            else:
                wait_s = 5.0 * (attempt + 1)
                print(f"    [Transient error ({type(e).__name__}: {e}) on attempt {attempt + 1}/{max_retries}: sleeping {wait_s}s...]", flush=True)
            time.sleep(wait_s)
    raise RuntimeError(f"Failed to embed batch after {max_retries} attempts.")


async def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing {CSV_PATH} — see this script's module docstring.")

    df = pd.read_csv(CSV_PATH)
    _require_columns(df)
    category_columns = _clause_category_columns(df)
    print(f"Found {len(category_columns)} clause categories, {len(df)} contracts.")

    voyage = voyageai.Client(api_key=settings.voyage_api_key)
    pool = await get_pool()

    # Query already ingested documents to allow safe resumption
    async with pool.acquire() as conn:
        existing_filenames = set(
            await conn.fetchval(
                """
                SELECT COALESCE(array_agg(external_id), '{}')
                FROM documents
                WHERE id IN (SELECT DISTINCT document_id FROM clauses)
                """
            )
        )
        total_existing_clauses = await conn.fetchval("SELECT count(*) FROM clauses;")

    if existing_filenames:
        print(f"Resuming: {len(existing_filenames)} contracts ({total_existing_clauses} clauses) already in database.")

    inserted_clauses = total_existing_clauses
    pending_texts: list[str] = []
    pending_meta: list[tuple[int, str, str]] = []  # (document_id, clause_type, text)

    async def flush_batch() -> None:
        nonlocal inserted_clauses
        if not pending_texts:
            return
        embeddings = _embed_with_retry(
            voyage, pending_texts, model=settings.embedding_model, input_type="document"
        )
        async with pool.acquire() as conn:
            for (doc_id, clause_type, text), emb in zip(pending_meta, embeddings):
                await conn.execute(
                    """
                    INSERT INTO clauses (document_id, clause_type, clause_text, embedding)
                    VALUES ($1, $2, $3, $4)
                    """,
                    doc_id,
                    clause_type,
                    text,
                    emb,
                )
        inserted_clauses += len(pending_texts)
        print(f"  -> Total clauses indexed: {inserted_clauses}...", flush=True)
        pending_texts.clear()
        pending_meta.clear()

    for _, row in df.iterrows():
        filename = str(row["Filename"])
        if filename in existing_filenames:
            continue

        parties_raw = row.get("Parties", "")
        parties = _parse_span_list(parties_raw)

        async with pool.acquire() as conn:
            doc_id = await conn.fetchval(
                """
                INSERT INTO documents (source, external_id, title, parties, raw_text)
                VALUES ('cuad', $1, $2, $3, $4)
                ON CONFLICT (source, external_id) DO UPDATE SET title = EXCLUDED.title
                RETURNING id
                """,
                filename,
                filename,
                parties,
                "",  # full raw_text: load from full_contracts_txt/<filename>.txt if present
            )

        for category in category_columns:
            for span in _parse_span_list(row.get(category)):
                pending_texts.append(span)
                pending_meta.append((doc_id, category, span))
                if len(pending_texts) >= BATCH_SIZE:
                    await flush_batch()

    await flush_batch()
    print(f"Ingestion complete! Total clauses indexed: {inserted_clauses}. Run: python eval/run_eval.py")


if __name__ == "__main__":
    asyncio.run(main())
