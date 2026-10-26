"""Single shared asyncpg pool. Everything else in this package borrows a connection
from here rather than opening its own — keep it that way, connection sprawl is how
small services quietly fall over under load.
"""
from __future__ import annotations

import asyncpg
from pgvector.asyncpg import register_vector

from .config import settings

_pool: asyncpg.Pool | None = None


async def _init_connection(conn: asyncpg.Connection) -> None:
    await register_vector(conn)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        is_pooler = "6543" in settings.database_url or "pooler.supabase.com" in settings.database_url
        pool_kwargs: dict = {
            "min_size": 1,
            "max_size": 10,
            "init": _init_connection,
        }
        if is_pooler:
            pool_kwargs["statement_cache_size"] = 0

        _pool = await asyncpg.create_pool(
            settings.database_url,
            **pool_kwargs,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
