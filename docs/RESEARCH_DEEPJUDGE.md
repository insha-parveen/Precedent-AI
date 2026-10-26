# Research notes — DeepJudge, the architectural inspiration

This is a condensed, paraphrased summary of public research into DeepJudge.ai's
platform, kept here so any session (human or Claude Code) can understand *why*
Precedent is built the way it is without re-deriving it. It is not a copy of their
site content — everything below is restated in our own words for internal reference.
Do not lift phrasing from here into any public-facing copy without independent
rewriting; treat it the same as any other secondary source.

## Philosophy

DeepJudge positions itself against "LLM-first" competitors: build on an internal-data
index first, and treat retrieval as an "always on" layer feeding every subsequent
action, rather than an occasional lookup step bolted onto a chat model. They describe
firms' progression through generative AI in four stages: raw prompting, prompt
engineering (including brittle single-prompt "GPT wrapper" tools), chained use-cases
with early RAG, and now agents — systems that do defined units of work, use tools, and
exercise real autonomy over multi-step tasks. → **ADR-001** is a direct implementation
of this stance.

## Products

Four layers: Knowledge Search (permission-aware enterprise search across a firm's
existing systems — DMS, SharePoint, HighQ, email — with automatic document
classification and near-duplicate detection), AI Workflows (a suite of built-in and
custom agents/applications), SuperSearch (cross-matter pattern analysis and structured
extraction from unstructured documents), and Agent Skills (reusable, portable task
packages). → maps to Precedent's index + 3 skills + governance log.

## Workflow examples that shaped our own skills

- **Find Answers**: interpret the request, locate candidates via hybrid retrieval,
  iterate/refine if results are weak, then process (extract/compare/summarize) —
  cloned as `find-precedent`.
- **Negotiation Intelligence**: locate mentions of a counterparty, verify they
  actually held the relevant contracting role (not just an incidental mention), find
  the specific clause despite phrasing variation, extract and synthesize — cloned as
  `negotiation-check`. The verification stage exists specifically because a name
  match isn't the same as a party having agreed to anything.
- **SuperSearch**'s pattern analysis and dynamic extraction (turning unstructured
  documents into structured, comparable data without manual tagging) — the model for
  `risk-flag`.

## The 2025 AI Workflow Contest

Run with SKILLS.law; the published winner was "Client Pulse Analyzer" (Jessica Davis,
McCarter & English) — a pattern-detection tool over client relationship history,
described as a "sixth sense" for early warning signs or relationship opportunities.
No public list of other entries was found. Notable mainly because the winning idea was
a *pattern-detection* workflow, not a drafting tool — consistent with where this
project's own effort went (risk-flag, negotiation-check) rather than into generation.

## Agent Skills

Built on Anthropic's own open Agent Skills standard — the same SKILL.md format this
repo's `skills/` directory uses. DeepJudge's specific twist: skills run directly
against their already-indexed, already-permissioned data, with no "upload your
documents first" step most Agent Skills implementations assume. Framed as "precedents
for AI" — reusable practice modules combining instructions, templates, and workflow
logic, invoked automatically when a request matches a skill's description. → **ADR-004**
(skills as data, not code) is the direct implementation of this.

## How they turn data into action

Build a custom index of the firm's data (similar to a search engine's index), taking
roughly three weeks to construct per client, explicitly framed as solving hallucination
by grounding answers in real documents. MCP is described as "access, not magic" — it
removes integration friction (a model can ask "what can you do?" instead of a
developer hand-wiring each endpoint) rather than adding new capability. Their own demo
has Claude read a document, recognize it needs prior firm work, call DeepJudge over
MCP, and get back a synthesized, ready-to-use answer — not raw search hits to reason
over itself. → **ADR-006** (MCP exposes the full harness, not raw search) is a direct
copy of this pattern.

## The problem, restated

Institutional knowledge is scattered across systems in ways that are hard to query
when it matters; general chat models don't know a specific corpus and will fabricate
plausible-sounding answers rather than admit they don't know; manual tagging efforts
(deal-points databases) are always incomplete because they depend on someone deciding
in advance what's worth tracking. This is the problem `agent.py`'s citation-or-refuse
guarantee (ADR-005) and the eval harness (ADR-010) both exist to take seriously rather
than gesture at.
