"""Voyage AI embedding utilities with retry logic.

Extracted from scripts/ingest_cuad.py for reuse across ingestion pipelines.
"""
from __future__ import annotations

import time
import voyageai

from src.precedent.config import settings


_voyage = voyageai.Client(api_key=settings.voyage_api_key)


def embed_with_retry(
    texts: list[str],
    model: str | None = None,
    input_type: str = "document",
    max_retries: int = 20,
) -> list[list[float]]:
    """Call Voyage AI embed with backoff retry on rate limits and transient errors.

    Args:
        texts: List of texts to embed
        model: Embedding model (defaults to settings.embedding_model)
        input_type: "document" for ingestion, "query" for search
        max_retries: Maximum number of retry attempts

    Returns:
        List of embeddings (one per input text)

    Raises:
        RuntimeError: If all retries exhausted
    """
    model = model or settings.embedding_model
    for attempt in range(max_retries):
        try:
            res = _voyage.embed(texts, model=model, input_type=input_type)
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


async def embed_batch_async(
    texts: list[str],
    model: str | None = None,
    input_type: str = "document",
    max_retries: int = 20,
) -> list[list[float]]:
    """Async wrapper for embed_with_retry (runs in thread pool for non-blocking).

    Note: voyageai client is synchronous; for true async, use the async client
    or run this in a thread pool executor.
    """
    import asyncio
    return await asyncio.to_thread(embed_with_retry, texts, model, input_type, max_retries)