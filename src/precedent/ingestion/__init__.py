"""Shared ingestion utilities for Precedent.

This package provides reusable components for document ingestion pipelines:
- parsers: Text extraction from PDF, DOCX, TXT
- chunking: Clause-boundary-aware text splitting
- embed: Voyage AI embedding with retry logic
- db: Database insert helpers for documents and clauses
"""