"""Agent operations: every run of the agent harness writes exactly one row to
skill_runs, regardless of whether it succeeded, failed, or was refused for lack of
grounding. This is what lets you answer "who's using this, on what, at what cost" —
the question every AI-agent deployment eventually gets asked and most can't answer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import asyncpg

from .config import settings


@dataclass
class RunRecord:
    skill_name: str | None
    user_query: str
    model: str
    tool_calls: list[dict] = field(default_factory=list)
    cited_doc_ids: list[int] = field(default_factory=list)
    grounded: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    error: str | None = None


def compute_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Rough cost estimate from the pricing table in config.py. This is for visibility
    in the governance log, not a billing-grade reconciliation — re-check against
    platform.claude.com/docs/en/about-claude/pricing if the numbers here look stale.
    """
    in_rate, out_rate = settings.pricing_per_mtok.get(model, (0.0, 0.0))
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate


async def log_run(pool: asyncpg.Pool, run: RunRecord) -> int:
    cost = compute_cost_usd(run.model, run.input_tokens, run.output_tokens)
    async with pool.acquire() as conn:
        row_id = await conn.fetchval(
            """
            INSERT INTO skill_runs (
                skill_name, user_query, model, tool_calls, cited_doc_ids, grounded,
                input_tokens, output_tokens, cost_usd, latency_ms, error
            )
            VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """,
            run.skill_name,
            run.user_query,
            run.model,
            json.dumps(run.tool_calls),
            run.cited_doc_ids,
            run.grounded,
            run.input_tokens,
            run.output_tokens,
            cost,
            run.latency_ms,
            run.error,
        )
    return row_id
