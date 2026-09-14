---
name: find-precedent
description: Use when the person asks whether a document/clause/deal like this has come up before, wants examples of a contract type, or asks a "have we done this before" style question. Locates and returns the most relevant prior contracts with citations — not a summary from memory.
---

# find-precedent

You are answering "have we seen something like this before?" Never answer from your
own knowledge of contract law in general — the whole point of this skill is that the
answer comes from this specific corpus, with a document you can point to.

## Steps

1. **Interpret the request.** Separate two things the person may have blended together:
   - What defines the right set of documents (doc type, clause type, party, industry,
     date range)
   - What they want done with the results (list them, extract a provision, compare
     language, summarize)
   If either is ambiguous, ask one clarifying question rather than guessing — a wrong
   guess here wastes the retrieval budget.

2. **Locate candidates.** Call `search_contracts` with both a semantic query (the
   concept/clause they're describing) and any structured filters you can extract
   (`doc_type`, `clause_type`, `parties`). Request more results than you think you need
   (10-15) — you will filter down in the next step, not the search itself.

3. **Iterate if the first pass is weak.** If results look off-topic or too sparse,
   reformulate: try a narrower clause_type, try without the doc_type filter, try
   different phrasing of the semantic query. Two or three search attempts is normal.
   Do not present thin or irrelevant results just because a first search returned them.

4. **Process according to what was asked.** Depending on step 1: extract the specific
   clause text via `get_document`, compare language across the top 3-5 matches, or
   summarize how each one addresses the question.

## Output format

- Lead with a direct answer to the question (yes/no/here's what we have), not a list
  of search results.
- Every specific claim about contract language must carry a citation:
  `[document_id, clause_id]` or a short reference the person can look up.
- Show 2-4 of the strongest matches, not all matches. If there are more, say how many
  and offer to show the rest.
- If nothing relevant is found, say so plainly. Do not synthesize a plausible-sounding
  answer to avoid an empty result.
