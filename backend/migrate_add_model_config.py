#!/usr/bin/env python3
"""
Migration: Add per-session model configuration columns to chat_sessions
=====================================================================
Adds columns used for provider/model selection and parameters:
- model_provider (varchar)
- model_name (varchar)
- model_temperature (float)
- model_max_output_tokens (integer, nullable)
- model_api_key (text, nullable)
- model_base_url (varchar, nullable)

Safe to run multiple times (uses IF NOT EXISTS checks).

Usage:
  python migrate_add_model_config.py
"""

from sqlalchemy import text
from database import sync_engine

DDL_STATEMENTS = [
    # Add columns if they do not exist
    text("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS model_provider VARCHAR(20) DEFAULT 'groq'
    """),
    text("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS model_name VARCHAR(200) DEFAULT 'llama-3.3-70b-versatile'
    """),
    text("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS model_temperature DOUBLE PRECISION DEFAULT 0.1
    """),
    text("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS model_max_output_tokens INTEGER
    """),
    text("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS model_api_key TEXT
    """),
    text("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS model_base_url VARCHAR(500)
    """),
]

POST_STMTS = [
    # Ensure existing rows have defaults for new non-sensitive fields
    text("""
        UPDATE chat_sessions
        SET 
          model_provider = COALESCE(model_provider, 'groq'),
          model_name = COALESCE(model_name, 'llama-3.3-70b-versatile'),
          model_temperature = COALESCE(model_temperature, 0.1)
    """),
]


def column_summary(conn):
    res = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'chat_sessions'
        ORDER BY column_name
    """))
    return list(res.fetchall())


def main():
    print("Starting migration: add model config columns to chat_sessions...")
    with sync_engine.connect() as conn:
        try:
            for stmt in DDL_STATEMENTS:
                conn.execute(stmt)
            for stmt in POST_STMTS:
                conn.execute(stmt)
            conn.commit()
            print("✓ Migration applied.")

            cols = column_summary(conn)
            names = {c[0] for c in cols}
            required = {
                'model_provider', 'model_name', 'model_temperature',
                'model_max_output_tokens', 'model_api_key', 'model_base_url'
            }
            missing = sorted(list(required - names))
            if missing:
                print(f"! Warning: missing columns not found after migration: {missing}")
            else:
                print("✓ Verified all model config columns exist.")
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    main()