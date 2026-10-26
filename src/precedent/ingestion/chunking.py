"""Clause-boundary-aware text chunking for contracts.

Extracted from scripts/ingest_edgar.py for reuse across ingestion pipelines.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClauseChunk:
    """A chunk of contract text representing a clause or section."""
    text: str
    clause_type: str = "Other"
    char_start: Optional[int] = None
    char_end: Optional[int] = None


def chunk_into_clauses(text: str, max_clauses: int = 100, max_chars_per_clause: int = 2000) -> list[ClauseChunk]:
    """Chunk contract text into clauses using heuristic section headers.

    Args:
        text: Full contract text
        max_clauses: Maximum number of clauses to return
        max_chars_per_clause: Maximum characters per clause chunk

    Returns:
        List of ClauseChunk objects
    """
    # Split on major section boundaries (Section X., Article X., SECTION X., ARTICLE X.)
    section_pattern = r"(?=(?:^|\n)\s*(?:Section|Article|SECTION|ARTICLE)\s+[\dIVX]+\.?\s)"
    sections = re.split(section_pattern, text, flags=re.IGNORECASE | re.MULTILINE)

    chunks = []
    char_pos = 0

    for section in sections:
        if not section.strip():
            continue

        # Further split on numbered sub-clauses: (a), (b), 1., 2., etc.
        sub_pattern = r"(?=(?:^|\n)\s*(?:\(\w+\)|\d+\.\s))"
        sub_clauses = re.split(sub_pattern, section, flags=re.MULTILINE)

        for clause in sub_clauses:
            clause = clause.strip()
            if len(clause) < 50:  # Skip tiny fragments
                continue

            # Cap clause length for classification
            clause_text = clause[:max_chars_per_clause]

            chunks.append(ClauseChunk(
                text=clause_text,
                char_start=char_pos,
                char_end=char_pos + len(clause),
            ))
            char_pos += len(clause) + 1

            if len(chunks) >= max_clauses:
                return chunks

    # If no sections found, fall back to paragraph chunking
    if not chunks:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
        for p in paragraphs:
            if len(chunks) >= max_clauses:
                break
            chunks.append(ClauseChunk(text=p[:max_chars_per_clause]))

    return chunks[:max_clauses]


def chunk_by_fixed_size(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[ClauseChunk]:
    """Fallback: simple fixed-size chunking with overlap.

    Used when heuristic clause chunking produces too few chunks.

    Args:
        text: Full contract text
        chunk_size: Target size of each chunk in characters
        overlap: Overlap between adjacent chunks

    Returns:
        List of ClauseChunk objects
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        if len(chunk_text.strip()) >= 50:
            chunks.append(ClauseChunk(text=chunk_text, char_start=start, char_end=end))
        start += chunk_size - overlap
    return chunks