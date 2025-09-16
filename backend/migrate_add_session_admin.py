#!/usr/bin/env python3
"""
Migration: Add session_admin_id to chat_sessions
- Adds nullable column session_admin_id (FK to users.id)
- Backfills existing rows to current owner (user_id) to make them their own session admin
Usage:
    python migrate_add_session_admin.py
"""
from sqlalchemy import text
from database import sync_engine

def column_exists(conn) -> bool:
    result = conn.execute(text(
        """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'chat_sessions' 
        AND column_name = 'session_admin_id'
        """
    ))
    return result.fetchone() is not None

def add_column(conn):
    conn.execute(text(
        """
        ALTER TABLE chat_sessions 
        ADD COLUMN session_admin_id VARCHAR NULL
        """
    ))
    conn.commit()


def backfill(conn):
    # Set session_admin_id to the session owner for existing rows
    conn.execute(text(
        """
        UPDATE chat_sessions
        SET session_admin_id = user_id
        WHERE session_admin_id IS NULL
        """
    ))
    conn.commit()


def main():
    with sync_engine.connect() as conn:
        if column_exists(conn):
            print("✓ session_admin_id already exists")
        else:
            print("Adding session_admin_id column...")
            add_column(conn)
            print("✓ Added column")
        print("Backfilling existing rows...")
        backfill(conn)
        print("✓ Backfill complete")

if __name__ == "__main__":
    main()