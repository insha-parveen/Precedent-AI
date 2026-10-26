#!/usr/bin/env python3
"""Query the skill_runs table to see session history with all columns."""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from precedent.db import get_pool

async def main():
    """Query and display skill_runs data with all columns."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # First, get the count
            count = await conn.fetchval('SELECT COUNT(*) FROM skill_runs')
            print(f"Total rows in skill_runs: {count}")

            if count == 0:
                print("No skill runs found in the database.")
                return

            # Get all rows with all columns
            rows = await conn.fetch('''
                SELECT id, ts, skill_name, user_query, model, tool_calls,
                       cited_doc_ids, grounded, input_tokens, output_tokens,
                       cost_usd, latency_ms, error
                FROM skill_runs
                ORDER BY ts DESC
            ''')

            print(f"\nAll {len(rows)} skill runs:")
            print("=" * 120)

            for i, row in enumerate(rows, 1):
                print(f"\n--- Run {i} (ID: {row['id']}) ---")
                print(f"Timestamp: {row['ts']}")
                print(f"Skill: {row['skill_name'] or 'None'}")
                print(f"User Query: {row['user_query']}")
                print(f"Model: {row['model']}")
                print(f"Grounded: {row['grounded']}")
                print(f"Input Tokens: {row['input_tokens']}, Output Tokens: {row['output_tokens']}")
                print(f"Cost: ${float(row['cost_usd']):.6f}")
                print(f"Latency: {row['latency_ms']} ms")
                if row['error']:
                    print(f"Error: {row['error']}")
                if row['tool_calls'] and str(row['tool_calls']) not in ['[]', 'None']:
                    print(f"Tool Calls: {row['tool_calls']}")
                if row['cited_doc_ids'] and str(row['cited_doc_ids']) not in ['{}', 'None']:
                    print(f"Cited Doc IDs: {row['cited_doc_ids']}")

    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'pool' in locals():
            await pool.close()

if __name__ == "__main__":
    asyncio.run(main())