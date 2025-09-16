#!/usr/bin/env python3
"""
Database Migration: Add Internet Search Column
=============================================

This script adds the enable_internet_search column to the chat_sessions table.
Run this script after updating the models to add the new column to the database.

Usage:
    python migrate_add_internet_search.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from database import sync_engine
from sqlalchemy import text

def add_internet_search_column():
    """Add enable_internet_search column to chat_sessions table"""
    print("Adding enable_internet_search column to chat_sessions table...")
    
    try:
        with sync_engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' 
                AND column_name = 'enable_internet_search'
            """))
            
            if result.fetchone():
                print("✓ Column 'enable_internet_search' already exists")
                return True
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE chat_sessions 
                ADD COLUMN enable_internet_search BOOLEAN DEFAULT FALSE
            """))
            
            # Commit the transaction
            conn.commit()
            
            print("✓ Successfully added enable_internet_search column")
            return True
            
    except Exception as e:
        print(f"✗ Error adding column: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    print("Verifying migration...")
    
    try:
        with sync_engine.connect() as conn:
            # Check if column exists and has correct type
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' 
                AND column_name = 'enable_internet_search'
            """))
            
            row = result.fetchone()
            if row:
                print(f"✓ Column found: {row[0]} ({row[1]}) with default: {row[2]}")
                return True
            else:
                print("✗ Column not found")
                return False
                
    except Exception as e:
        print(f"✗ Error verifying migration: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("Database Migration: Add Internet Search Column")
    print("=" * 60)
    
    # Add the column
    if not add_internet_search_column():
        print("Migration failed!")
        return False
    
    # Verify the migration
    if not verify_migration():
        print("Migration verification failed!")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Restart the backend server")
    print("2. Test creating a new session with internet search enabled")
    print("3. Verify the admin panel shows the internet search toggle")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
