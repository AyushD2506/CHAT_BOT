#!/usr/bin/env python3
"""
Quick Fix: Add Internet Search Column
====================================

This is a quick fix script to add the missing enable_internet_search column
to the chat_sessions table. Run this immediately to fix the current error.

Usage:
    python quick_fix_internet_search.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

def quick_fix():
    """Quickly add the missing column"""
    print("Quick Fix: Adding enable_internet_search column...")
    
    try:
        from database import sync_engine
        from sqlalchemy import text
        
        with sync_engine.connect() as conn:
            # Add the column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE chat_sessions 
                ADD COLUMN IF NOT EXISTS enable_internet_search BOOLEAN DEFAULT FALSE
            """))
            
            # Set all existing sessions to have internet search disabled
            conn.execute(text("""
                UPDATE chat_sessions 
                SET enable_internet_search = FALSE 
                WHERE enable_internet_search IS NULL
            """))
            
            conn.commit()
            
            print("✓ Successfully added enable_internet_search column")
            print("✓ All existing sessions set to have internet search disabled")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    if quick_fix():
        print("\n✅ Quick fix completed! You can now restart the backend server.")
    else:
        print("\n❌ Quick fix failed. Please check the error above.")
        sys.exit(1)
