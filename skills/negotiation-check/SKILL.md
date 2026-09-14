---
name: negotiation-check
description: Use when the person wants to know how a specific counterparty has negotiated a specific clause or position across past deals — "has [party] ever agreed to X", "how does [party] usually handle [clause type]". Not for general clause lookups with no named counterparty — use find-precedent for that.
---

# negotiation-check

The scenario this exists for: someone is negotiating a clause right now, the other side
says "we never agree to that," and you need to check whether that's actually true across
every contract this corpus has where that party appears.

This is a four-stage pipeline. Do not skip stages or merge them — each one exists
because skipping it produces false positives (see "why each stage exists" below).

## Steps

1. **Locate mentions.** Call `search_contracts` filtered by the named party (as a
   `parties` filter, and as a semantic/keyword fallback in case the name is spelled or
   abbreviated differently across documents).

2. **Verify the relationship.** For each candidate document, confirm the named party
   actually appears as a contracting party on the relevant side of the deal — not
   mentioned in passing, not acting as counsel or an advisor. Use `get_document` to
   check the parties section if `search_contracts` metadata doesn't make this clear.
   *Why this stage exists:* a name matching the text isn't the same as that party having
   agreed to anything. Skipping verification produces confident-sounding false positives,
   which is worse than no answer.

3. **Find the target clause.** Within the verified set, locate the specific clause type
   the person asked about. Clause phrasing varies a lot across documents — search
   semantically for the concept (e.g. "cap on liability", "limitation of liability",
   "aggregate liability not to exceed") in addition to the CUAD `clause_type` filter, so
   you don't miss a match just because of vocabulary differences.

4. **Extract and synthesize.** Pull the exact clause language from each remaining
   document and summarize the pattern: did this party agree to something like the
   position in question, and under what conditions (deal size, industry, who drafted).

## Output format

- Open with a direct verdict: yes/no/mixed, backed by count ("agreed to similar language
  in 3 of 4 contracts where they appear").
- Quote or closely paraphrase the actual clause language for each supporting document,
  each with a `[document_id, clause_id]` citation.
- If verification (step 2) eliminates a document, don't mention it as if it were
  evidence — silently drop it, it was never really on point.
- If the party never appears as a contracting party in this corpus at all, say that
  directly rather than stretching a weak semantic match into an answer.
