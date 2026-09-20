from typing import TypedDict, Annotated, Set, List, Union, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from . import retrieval, providers
from .config import settings
from .governance import RunRecord, log_run
from .skills_loader import Skill, load_skills
from .tools import ALL_TOOLS
import re
import time
import asyncpg
from dataclasses import dataclass

# Setup providers
gemini_provider = providers.GeminiProvider(api_key=settings.gemini_api_key)
grok_provider = providers.GrokProvider(
    api_key=settings.grok_api_key or settings.openai_api_key,
    base_url=settings.grok_base_url
)
anthropic_provider = providers.AnthropicProvider(api_key=settings.anthropic_api_key)

# Default hosted web provider: Gemini primary -> Grok fallback
provider = providers.FallbackProvider(primary=gemini_provider, fallback=grok_provider)

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

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    skill: Optional[Skill]
    seen_doc_ids: Set[int]
    input_tokens: int
    output_tokens: int
    error: Optional[str]
    system_prompt: str
    pool: asyncpg.Pool
    access_groups: List[str]
    retried: bool
    needs_retry: bool
    final_answer: str
    grounded: bool
    cited_doc_ids: List[int]

def route_skill(query: str, skills: list[Skill]) -> Skill | None:
    if not skills:
        return None
    options = "\n".join(f"- {s.name}: {s.description}" for s in skills)
    resp = provider.create_message(
        system=(
            "Pick the single skill whose description best matches the user's request. "
            "Reply with ONLY the skill name, exactly as given, or NONE if no skill's "
            "description clearly matches (a generic lookup with no named counterparty "
            "and no target document to compare should usually be NONE).\n\n"
            f"Skills:\n{options}"
        ),
        messages=[{"role": "user", "content": query}],
    )
    name = resp.content[0].text.strip() if resp.content else "NONE"
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
    if ":" in name:
        name = name.split(":")[-1]
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

# Node implementations
async def route_node(state: AgentState):
    skills = load_skills()
    query = state["messages"][0].content
    skill = route_skill(query, skills)
    system = BASE_SYSTEM_PROMPT
    if skill:
        system += f"\n\nActive skill — {skill.name}:\n{skill.instructions}"
    return {"skill": skill, "system_prompt": system}

async def generate_node(state: AgentState):
    resp = provider.create_message(
        system=state["system_prompt"],
        messages=state["messages"],
        tools=ALL_TOOLS,
    )
    content_text = resp.content[0].text if resp.content else ""
    additional_kwargs = {}
    if resp.raw_response is not None:
        additional_kwargs["gemini_candidate"] = resp.raw_response

    message = AIMessage(content=content_text, additional_kwargs=additional_kwargs)
    if hasattr(resp, 'tool_calls') and resp.tool_calls:
        # Normalize tool_calls to dict format for AIMessage
        normalized_calls = []
        for tc in resp.tool_calls:
            if isinstance(tc, dict):
                normalized_calls.append(tc)
            else:
                normalized_calls.append({
                    "id": tc.id,
                    "name": tc.name,
                    "args": tc.args
                })
        message.tool_calls = normalized_calls

    return {
        "messages": [message],
        "input_tokens": state.get("input_tokens", 0) + resp.usage.input_tokens,
        "output_tokens": state.get("output_tokens", 0) + resp.usage.output_tokens
    }

def should_continue(state: AgentState):
    if state.get("error"):
        return "check_citations"
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "check_citations"

async def execute_tools_node(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    tool_results = []
    seen_doc_ids = set(state.get("seen_doc_ids", set()))
    for tool_call in last_message.tool_calls:
        tc_name = tool_call["name"] if isinstance(tool_call, dict) else tool_call.name
        tc_args = tool_call["args"] if isinstance(tool_call, dict) else tool_call.args
        tc_id = tool_call["id"] if isinstance(tool_call, dict) else tool_call.id

        result_text, doc_ids = await _execute_tool(
            state["pool"], state["access_groups"], tc_name, tc_args
        )
        seen_doc_ids |= doc_ids
        tool_results.append(ToolMessage(tool_call_id=tc_id, name=tc_name, content=result_text))
    return {"messages": tool_results, "seen_doc_ids": seen_doc_ids}

async def check_citations_node(state: AgentState):
    last_message = state["messages"][-1]
    answer = last_message.content if hasattr(last_message, "content") else str(last_message)
    cited = {int(m) for m in CITATION_PATTERN.findall(answer)}
    seen = state.get("seen_doc_ids", set())

    # If sources were seen but not cited, and retry hasn't run yet -> trigger retry
    if seen and not cited and not state.get("retried", False):
        return {"needs_retry": True}

    grounded = bool(cited) or not seen
    if seen and not cited:
        answer = f"[unverified — could not confirm citations against retrieved sources]\n\n{answer}"

    return {
        "needs_retry": False,
        "final_answer": answer,
        "grounded": grounded,
        "cited_doc_ids": sorted(list(cited)),
    }

def route_citation_decision(state: AgentState):
    if state.get("needs_retry"):
        return "retry"
    return END

async def retry_node(state: AgentState):
    return {
        "messages": [HumanMessage(content=GROUNDING_RETRY_PROMPT)],
        "retried": True,
    }

# Graph Construction
workflow = StateGraph(AgentState)
workflow.add_node("route", route_node)
workflow.add_node("generate", generate_node)
workflow.add_node("tools", execute_tools_node)
workflow.add_node("check_citations", check_citations_node)
workflow.add_node("retry", retry_node)

workflow.add_edge(START, "route")
workflow.add_edge("route", "generate")
workflow.add_conditional_edges("generate", should_continue, {
    "tools": "tools",
    "check_citations": "check_citations"
})
workflow.add_edge("tools", "generate")
workflow.add_conditional_edges("check_citations", route_citation_decision, {
    "retry": "retry",
    END: END
})
workflow.add_edge("retry", "generate")
graph = workflow.compile()

async def run_query(
    pool: asyncpg.Pool,
    user_query: str,
    *,
    access_groups: list[str],
) -> AgentResult:
    start = time.monotonic()
    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_query)],
        "skill": None,
        "seen_doc_ids": set(),
        "input_tokens": 0,
        "output_tokens": 0,
        "error": None,
        "system_prompt": BASE_SYSTEM_PROMPT,
        "pool": pool,
        "access_groups": access_groups,
        "retried": False,
        "needs_retry": False,
        "final_answer": "",
        "grounded": False,
        "cited_doc_ids": [],
    }
    final_state = await graph.ainvoke(initial_state)
    answer = final_state.get("final_answer") or ""
    if not answer:
        answer = "".join(b.content if isinstance(b, AIMessage) else "" for b in final_state["messages"] if isinstance(b, AIMessage)).strip()

    cited_doc_ids = final_state.get("cited_doc_ids", [])
    grounded = final_state.get("grounded", False)
    skill_used = final_state["skill"].name if final_state.get("skill") else None

    # Log the run for governance
    await log_run(pool, RunRecord(
        skill_name=skill_used,
        user_query=user_query,
        model=settings.agent_model,
        tool_calls=[],
        cited_doc_ids=cited_doc_ids,
        grounded=grounded,
        input_tokens=final_state["input_tokens"],
        output_tokens=final_state["output_tokens"],
        latency_ms=int((time.monotonic() - start) * 1000),
        error=final_state.get("error"),
    ))

    return AgentResult(
        answer=answer,
        skill_used=skill_used,
        cited_doc_ids=cited_doc_ids,
        grounded=grounded,
        input_tokens=final_state["input_tokens"],
        output_tokens=final_state["output_tokens"],
        latency_ms=int((time.monotonic() - start) * 1000),
    )
