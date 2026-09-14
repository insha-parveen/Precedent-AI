"""Applies db/schema.sql. Idempotent (everything in schema.sql is CREATE IF NOT EXISTS),
so it's safe to re-run.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.precedent.config import settings  # noqa: E402

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "db" / "schema.sql"


async def main() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = await asyncpg.connect(settings.database_url)
    try:
        await conn.execute(sql)
        print(f"Applied {SCHEMA_PATH} to {settings.database_url}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
