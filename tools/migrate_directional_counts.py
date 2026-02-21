"""
migrate_directional_counts.py  —  Phase 8 One-time DB Migration

Creates the directional_counts table in smart_net_db (local PostgreSQL).
Run ONCE before starting the system with Phase 8 enabled.

Usage:
    python tools/migrate_directional_counts.py
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Allow running from project root or tools/ dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

DB_PARAMS = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "dbname":   os.getenv("DB_NAME", "smart_net_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", ""),
}

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS directional_counts (
    id            SERIAL PRIMARY KEY,
    junction_id   TEXT        NOT NULL,
    phase         TEXT        NOT NULL,
    counts_json   JSONB       NOT NULL,
    recorded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Safe to run even if table already existed without recorded_at
ALTER TABLE directional_counts
    ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_dc_junction
    ON directional_counts (junction_id, recorded_at DESC);
"""

def run():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(CREATE_SQL)
        print("✅ directional_counts table created (or already exists).")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
