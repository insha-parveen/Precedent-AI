import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from precedent.db import get_pool

async def main():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Test connection
            result = await conn.fetchval('SELECT 1')
            print(f"Database connection successful: {result}")

            # Check if skill_runs table has any data
            count = await conn.fetchval('SELECT COUNT(*) FROM skill_runs')
            print(f"Number of rows in skill_runs: {count}")

            if count > 0:
                # Get the 10 most recent rows
                query = """
                SELECT id, ts, skill_name, user_query, model, tool_calls, cited_doc_ids,
                       grounded, input_tokens, output_tokens, cost_usd, latency_ms, error
                FROM skill_runs
                ORDER BY ts DESC
                LIMIT 10
                """
                rows = await conn.fetch(query)

                print("\n10 most recent rows:")
                print("=" * 120)
                for row in rows:
                    print(f"ID: {row['id']}")
                    print(f"Timestamp: {row['ts']}")
                    print(f"Skill Name: {row['skill_name'] or 'NULL'}")
                    print(f"User Query: {row['user_query'][:100]}{'...' if len(row['user_query']) > 100 else ''}")
                    print(f"Model: {row['model']}")
                    print(f"Grounded: {row['grounded']}")
                    print(f"Latency (ms): {row['latency_ms']}")
                    print(f"Cost (USD): {row['cost_usd']}")
                    print(f"Input Tokens: {row['input_tokens']}")
                    print(f"Output Tokens: {row['output_tokens']}")
                    if row['error']:
                        print(f"Error: {row['error'][:100]}{'...' if len(row['error']) > 100 else ''}")
                    print("-" * 80)
            else:
                print("No data found in skill_runs table")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())