"""Ingest SEC EDGAR filings into the hybrid index.

Pulls real filed contracts (merger agreements, credit agreements) from SEC EDGAR,
chunks them at clause boundaries using heuristics, classifies clauses against
the CUAD 41-category taxonomy using Haiku, and loads into the same tables as CUAD.

SEC API: https://data.sec.gov/submissions/CIK{cik}.json (10 req/sec, no auth)
Exhibit download: https://www.sec.gov/Archives/edgar/data/{CIK}/{accession_no}/{filename}

Target filing types:
- 8-K: exhibits 10.1, 10.2 (material agreements)
- 10-K / 10-Q: credit agreement exhibits
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiohttp
import asyncpg

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.precedent.config import settings  # noqa: E402
from src.precedent.db import get_pool  # noqa: E402
from src.precedent.classifier import classify_clause  # noqa: E402

# Conservative rate limiting: SEC allows 10 req/sec, we'll do ~5/sec
REQUEST_DELAY = 0.2

# CIKs for major companies with frequent material contracts
TARGET_CIKS = {
    "0000320193": "Apple Inc.",
    "0000789019": "Microsoft Corporation",
    "0001018724": "Amazon.com Inc.",
    "0001326801": "Meta Platforms Inc.",
    "0001652044": "Alphabet Inc. (Google)",
    "0000019617": "American Express Co.",
    "0000066740": "Bank of America Corporation",
    "0000070858": "Berkshire Hathaway Inc.",
    "0000019887": "Boeing Co.",
    "0000354950": "Caterpillar Inc.",
    "0000034088": "Exxon Mobil Corp",
    "0000732712": "Qualcomm Inc",
    "0000002178": "Broadcom Inc",
}

# Filing types that contain material contracts as exhibits
TARGET_FILING_TYPES = {"8-K", "10-K", "10-Q"}

# Exhibit numbers that typically contain contracts (check prefix 10.)
def is_target_exhibit(ex_num: str) -> bool:
    return ex_num.startswith("10.")

MAX_DOCUMENTS = 30  # Limit for pilot ingestion
MAX_FILINGS_PER_CIK = 5


@dataclass
class Filing:
    accession_number: str  # No-dash
    raw_accession: str    # Dashed
    cik: str
    filing_date: str
    form: str
    primary_document: str
    exhibit_files: dict[str, str]  # exhibit_number -> filename


@dataclass
class ClauseChunk:
    text: str
    clause_type: str = "Other"
    char_start: Optional[int] = None
    char_end: Optional[int] = None


SEC_USER_AGENT = "Precedent-AI/1.0 (research; contact: precedent-ai-dev@example.com)"

async def fetch_url(session: aiohttp.ClientSession, url: str, is_json: bool = True) -> dict | str:
    """Fetch URL with rate limiting and error handling."""
    await asyncio.sleep(REQUEST_DELAY)
    async with session.get(url, headers={"User-Agent": SEC_USER_AGENT}) as resp:
        if resp.status == 429:
            await asyncio.sleep(2.0)
            return await fetch_url(session, url, is_json)
        if resp.status == 404:
            raise FileNotFoundError(f"404 Not Found: {url}")
        resp.raise_for_status()
        return await resp.json() if is_json else await resp.text()

async def get_company_filings(session: aiohttp.ClientSession, cik: str) -> list[Filing]:
    """Fetch recent filings for a CIK and discover exhibits from primary documents."""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    data = await fetch_url(session, url, is_json=True)

    filings = []
    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return filings

    for i, form in enumerate(recent.get("form", [])):
        if form not in TARGET_FILING_TYPES:
            continue

        raw_accession = recent["accessionNumber"][i]
        accession = raw_accession.replace("-", "")
        filing_date = recent["filingDate"][i]
        primary_doc = recent["primaryDocument"][i]

        # Fetch the primary document HTML to find exhibit links
        # URL format: https://www.sec.gov/Archives/edgar/data/{CIK_10digit}/{accession_no}/{primary_doc}
        primary_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{raw_accession.replace('-', '')}/{recent['primaryDocument'][i]}"

        try:
            primary_html = await fetch_url(session, primary_url, is_json=False)
            exhibits = {}

            # Parse primary document HTML for exhibit links
            # SEC uses various naming conventions: a10-qexhibit31106272026.htm, ex10-1.htm, etc.
            href_pattern = re.compile(r'href=["\']([^"\']*\.(?:htm|html|txt))["\']', re.IGNORECASE)
            for match in href_pattern.findall(primary_html):
                filename = match.split('/')[-1]  # Get just the filename (match is a string from findall)
                filename_lower = filename.lower()
                # Check for various exhibit patterns: a10-qexhibit311..., ex10-1.htm, etc.
                # The key is finding "exhibit" or "ex" followed by numbers
                if 'ex' in filename_lower and any(filename_lower.endswith(ext) for ext in [".htm", ".html", ".txt"]):
                    # Try to extract exhibit number
                    # Pattern 1: ex10-1 or ex99-1 (traditional)
                    # Pattern 2: a10-qexhibit311... (modern SEC format: a10-qexhibit...)
                    ex_num = None

                    # Try pattern: ex10-1 or ex99-1
                    match = re.search(r'ex(\d+)[-_\.]', filename_lower)
                    if match:
                        ex_num = match.group(1)

                    # Try pattern: 10-qexhibit or 10-kexhibit or a10-qexhibit
                    if not ex_num:
                        match = re.search(r'[a-z]?(\d+)[-_\.]?[kq]exhibit', filename_lower)
                        if match:
                            ex_num = match.group(1)

                    # Try pattern: exhibit311 -> 311 (less likely to be 10.x)
                    if not ex_num:
                        match = re.search(r'exhibit(\d+)', filename_lower)
                        if match:
                            ex_num = match.group(1)

                    if ex_num:
                        # Check if it's a target exhibit (10.x)
                        if ex_num == "10":
                            exhibits[ex_num] = filename

            if not exhibits:
                print(f"  No target exhibits found in primary doc for {raw_accession}")
                continue

            # Parse date string to date object
            from datetime import datetime
            filing_date_obj = datetime.strptime(filing_date, "%Y-%m-%d").date()

            filings.append(Filing(
                accession_number=raw_accession.replace("-", ""),
                raw_accession=raw_accession,
                cik=cik,
                filing_date=filing_date_obj,
                form=form,
                primary_document=primary_doc,
                exhibit_files=exhibits,
            ))

        except Exception as e:
            print(f"  Warning: Could not fetch primary doc for filing {raw_accession}: {e}")
            continue

        if len(filings) >= MAX_FILINGS_PER_CIK:
            break

    return filings


async def download_exhibit(session: aiohttp.ClientSession, cik: str, accession: str, filename: str) -> str:
    """Download exhibit text from SEC Archives."""
    # URL format: https://www.sec.gov/Archives/edgar/data/{CIK_10digit}/{accession_no}/{filename}
    # CIK needs to be 10-digit with leading zeros removed for path
    cik_path = cik.lstrip('0')
    accession_path = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession.replace('-', '')}/{filename}"

    await asyncio.sleep(REQUEST_DELAY)
    async with session.get(url, headers={"User-Agent": SEC_USER_AGENT}) as resp:
        if resp.status == 404:
            # Try without .txt extension variations
            for ext in [".txt", ".htm", ".html", ""]:
                alt_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession.replace('-', '')}/{filename}{ext}"
                async with session.get(alt_url, headers={"User-Agent": SEC_USER_AGENT}) as r:
                    if r.status == 200:
                        return await r.text()
            raise FileNotFoundError(f"Exhibit not found: {filename}")
        resp.raise_for_status()
        return await resp.text()


def extract_text_from_html(html: str) -> str:
    """Extract readable text from SEC HTML exhibit."""
    # Remove script/style tags
    html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace common tags with newlines
    html = re.sub(r"</(p|div|br|tr|li)>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode HTML entities
    html = html.replace("&nbsp;", " ").replace("&", "&").replace("<", "<").replace(">", ">")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", html)
    return text.strip()


def chunk_into_clauses(text: str) -> list[ClauseChunk]:
    """Chunk contract text into clauses using heuristic section headers."""
    # Split on major section boundaries
    section_pattern = r"(?=(?:^|\n)\s*(?:Section|Article|SECTION|ARTICLE)\s+[\dIVX]+\.?\s)"
    sections = re.split(section_pattern, text, flags=re.IGNORECASE | re.MULTILINE)

    chunks = []
    char_pos = 0

    for section in sections:
        if not section.strip():
            continue

        # Further split on numbered sub-clauses
        sub_pattern = r"(?=(?:^|\n)\s*(?:\(\w+\)|\d+\.\s))"
        sub_clauses = re.split(sub_pattern, section, flags=re.MULTILINE)

        for clause in sub_clauses:
            clause = clause.strip()
            if len(clause) < 50:  # Skip tiny fragments
                continue

            chunks.append(ClauseChunk(
                text=clause[:2000],  # Cap at 2000 chars for classification
                char_start=char_pos,
                char_end=char_pos + len(clause),
            ))
            char_pos += len(clause) + 1

    # If no sections found, fall back to paragraph chunking
    if not chunks:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
        for p in paragraphs:
            chunks.append(ClauseChunk(text=p[:2000]))

    return chunks[:50]  # Cap at 50 clauses per document


async def ingest_edgar_document(
    pool: asyncpg.Pool,
    cik: str,
    company_name: str,
    filing: Filing,
    exhibit_num: str,
    exhibit_text: str,
) -> int:
    """Ingest a single EDGAR exhibit as a document with classified clauses."""
    clauses = chunk_into_clauses(exhibit_text)
    if not clauses:
        return 0

    # Classify clauses in batches
    print(f"  Classifying {len(clauses)} clauses from {filing.raw_accession} exhibit {exhibit_num}...")
    for clause in clauses:
        try:
            clause.clause_type = await classify_clause(clause.text)
        except Exception as e:
            print(f"  [Classifier warning] {type(e).__name__}: {e}")
            clause.clause_type = "Other"

    # Insert document
    title = f"{company_name} - {filing.form} Exhibit {exhibit_num} ({filing.filing_date})"
    source_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{filing.raw_accession}/{exhibit_num}"

    async with pool.acquire() as conn:
        doc_id = await conn.fetchval(
            """
            INSERT INTO documents (source, external_id, title, doc_type, parties, filing_date, raw_text, access_group, source_url)
            VALUES ('edgar', $1, $2, $3, $4, $5, $6, 'public', $7)
            ON CONFLICT (source, external_id) DO UPDATE SET title = EXCLUDED.title
            RETURNING id
            """,
            f"{filing.raw_accession}-{exhibit_num}",
            title,
            filing.form,
            [company_name],
            filing.filing_date,
            exhibit_text[:10000],
            source_url,
        )

        # Insert clauses
        for clause in clauses:
            await conn.execute(
                """
                INSERT INTO clauses (document_id, clause_type, clause_text, char_start, char_end, access_group)
                VALUES ($1, $2, $3, $4, $5, 'public')
                """,
                doc_id,
                clause.clause_type,
                clause.text,
                clause.char_start,
                clause.char_end,
            )

    print(f"  -> Ingested document {doc_id} with {len(clauses)} clauses")
    return len(clauses)


async def main() -> None:
    print("=" * 60)
    print("SEC EDGAR Ingestion Pilot (Primary Document Parsing)")
    print("=" * 60)

    pool = await get_pool()

    async with aiohttp.ClientSession() as session:
        total_clauses = 0
        total_docs = 0

        for cik, company_name in TARGET_CIKS.items():
            if total_docs >= MAX_DOCUMENTS:
                break

            print(f"\n[{company_name}] Fetching filings...")
            try:
                filings = await get_company_filings(session, cik)
                print(f"  Found {len(filings)} relevant filings with exhibits")

                for filing in filings:
                    if total_docs >= MAX_DOCUMENTS:
                        break

                    for exhibit_num, exhibit_file in filing.exhibit_files.items():
                        if total_docs >= MAX_DOCUMENTS:
                            break

                        print(f"  Downloading {filing.form} exhibit {exhibit_num} ({filing.filing_date})...")
                        try:
                            raw_html = await download_exhibit(session, cik, filing.raw_accession, exhibit_file)
                            exhibit_text = extract_text_from_html(raw_html)

                            if len(exhibit_text) < 500:
                                print(f"    Skipping: too short ({len(exhibit_text)} chars)")
                                continue

                            clauses_added = await ingest_edgar_document(
                                pool, cik, company_name, filing, exhibit_num, exhibit_text
                            )
                            total_clauses += clauses_added
                            total_docs += 1

                        except Exception as e:
                            print(f"    Error: {e}")
                            continue

            except Exception as e:
                print(f"  Error fetching filings for {company_name}: {e}")
                continue

    print(f"\n{'=' * 60}")
    print(f"EDGAR Ingestion Complete!")
    print(f"Documents: {total_docs}")
    print(f"Clauses:   {total_clauses}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())