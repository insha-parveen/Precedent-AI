---
name: risk-flag
description: Use when the person provides or references a specific contract and wants it checked for missing or unusual clauses relative to typical market terms — "does this look standard", "what's missing from this NDA", "flag anything unusual in this agreement". Not for open-ended clause lookups with no target document.
---

# risk-flag

You are comparing one target document against the distribution of terms seen across the
rest of the corpus — not applying general legal knowledge about what contracts "should"
contain. The baseline is empirical (what this corpus actually shows), not doctrinal.

## Steps

1. **Identify the target document and its type.** Confirm `doc_type` via `get_document`
   or ask if it isn't clear — the baseline comparison only makes sense within the same
   document type (don't compare an NDA's clause set against merger agreement norms).

2. **Build the comparison set.** Call `search_contracts` filtered to the same `doc_type`
   to get the population of comparable contracts already in the corpus.

3. **Compare clause coverage.** For each of CUAD's clause categories that commonly
   appear in this `doc_type`, check whether the target document has a labeled clause of
   that type. A category that's present in most comparable contracts but absent here is
   a flag — not a conclusion that something is wrong, just something worth a human
   looking at.

4. **Compare clause terms where coverage matches.** For categories present in both the
   target and the comparison set, note if the target's language is notably more
   one-sided than what typically appears (e.g. an uncapped liability clause where
   comparable contracts cap it) — grounded in specific comparison documents, not a
   general sense of what's "fair."

## Output format

- A short table or list: clause category -> present/missing/unusual, one line of
  evidence each.
- Every "unusual" or "more one-sided than typical" claim needs a citation to the specific
  comparison document(s) it's based on.
- Explicitly separate "missing entirely" from "present but worth a second look" —
  they mean different things to whoever reads this.
- Close with a one-line disclaimer: this is a pattern comparison against this corpus,
  not legal advice, and a human should review anything flagged before acting on it.
