# Context brief (external input, reconciled)

This is the project brief pasted into chat on this date, saved verbatim for project
history. It was written independently of the scaffold already built in this repo, and
it disagrees with the existing code and docs in several concrete places (LangGraph vs.
the existing tool-use loop, a required browser frontend vs. an optional one, a skill
named `negotiate-like-we-have` vs. this repo's `negotiation-check`, an explicit
model-provider abstraction the existing `agent.py` doesn't have).

**Do not treat this file as a second source of truth alongside CLAUDE.md.** Every
substantive decision from this brief that was adopted has been merged into
`docs/ARCHITECTURE_DECISIONS.md` (ADR-011 through ADR-014), `docs/ROADMAP.md`, and
`docs/PRD.md`. Those are canonical. This file exists so the reasoning behind those
ADRs is traceable back to what prompted them — read it for context, not for
instructions that override the reconciled documents.

---

# PROJECT: PRECEDENT — Enterprise Contract Intelligence Agent

You are working on a portfolio-grade GenAI/AI Engineering project called **Precedent**.

Your job is to understand the product, architecture, goals, constraints, and intended real-world deployment BEFORE making implementation decisions.

Do not start coding blindly. First inspect the repository and existing files, then understand the architecture below and create/update the project plan accordingly.

---

## 1. WHAT WE ARE BUILDING

Precedent is an **enterprise contract-intelligence AI system**.

The core idea:

> Given a contract or business/legal question, the system retrieves relevant contractual evidence, finds historical precedent, detects deviations/risks, verifies its conclusions against source documents, and produces an evidence-backed answer with exact citations.

The system should NOT be a generic "chat with PDFs" application.

It should demonstrate a realistic enterprise AI architecture similar in spirit to modern legal AI platforms such as DeepJudge, while being an independent implementation with its own workflows and product design.

---

# 2. TWO MODES OF THE PRODUCT

## MODE A — PUBLIC PORTFOLIO DEMO

For the public/browser version, we will use public contract data.

Primary datasets:

* CUAD (Contract Understanding Atticus Dataset)
* Public SEC EDGAR filings/contracts

These datasets are used as the system's **knowledge/evaluation corpus**.

IMPORTANT:

Do NOT describe this as "training the LLM on CUAD."

The main LLM should remain a general-purpose inference model.

CUAD and EDGAR are primarily used for:

* document ingestion
* retrieval
* clause extraction
* precedent search
* risk/deviation analysis
* evaluation/benchmarking

The browser demo should allow a user to interact with this public corpus through a chat/UI.

Example:

User:
"Find contracts containing unusual termination provisions."

System:

1. retrieves relevant contracts
2. reranks evidence
3. extracts relevant clauses
4. compares them against precedent
5. verifies the conclusion
6. returns an answer
7. cites the exact source document and clause

---

# 3. MODE B — ENTERPRISE DEPLOYMENT

The architecture must also be designed so that a company could use the SAME agent/workflow architecture over its own authorised enterprise data.

Potential enterprise data sources:

* SharePoint
* Google Drive
* OneDrive
* Gmail / Microsoft 365 email
* Slack / Teams
* internal contract repositories
* CRM
* SQL databases
* document management systems
* other internal APIs/tools

This is where **MCP** becomes important.

MCP should be treated as the **tool/access integration layer**, NOT as the AI itself.

Conceptually:

Company systems
↓
MCP / connectors / authorised tools
↓
Precedent agent
↓
retrieval + reranking + skills + reasoning + verification
↓
evidence-backed answer

A company could potentially connect the agent to different authorised enterprise systems and use the same workflows over private company data.

IMPORTANT:

MCP does NOT automatically provide access to every company system.

Real enterprise integrations require:

* authentication
* authorisation
* permissions
* least-privilege access
* tenant isolation
* audit logging
* secure credential handling

The architecture must reflect this.

---

# 4. MODEL-AGNOSTIC DESIGN

The application should avoid unnecessary coupling between the agent architecture and one LLM provider.

The inference layer should be abstract enough that an organisation could potentially use providers such as:

* OpenAI
* Anthropic
* other compatible inference providers
* local/self-hosted models where practical

Do not build unnecessary provider-specific logic throughout the application.

Use a clean model/inference abstraction.

---

# 5. CORE ARCHITECTURE

The conceptual architecture is:

```
                PRECEDENT
                   │
    ┌──────────────┴──────────────┐
    │                             │
```

Knowledge Layer               Agent Layer
│                             │
┌─────┴─────┐              ┌────────┴────────┐
│            │              │                 │
Hybrid Search Reranking    Agent Skills      LangGraph
│            │              │                 │
└─────┬──────┘              └────────┬────────┘
│                              │
└──────────────┬───────────────┘
↓
Verification
↓
Evidence + citations
↓
User

Enterprise mode additionally:

Enterprise systems
↓
MCP / connectors
↓
Precedent
↓
same retrieval + workflow architecture

---

# 6. RETRIEVAL

Retrieval is a FIRST-CLASS component.

Do not implement this as simple vector similarity only.

Aim for:

1. document ingestion
2. metadata extraction
3. clause-aware / structure-aware chunking
4. lexical/BM25-style retrieval where appropriate
5. semantic/vector retrieval
6. hybrid retrieval
7. reranking
8. metadata/permission filtering
9. evidence selection

The system should be designed so that retrieval can be evaluated independently.

---

# 7. AGENT SKILLS

The project should use reusable workflow/skill definitions rather than putting all logic into one giant agent prompt.

Initial skills:

### find-precedent

Purpose:
Find historical contracts/clauses that provide precedent for the current question or contract.

Pipeline:

retrieve
→ rerank
→ verify
→ compare
→ synthesize
→ cite

### negotiate-like-we-have

Purpose:
Given a clause or contract position, identify how similar provisions were handled historically.

Pipeline:

identify clause
→ find similar precedent
→ compare positions
→ identify common historical outcomes
→ provide evidence

### risk-flag

Purpose:
Identify unusual/high-risk contractual deviations.

Pipeline:

extract clause
→ compare against precedent
→ identify deviation
→ assess evidence
→ explain reasoning
→ cite source

Skills should be modular and reusable.

---

# 8. LANGGRAPH

Use LangGraph for orchestration where it genuinely improves the system.

The agent should have explicit workflow states/nodes rather than one opaque LLM call.

For example:

START
↓
Understand request
↓
Select skill/workflow
↓
Retrieve evidence
↓
Rerank
↓
Extract/structure
↓
Verify
↓
Synthesize
↓
Citation validation
↓
Response
↓
END

Where useful, allow:

* branching
* retries
* parallel retrieval
* verification loops
* structured state
* human approval in future enterprise workflows

Do not add LangGraph nodes merely for the sake of showing LangGraph.

---

# 9. VERIFICATION

A major requirement is:

> The agent must verify important conclusions against retrieved evidence before answering.

Avoid unsupported statements.

The final response should ideally distinguish:

* source fact
* extracted clause
* comparison
* model inference/reasoning

Every important conclusion should be traceable to source evidence.

---

# 10. CITATIONS

Citations are a core feature, not decoration.

The UI should show:

* document name
* relevant section/clause
* source identifier
* ideally page/section information where available
* source URL for web-derived documents where applicable

A user should be able to inspect the evidence behind an answer.

---

# 11. EVALUATION

Evaluation is one of the most important parts of this project.

Do NOT only demonstrate that the chatbot works.

Build an evaluation framework.

Use CUAD labels/annotations where appropriate to evaluate extraction/retrieval capabilities.

Potential metrics:

* precision
* recall
* F1
* Recall@K
* Precision@K
* MRR
* NDCG
* citation/evidence accuracy
* groundedness
* answer correctness
* latency
* token/cost usage

Create a small deterministic golden evaluation set for the main workflows.

Evaluation should be runnable repeatedly after system changes.

---

# 12. MCP

MCP should be implemented as an **enterprise integration demonstration**.

It should expose a clean set of tools/resources that an MCP-compatible client/agent can interact with.

Potential examples:

* search_contracts
* get_contract
* search_customers
* get_contract_metadata
* search_documents

The MCP layer should not contain the core business logic.

Core intelligence remains in Precedent.

MCP is the interface through which external AI clients/agents or enterprise systems can access authorised Precedent capabilities and/or enterprise data.

Design it so that the architecture remains understandable:

Agent
↓
MCP tool
↓
authorised data source
↓
structured result
↓
agent reasoning

Do NOT build a fake MCP integration that merely wraps arbitrary internal functions without demonstrating a realistic use case.

---

# 13. SECURITY / ENTERPRISE DESIGN

Even though this is a portfolio project, demonstrate enterprise thinking.

Include architecture/design for:

* RBAC
* user identity
* document permissions
* tenant isolation
* least privilege
* audit logs
* secure API keys
* no secrets committed to Git
* prompt injection considerations
* malicious document considerations
* retrieval permission filtering
* citation/source validation

A user's access rights should ideally be applied BEFORE sensitive retrieval results are passed to the LLM.

---

# 14. PRODUCT EXPERIENCE

The browser UI should NOT look like a basic ChatGPT clone.

The main experience should communicate:

### Ask

"Find precedent for this clause."

### Investigate

"Why is this clause unusual?"

### Compare

"How does this contract differ from our historical agreements?"

### Review

"Identify clauses that require legal attention."

### Evidence

Show exact supporting documents/clauses.

A possible UI:

---

PRECEDENT
Contract Intelligence
---------------------

Ask a question...

[ Find precedent ]

Results

Risk: Medium

Reason:
The termination provision differs from
78% of comparable agreements.

## Evidence

Contract A
Section 8 — Termination

Contract B
Section 12 — Termination

Contract C
Section 9 — Termination
-----------------------

[View source]

---

# 15. TECHNOLOGY PRINCIPLES

Use production-style engineering practices.

Likely stack:

Backend:

* Python
* FastAPI

Agent:

* LangGraph

Retrieval:

* PostgreSQL + pgvector or another appropriate vector store
* hybrid retrieval
* reranking

Frontend:

* Next.js/React

Data:

* CUAD
* SEC EDGAR/public contracts

MCP:

* Python MCP implementation / appropriate official SDK

Deployment:

* choose practical free/low-cost services for the portfolio MVP

Do not introduce technologies just because they are fashionable.

Every major dependency must have a reason.

---

# 16. COST CONSTRAINT

This is a portfolio project.

Prefer free/open-source or free-tier solutions during development.

Avoid designing the MVP around expensive proprietary APIs.

Create clean provider abstractions so paid APIs can be substituted later.

Do not assume the project needs to spend money to demonstrate the architecture.

---

# 17. WHAT MAKES THIS PROJECT STRONG

The project should demonstrate ALL of the following:

Python
SQL
RAG
Hybrid search
Vector search
Reranking
Structured extraction
LLM orchestration
LangGraph
Agent Skills
MCP
FastAPI
Frontend
RBAC/security concepts
Evaluation
Observability/logging
Cost/latency awareness
Production architecture
Deployment

But functionality is more important than simply listing technologies.

---

# 18. IMPORTANT PRODUCT DISTINCTION

Do NOT build a clone of DeepJudge.

DeepJudge was researched only to understand architectural/product patterns.

Precedent should have its own identity and implementation.

The key inspiration is:

permission-aware retrieval
+
reusable AI workflows/skills
+
verification
+
enterprise integrations
+
evidence-backed output

---

# 19. DEVELOPMENT RULES

Before coding:

1. Inspect the entire repository.
2. Identify existing code and architecture.
3. Do not unnecessarily rewrite working components.
4. Create a clear implementation plan.
5. Identify risks and missing pieces.
6. Then implement incrementally.

When making technical decisions:

* prefer simple robust solutions
* don't over-engineer
* don't add unnecessary microservices
* don't add unnecessary agents
* don't add unnecessary abstractions
* don't create fake enterprise features
* keep components testable
* keep provider dependencies replaceable

Do not ask me for trivial approvals.

Make reasonable engineering decisions autonomously.

If an important architectural decision has multiple valid choices, choose the most practical option for a portfolio project and document the decision.

---

# 20. END GOAL

At the end, the project should tell this story:

> "I built an enterprise-style contract intelligence agent. It uses hybrid retrieval and reranking to find contractual evidence, LangGraph to orchestrate reusable Agent Skills, verification to reduce unsupported answers, and citations to make results auditable. I benchmarked the retrieval/extraction pipeline against CUAD and public contract data. The system has a browser-based public demo, while its architecture can be connected to authorised enterprise data through MCP."

That is the product we are building.
