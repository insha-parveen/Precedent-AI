"""Ingest custom client contracts into the hybrid index.

Usage:
    python scripts/ingest_custom.py --input-dir /path/to/contracts --access-group client-acme-corp

Features:
- Supports PDF, DOCX, TXT files
- Heuristic clause chunking (section headers, numbered clauses)
- Haiku classification against 41 CUAD categories
- Voyage embeddings with retry logic
- Resumable: skips already-ingested files (by filename)
- Tags all data with custom access_group for tenant isolation
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.precedent.classifier import classify_batch
from src.precedent.config import settings
from src.precedent.db import get_pool
from src.precedent.ingestion import parsers, chunking, embed, db


BATCH_SIZE = 32
MAX_CLAUSES_PER_DOC = 100
MAX_CHARS_PER_CLAUSE = 2000


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest custom client contracts")
    parser.add_argument("--input-dir", required=True, help="Directory containing contract files (PDF, DOCX, TXT)")
    parser.add_argument("--access-group", required=True, help="Access group for tenant isolation (e.g., client-acme-corp)")
    parser.add_argument("--doc-type", help="Default document type for all files (e.g., MSA, NDA)")
    parser.add_argument("--party", action="append", help="Party name(s) to associate with all documents")
    parser.add_argument("--recursive", action="store_true", default=True, help="Search recursively (default: True)")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false", help="Don't search recursively")
    parser.add_argument("--max-clauses", type=int, default=MAX_CLAUSES_PER_DOC, help=f"Max clauses per document (default: {MAX_CLAUSES_PER_DOC})")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"Embedding batch size (default: {BATCH_SIZE})")
    parser.add_argument("--dry-run", action="store_true", help="Parse and classify but don't write to database")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {input_dir}")

    print("=" * 60)
    print("Custom Contract Ingestion")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Access group:    {args.access_group}")
    print(f"Doc type:        {args.doc_type or '(auto-detect)'}")
    print(f"Parties:         {args.party or '(none)'}")
    print(f"Recursive:       {args.recursive}")
    print(f"Max clauses/doc: {args.max_clauses}")
    print(f"Batch size:      {args.batch_size}")
    print(f"Dry run:         {args.dry_run}")
    print("=" * 60)

    # Discover files
    files = parsers.discover_contract_files(input_dir, recursive=args.recursive)
    if not files:
        raise SystemExit(f"No supported files found in {input_dir} (looking for .pdf, .docx, .txt)")

    print(f"\nDiscovered {len(files)} file(s):")
    for f in files:
        print(f"  - {f.relative_to(input_dir)}")

    # Get database pool
    pool = await get_pool()

    # Check existing files for resumption
    existing_external_ids = await db.get_existing_external_ids(pool, "custom")
    print(f"\nAlready ingested (source=custom): {len(existing_external_ids)} document(s)")

    total_docs = 0
    total_clauses = 0
    skipped = 0

    for filepath in files:
        external_id = filepath.relative_to(input_dir).as_posix()

        if external_id in existing_external_ids:
            print(f"\n[SKIP] Already ingested: {external_id}")
            skipped += 1
            continue

        print(f"\n[PROCESS] {external_id}")

        try:
            # 1. Extract text
            print("  Extracting text...")
            raw_text = parsers.extract_text(filepath)
            if len(raw_text) < 100:
                print(f"  [WARN] Text too short ({len(raw_text)} chars), skipping")
                continue

            # 2. Chunk into clauses
            print("  Chunking into clauses...")
            clause_chunks = chunking.chunk_into_clauses(
                raw_text,
                max_clauses=args.max_clauses,
                max_chars_per_clause=MAX_CHARS_PER_CLAUSE,
            )

            if not clause_chunks:
                print("  [WARN] No clauses extracted, skipping")
                continue

            print(f"  Extracted {len(clause_chunks)} clause chunk(s)")

            # 3. Classify clauses
            print("  Classifying clauses...")
            clause_texts = [c.text for c in clause_chunks]
            classifications = await classify_batch(clause_texts)

            for chunk, cls in zip(clause_chunks, classifications):
                chunk.clause_type = cls

            # 4. Embed clauses
            print("  Generating embeddings...")
            embeddings = embed.embed_with_retry(
                clause_texts,
                model=settings.embedding_model,
                input_type="document",
            )

            # 5. Prepare clause records
            clause_records = []
            for chunk, emb in zip(clause_chunks, embeddings):
                clause_records.append({
                    "clause_type": chunk.clause_type,
                    "clause_text": chunk.text,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                    "embedding": emb,
                })

            # 6. Insert into database
            if not args.dry_run:
                print("  Writing to database...")

                # Determine document metadata
                filename = filepath.name
                title = args.doc_type or filename
                if args.doc_type:
                    title = f"{args.doc_type} - {filename}"

                doc_id = await db.insert_document(
                    pool,
                    source="custom",
                    external_id=external_id,
                    title=title,
                    doc_type=args.doc_type,
                    parties=args.party,
                    filing_date=None,  # Could extract from filename or document
                    raw_text=raw_text[:10000],  # Store first 10k chars
                    access_group=args.access_group,
                    source_url=None,
                )

                await db.insert_clauses(
                    pool,
                    document_id=doc_id,
                    clauses=clause_records,
                    access_group=args.access_group,
                )

                print(f"  -> Document {doc_id} with {len(clause_records)} clauses inserted")
            else:
                print(f"  [DRY RUN] Would insert document with {len(clause_records)} clauses")

            total_docs += 1
            total_clauses += len(clause_records)

        except Exception as e:
            print(f"  [ERROR] Failed to process {external_id}: {e}")
            continue

    print(f"\n{'=' * 60}")
    print("Ingestion Complete!")
    print(f"Documents processed: {total_docs}")
    print(f"Clauses indexed:     {total_clauses}")
    print(f"Skipped (existing):  {skipped}")
    if args.dry_run:
        print("[DRY RUN - no data written]")
    print(f"{'=' * 60}")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())