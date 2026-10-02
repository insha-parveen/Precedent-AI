"""Clause classifier for EDGAR documents.

Uses Haiku (Anthropic) via the existing LLMProvider abstraction to classify
raw contract text chunks into the CUAD 41-category taxonomy. This is the first
time the classifier_model (Haiku) is exercised in the Precedent pipeline.

The classifier is designed for cost-efficient batch classification with a
confidence threshold — low-confidence predictions fall back to "Other".
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.precedent.providers import AnthropicProvider, ProviderResponse  # noqa: E402
from src.precedent.config import settings  # noqa: E402


# CUAD's 41 clause categories — must match the taxonomy used in ingestion
CUAD_CATEGORIES = [
    "Affiliate License-Licensee",
    "Affiliate License-Licensor",
    "Anti-Assignment",
    "Audit Rights",
    "Cap On Liability",
    "Change Of Control",
    "Competition Restriction",
    "Confidentiality",
    "Covenant Not To Sue",
    "Effective Date",
    "Exclusivity",
    "Expiration Date",
    "Force Majeure",
    "Governing Law",
    "Insurance",
    "IP Ownership Assignment",
    "IP Ownership Inventor",
    "IP Ownership Joint",
    "License Grant",
    "License Grant-Back",
    "License Grant-Exclusive",
    "License Grant-Non-Exclusive",
    "License Grant-Restrictions",
    "License Grant-Sublicense",
    "License Grant-Territory",
    "Limited Liability",
    "Liquidated Damages",
    "Most Favored Nation",
    "Non-Compete",
    "Non-Disparagement",
    "Non-Solicit Customer",
    "Non-Solicit Employee",
    "Notice Period To Terminate Renewal",
    "Of ACV",
    "Parties",
    "Payment Terms",
    "Price Restriction",
    "Renewal Term",
    "Revenue Profit Sharing",
    "Right Of First Refusal Offer Match",
    "Termination For Convenience",
    "Termination For Cause",
    "Volume Restriction",
    "Warranty Duration",
]

# For classification, we group similar categories to reduce confusion
CATEGORY_DEFINITIONS = {
    "Governing Law": "Which jurisdiction's law governs the contract",
    "Termination For Convenience": "Either party can terminate without cause with notice",
    "Termination For Cause": "Termination rights triggered by breach or specific events",
    "Cap On Liability": "Maximum liability capped at a fixed amount or fees paid",
    "Limited Liability": "Liability limitations, exclusions of consequential damages",
    "Indemnification": "Indemnification obligations between parties",
    "Confidentiality": "Non-disclosure and confidentiality obligations",
    "Non-Compete": "Restrictions on competing with the other party",
    "Non-Solicit Customer": "Restrictions on soliciting the other party's customers",
    "Non-Solicit Employee": "Restrictions on soliciting the other party's employees",
    "Non-Disparagement": "Prohibition on negative statements about the other party",
    "Change Of Control": "Rights triggered by merger, acquisition, or change of control",
    "Anti-Assignment": "Restrictions on assigning or transferring the contract",
    "Audit Rights": "Right to inspect the other party's books and records",
    "Most Favored Nation": "Best pricing guarantee compared to other customers",
    "License Grant": "Grant of license rights (general)",
    "License Grant-Exclusive": "Exclusive license grant",
    "License Grant-Non-Exclusive": "Non-exclusive license grant",
    "License Grant-Sublicense": "Right to sublicense",
    "License Grant-Territory": "Geographic territory for license",
    "License Grant-Restrictions": "Restrictions on license use",
    "License Grant-Back": "Grant-back of improvements to licensor",
    "IP Ownership Assignment": "Assignment of IP ownership",
    "IP Ownership Inventor": "Inventor ownership provisions",
    "IP Ownership Joint": "Joint IP ownership",
    "Payment Terms": "Payment amounts, schedules, and terms",
    "Price Restriction": "Restrictions on pricing or price changes",
    "Volume Restriction": "Minimum or maximum volume commitments",
    "Revenue Profit Sharing": "Revenue or profit sharing arrangements",
    "Right Of First Refusal Offer Match": "Right of first refusal or offer matching",
    "Exclusivity": "Exclusive dealing or supply obligations",
    "Insurance": "Insurance requirements",
    "Force Majeure": "Force majeure clause",
    "Warranty Duration": "Duration of warranties",
    "Notice Period To Terminate Renewal": "Notice period for non-renewal",
    "Renewal Term": "Automatic renewal provisions",
    "Expiration Date": "Contract expiration date",
    "Effective Date": "Contract effective date",
    "Of ACV": "Annual Contract Value references",
    "Parties": "Identification of contracting parties",
    "Competition Restriction": "General competition restrictions",
    "Covenant Not To Sue": "Covenant not to sue",
    "Affiliate License-Licensee": "Affiliate license terms (licensee side)",
    "Affiliate License-Licensor": "Affiliate license terms (licensor side)",
}

# Build the classification prompt
CLASSIFICATION_PROMPT = f"""You are a legal contract classifier. Classify the following contract clause text into ONE of these 41 categories:

{chr(10).join(f'- {cat}: {CATEGORY_DEFINITIONS.get(cat, "General contract provision")}' for cat in CUAD_CATEGORIES)}

Respond with ONLY a JSON object:
{{
  "category": "exact_category_name_from_list_above",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

If the text doesn't clearly fit any category, use "Other" as the category with low confidence.
"""


async def classify_clause(text: str) -> str:
    """Classify a single clause text into a CUAD category using Haiku.

    Args:
        text: The clause text to classify (up to ~2000 chars)

    Returns:
        Category name (one of CUAD_CATEGORIES or "Other")
    """
    # Truncate if too long
    text = text[:2000]

    provider = AnthropicProvider(api_key=settings.anthropic_api_key or "dummy")

    # Use Haiku for cost efficiency
    try:
        response: ProviderResponse = provider.create_message(
            system=CLASSIFICATION_PROMPT,
            messages=[{"role": "user", "content": text}],
            model=settings.classifier_model,
        )

        if not response.content:
            return "Other"

        result = json.loads(response.content[0].text)
        category = result.get("category", "Other")
        confidence = float(result.get("confidence", 0.0))

        # Only accept high-confidence predictions
        if confidence >= 0.7 and category in CUAD_CATEGORIES:
            return category
        return "Other"
    except (json.JSONDecodeError, KeyError, ValueError):
        return "Other"
    except Exception as e:
        # Handle auth errors, rate limits, etc. gracefully during pilot
        print(f"  [Classifier warning] {type(e).__name__}: {e}")
        return "Other"


async def classify_batch(texts: list[str]) -> list[str]:
    """Classify multiple clauses efficiently.

    Note: For production bulk classification, use Anthropic's Batch API.
    This sequential version is fine for pilot-scale ingestion.
    """
    results = []
    for text in texts:
        category = await classify_clause(text)
        results.append(category)
    return results


if __name__ == "__main__":
    # Quick test
    import asyncio

    test_clauses = [
        "This Agreement shall be governed by the laws of the State of Delaware.",
        "Either party may terminate this Agreement for convenience upon 30 days written notice.",
        "The total liability of either party shall not exceed the fees paid under this Agreement.",
        "The Receiving Party shall not disclose any Confidential Information to third parties.",
    ]

    async def test():
        for clause in test_clauses:
            cat = await classify_clause(clause)
            print(f"[{cat}] {clause[:80]}...")

    asyncio.run(test())