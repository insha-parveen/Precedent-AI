"""Folder watcher daemon for local-first ingestion.

Monitors directories for file changes and triggers incremental ingestion.

Importers/callers: None yet (new file). Will be called from:
- src/precedent/cli.py (watch command)
- src/precedent/mcp_server.py (watch_folder MCP tool)

Affected API (new classes/functions):
- WatchConfig - dataclass for watch configuration
- ContractEventHandler - watchdog event handler
- FolderWatcher - main watcher class with start/stop
- create_watcher_from_settings() - factory from config

Data schemas:
- WatchConfig fields: path, access_group, doc_type, party, recursive, debounce_seconds
- settings.watch_folders format: "path|access_group|doc_type|party|recursive"

User instruction: "To let a client 'point Claude at their desktop folders': 1. New MCP tools — ingest_directory(path, access_group), watch_folder(path) 2. File watcher/ingestion pipeline — Background process that monitors folders 3. Local-first mode — SQLite + local embeddings (no Supabase) for air-gapped use 4. Security model — The MCP server runs with the user's file permissions; dangerous if exposed remotely"
"""

# Minimal implementation to unblock tests - this is a placeholder
# TODO: Implement actual folder watcher functionality

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class WatchConfig:
    """Configuration for a folder watch."""
    path: str
    access_group: str = "public"
    doc_type: str = "agreement"
    party: str = ""
    recursive: bool = True
    debounce_seconds: int = 2


class ContractEventHandler:
    """Placeholder for watchdog event handler."""
    pass


class FolderWatcher:
    """Placeholder for main watcher class."""

    def __init__(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass


def create_watcher_from_settings():
    """Factory function to create watcher from settings."""
    return FolderWatcher()