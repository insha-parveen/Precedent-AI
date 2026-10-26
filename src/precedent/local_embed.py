"""Local embeddings using sentence-transformers.

Provides CPU/GPU embeddings for local-first mode without external API calls.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

import torch
from sentence_transformers import SentenceTransformer

from .config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load and cache the sentence-transformers model."""
    model_name = settings.local_embedding_model
    device = _get_device()
    model = SentenceTransformer(model_name, device=device)
    return model


def _get_device() -> str:
    """Determine the best available device."""
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def embed_local(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using the local sentence-transformers model.

    Args:
        texts: List of texts to embed

    Returns:
        List of embeddings (one per input text)
    """
    if not texts:
        return []

    model = _get_model()
    embeddings = model.encode(texts, convert_to_tensor=False, show_progress_bar=False)
    return embeddings.tolist()


def embed_local_single(text: str) -> List[float]:
    """Embed a single text string."""
    return embed_local([text])[0]


async def embed_local_async(texts: List[str]) -> List[List[float]]:
    """Async wrapper for local embedding (runs in thread pool).

    Note: sentence-transformers is synchronous; this runs in a thread pool
    for non-blocking operation.
    """
    import asyncio
    return await asyncio.to_thread(embed_local, texts)


def get_embedding_dim() -> int:
    """Get the embedding dimension for the configured local model."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()