"""The agent harness.

Pipeline: route -> retrieve (via tool use) -> verify grounding -> cite -> log.

Deliberately NOT here: any skill-specific branching ("if negotiation-check, do X").
The three skills differ entirely through the text loaded from their SKILL.md files.
If you find yourself writing `if skill.name == "risk-flag":` anywhere below, stop —
that logic belongs in the skill's instructions, not in this file. See CLAUDE.md rule 4.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import anthropic
import asyncpg

from . import retrieval
from .config import settings
from .governance import RunRecord, log_run
from .skills_loader import Skill, load_skills

CITATION_PATTERN = re.compile(r"\[doc:(\d+)\]")

BASE_SYSTEM_PROMPT = """\
You are Precedent, a contract-intelligence agent over a fixed corpus of commercial \
contracts. Two rules override everything else, including any instinct to be more \
helpful by filling a gap:

1. Never state a fact about contract language, a party, or a clause unless it came \
from a search_contracts or get_document tool result in THIS conversation. If you \
don't have it from a tool call, say you don't have it — do not reason from general \
knowledge of what contracts "usually" say.
2. Every specific claim about document content must carry an inline citation in the \
exact format [doc:<document_id>], immediately after the claim. No other citation \
format is acceptable — the agent harness checks for this exact pattern.

If search_contracts returns nothing relevant after a reasonable reformulation attempt, \
say so plainly. An honest "not found" is always the correct answer over a fabricated \
plausible one.
"""

GROUNDING_RETRY_PROMPT = """\
Your previous answer didn't include citation markers in the exact format [doc:ID] for \
its factual claims. Revise it now: keep only claims you can trace to a document_id \
already returned by a tool call above, and add [doc:ID] immediately after each one. \
If a claim can't be traced to a retrieved document, remove it.
"""


@dataclass
class AgentResult:
    answer: str
    skill_used: str | None
    cited_doc_ids: list[int]
    grounded: bool
    input_tokens: int
    output_tokens: int
    latency_ms: int


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def route_skill(client: anthropic.Anthropic, query: str, skills: list[Skill]) -> Skill | None:
    """Pick the single best-matching skill, or None if the query is a generic lookup
    that find-precedent-style plain search already covers. This is a cheap, separate
    call on purpose — routing is a classification task, not something worth spending
    the main agent's tool-use budget deciding.
    """
    if not skills:
        return None

    options = "\n".join(f"- {s.name}: {s.description}" for s in skills)
    resp = client.messages.create(
        model=settings.classifier_model,
        max_tokens=20,
        system=(
            "Pick the single skill whose description best matches the user's request. "
            "Reply with ONLY the skill name, exactly as given, or NONE if no skill's "
            "description clearly matches (a generic lookup with no named counterparty "
            "and no target document to compare should usually be NONE).\n\n"
            f"Skills:\n{options}"
        ),
        messages=[{"role": "user", "content": query}],
    )
    name = resp.content[0].text.strip()
    return next((s for s in skills if s.name == name), None)


def _format_search_results(results: list[retrieval.ClauseResult]) -> str:
    if not results:
        return "No matching clauses found."
    lines = []
    for r in results:
        lines.append(
            f"document_id={r.document_id} clause_id={r.clause_id} "
            f"type={r.clause_type!r} doc_title={r.doc_title!r} doc_type={r.doc_type!r} "
            f"parties={r.parties}\ntext: {r.clause_text[:600]}"
        )
    return "\n\n".join(lines)


async def _execute_tool(
    pool: asyncpg.Pool, access_groups: list[str], name: str, tool_input: dict
) -> tuple[str, set[int]]:
    """Run one tool call. Returns (text for Claude, document_ids surfaced) — the
    second value is what the grounding check verifies citations against.
    """
    if name == "search_contracts":
        results = await retrieval.hybrid_search(
            pool,
            tool_input["query"],
            access_groups=access_groups,
            clause_type=tool_input.get("clause_type"),
            doc_type=tool_input.get("doc_type"),
            parties=tool_input.get("parties"),
            limit=tool_input.get("limit", 10),
        )
        return _format_search_results(results), {r.document_id for r in results}

    if name == "get_document":
        doc = await retrieval.get_document(
            pool, tool_input["document_id"], access_groups=access_groups
        )
        if doc is None:
            return "Document not found or not accessible.", set()
        clause_lines = "\n".join(
            f"  clause_id={c['clause_id']} type={c['clause_type']!r}: "
            f"{c['clause_text'][:300]}"
            for c in doc["clauses"]
        )
        return (
            f"document_id={doc['id']} title={doc['title']!r} doc_type={doc['doc_type']!r} "
            f"parties={doc['parties']}\nclauses:\n{clause_lines}"
        ), {doc["id"]}

    return f"Unknown tool: {name}", set()


async def run_query(
    pool: asyncpg.Pool,
    user_query: str,
    *,
    access_groups: list[str],
) -> AgentResult:
    from .tools import ALL_TOOLS

    start = time.monotonic()
    client = _client()
    skills = load_skills()
    skill = route_skill(client, user_query, skills)

    system = BASE_SYSTEM_PROMPT
    if skill:
        system += f"\n\nActive skill — {skill.name}:\n{skill.instructions}"

    messages: list[dict] = [{"role": "user", "content": user_query}]
    seen_doc_ids: set[int] = set()
    input_tokens = 0
    output_tokens = 0
    error: str | None = None

    try:
        # The tool-use loop. max 6 rounds — a well-scoped skill (see the "iterate 2-3
        # times" guidance in find-precedent's SKILL.md) shouldn't need more than that;
        # more is a sign of a routing or retrieval problem worth surfacing, not silently
        # looping forever against the API.
        for _ in range(6):
            resp = client.messages.create(
                model=settings.agent_model,
                max_tokens=1500,
                system=system,
                messages=messages,
                tools=ALL_TOOLS,
            )
            input_tokens += resp.usage.input_tokens
            output_tokens += resp.usage.output_tokens
            messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason != "tool_use":
                break

            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result_text, doc_ids = await _execute_tool(
                        pool, access_groups, block.name, block.input
                    )
                    seen_doc_ids |= doc_ids
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
        else:
            error = "tool-use loop exceeded 6 rounds without a final answer"

        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
        cited = {int(m) for m in CITATION_PATTERN.findall(answer)}
        grounded = bool(cited) or not seen_doc_ids  # nothing retrieved -> nothing to cite

        # One retry if we searched, got results, but the answer didn't cite them.
        if seen_doc_ids and not cited:
            messages.append({"role": "user", "content": GROUNDING_RETRY_PROMPT})
            resp = client.messages.create(
                model=settings.agent_model,
                max_tokens=1500,
                system=system,
                messages=messages,
                tools=ALL_TOOLS,
            )
            input_tokens += resp.usage.input_tokens
            output_tokens += resp.usage.output_tokens
            retry_answer = "".join(b.text for b in resp.content if b.type == "text").strip()
            retry_cited = {int(m) for m in CITATION_PATTERN.findall(retry_answer)}
            if retry_cited:
                answer, cited, grounded = retry_answer, retry_cited, True
            else:
                grounded = False
                answer = (
                    "[unverified — could not confirm citations against retrieved "
                    f"sources]\n\n{answer}"
                )

    except Exception as exc:  # noqa: BLE001 — surfaced via governance log, not swallowed
        error = str(exc)
        answer = "The agent hit an error and did not produce a grounded answer."
        cited = set()
        grounded = False

    latency_ms = int((time.monotonic() - start) * 1000)

    async def _log() -> None:
        await log_run(
            pool,
            RunRecord(
                skill_name=skill.name if skill else None,
                user_query=user_query,
                model=settings.agent_model,
                cited_doc_ids=sorted(cited),
                grounded=grounded,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                error=error,
            ),
        )

    await _log()

    return AgentResult(
        answer=answer,
        skill_used=skill.name if skill else None,
        cited_doc_ids=sorted(cited),
        grounded=grounded,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
    )
