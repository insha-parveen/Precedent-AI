# Supabase Setup for Precedent

## Prerequisites

1. [Supabase CLI](https://supabase.com/docs/guides/cli) installed
2. Supabase account (free tier available)

## Quick Start

### 1. Create a Supabase project

```bash
# Option A: Via CLI (requires login)
supabase login
supabase init
supabase link --project-ref <your-project-ref>

# Option B: Via Dashboard
# 1. Go to https://supabase.com/dashboard
# 2. Create new project
# 3. Note your project reference (e.g., `abcdefghijklmnop`)
```

### 2. Enable pgvector extension

In Supabase Dashboard → Database → Extensions, enable:

- `vector` (pgvector)
- `pg_trgm`

Or via SQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 3. Apply migrations

```bash
# From project root
supabase db push
```

Or manually run the SQL in `supabase/migrations/0001_initial_schema.sql` in the Supabase SQL Editor.

### 4. Get connection string

In Supabase Dashboard → Settings → Database:

- Copy the **Connection String** (Transaction mode, port 6543)
- Format: `postgresql://postgres:<password>@db.<project-ref>.supabase.co:6543/postgres`

### 5. Configure environment variables

Add to your `.env` or Vercel environment variables:

```env
DATABASE_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:6543/postgres
# or use the session pooler (port 5432) for long-running connections
```

## Free Tier Limits

- Database: 500 MB
- Bandwidth: 5 GB/month
- API requests: 50,000/month
- The pgvector extension is included

## Local Development

For local development with Docker:

```bash
docker compose up -d
# Uses local Postgres on port 5434 (see docker-compose.yml)
```

## Connection Pooling

Supabase provides two pooler modes:

- **Transaction mode (port 6543)**: Recommended for serverless functions (Vercel)
- **Session mode (port 5432)**: For long-running connections

For Vercel deployment, use the transaction pooler.

## Troubleshooting

### "pgvector not found" error

Ensure the `vector` extension is enabled in Supabase Dashboard → Database → Extensions.

### Connection timeout

- Check IP allowlist in Supabase Dashboard → Settings → Database
- Use `0.0.0.0/0` for development (or your specific IP)

### Migration conflicts

If you have existing data, create a new migration file instead of modifying `0001_initial_schema.sql`.
