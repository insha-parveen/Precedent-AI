import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from precedent.db import get_pool

async def main():
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Query the 10 most recent rows from skill_runs table
        query = """
        SELECT id, ts, skill_name, user_query, model, tool_calls, cited_doc_ids,
               grounded, input_tokens, output_tokens, cost_usd, latency_ms, error
        FROM skill_runs
        ORDER BY ts DESC
        LIMIT 10
        """
        rows = await conn.fetch(query)

        if not rows:
            print("No rows found in skill_runs table")
            return

        # Print header
        print(f"{'ID':<5} {'Timestamp':<25} {'Skill Name':<20} {'User Query':<30} {'Model':<15} {'Grounded':<8} {'Latency(ms)':<12}")
        print("-" * 120)

        # Print each row
        for row in rows:
            # Truncate long fields for display
            skill_name = (row['skill_name'] or 'NULL')[:19]
            user_query = (row['user_query'] or '')[:29]
            model = row['model'][:14] if row['model'] else 'NULL'
            grounded = str(row['grounded'])
            latency = str(row['latency_ms'])

            print(f"{row['id']:<5} {str(row['ts']):<25} {skill_name:<20} {user_query:<30} {model:<15} {grounded:<8} {latency:<12}")

if __name__ == "__main__":
    asyncio.run(main())