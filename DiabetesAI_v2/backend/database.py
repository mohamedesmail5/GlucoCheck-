"""
DiabetesAI — Database Layer (Supabase)
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.environ.get(
    "SUPABASE_URL",
    "https://hvarbaylkygctkindmsb.supabase.co"
)
SUPABASE_SERVICE_KEY: str = os.environ.get(
    "SUPABASE_SERVICE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2YXJiYXlsa3lnY3RraW5kbXNiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTU1OTk4NSwiZXhwIjoyMDkxMTM1OTg1fQ.uHXUezhElPKP5uxE8_Bxy2Lp_76LFIjhnfR9kTTMhjc"
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def init_db():
    """Create tables if they don't exist (run once)."""
    # Tables are managed via Supabase dashboard / migrations
    # This function verifies connection
    try:
        supabase.table("users").select("id").limit(1).execute()
        print("✓ Supabase connected")
    except Exception as e:
        print(f"⚠ Supabase connection warning: {e}")


# ─── SQL Schema (run in Supabase SQL Editor) ──────────────────────────────────
SCHEMA_SQL = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email        TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name    TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions table (chat sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    title        TEXT DEFAULT 'جلسة جديدة',
    grade        INTEGER DEFAULT NULL,      -- 0,1,2,3
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id   UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role         TEXT CHECK(role IN ('user','agent')) NOT NULL,
    content      TEXT NOT NULL,
    image_url    TEXT DEFAULT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Diagnoses table
CREATE TABLE IF NOT EXISTS diagnoses (
    id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id   UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    grade        INTEGER NOT NULL,
    confidence   FLOAT,
    source       TEXT CHECK(source IN ('text','image','combined')),
    details      JSONB DEFAULT '{}',
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Policies
ALTER TABLE users    ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnoses ENABLE ROW LEVEL SECURITY;
"""
