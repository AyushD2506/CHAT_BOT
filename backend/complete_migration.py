#!/usr/bin/env python3
"""
Complete Database Migration for Internet Search
==============================================

This script performs a complete migration to add internet search functionality:
1. Adds the enable_internet_search column to chat_sessions
2. Updates existing sessions to have internet search disabled by default
3. Verifies the migration was successful

Usage:
    python complete_migration.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from database import sync_engine, async_engine
from sqlalchemy import text
from models import ChatSession
from sqlalchemy.orm import sessionmaker

def add_internet_search_column():
    """Add enable_internet_search column to chat_sessions table"""
    print("Step 1: Adding enable_internet_search column...")
    
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
            
            # Add the column with default value
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

def update_existing_sessions():
    """Update existing sessions to have internet search disabled"""
    print("Step 2: Updating existing sessions...")
    
    try:
        with sync_engine.connect() as conn:
            # Count existing sessions
            result = conn.execute(text("SELECT COUNT(*) FROM chat_sessions"))
            session_count = result.scalar()
            
            if session_count == 0:
                print("✓ No existing sessions to update")
                return True
            
            # Update all existing sessions to have internet search disabled
            conn.execute(text("""
                UPDATE chat_sessions 
                SET enable_internet_search = FALSE 
                WHERE enable_internet_search IS NULL
            """))
            
            conn.commit()
            
            print(f"✓ Updated {session_count} existing sessions (internet search disabled)")
            return True
            
    except Exception as e:
        print(f"✗ Error updating sessions: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    print("Step 3: Verifying migration...")
    
    try:
        with sync_engine.connect() as conn:
            # Check if column exists and has correct type
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' 
                AND column_name = 'enable_internet_search'
            """))
            
            row = result.fetchone()
            if not row:
                print("✗ Column not found")
                return False
            
            print(f"✓ Column found: {row[0]} ({row[1]}) with default: {row[2]}, nullable: {row[3]}")
            
            # Check that all sessions have the column set
            result = conn.execute(text("""
                SELECT COUNT(*) FROM chat_sessions 
                WHERE enable_internet_search IS NULL
            """))
            
            null_count = result.scalar()
            if null_count > 0:
                print(f"✗ {null_count} sessions still have NULL values")
                return False
            
            print("✓ All sessions have enable_internet_search set")
            
            # Show summary of sessions
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN enable_internet_search = TRUE THEN 1 ELSE 0 END) as enabled_sessions,
                    SUM(CASE WHEN enable_internet_search = FALSE THEN 1 ELSE 0 END) as disabled_sessions
                FROM chat_sessions
            """))
            
            stats = result.fetchone()
            print(f"✓ Session summary: {stats[0]} total, {stats[1]} with internet search enabled, {stats[2]} disabled")
            
            return True
            
    except Exception as e:
        print(f"✗ Error verifying migration: {e}")
        return False

def test_model_integration():
    """Test that the model integration works correctly"""
    print("Step 4: Testing model integration...")
    
    try:
        # Test creating a session with internet search enabled
        SessionLocal = sessionmaker(bind=sync_engine)
        with SessionLocal() as session:
            # Create a test session
            test_session = ChatSession(
                session_name="Test Internet Search Session",
                user_id="test-user-id",
                enable_internet_search=True
            )
            
            session.add(test_session)
            session.commit()
            session.refresh(test_session)
            
            print(f"✓ Created test session with ID: {test_session.id}")
            print(f"✓ Internet search enabled: {test_session.enable_internet_search}")
            
            # Clean up test session
            session.delete(test_session)
            session.commit()
            
            print("✓ Test session cleaned up")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing model integration: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 70)
    print("Complete Database Migration for Internet Search Feature")
    print("=" * 70)
    
    # Step 1: Add the column
    if not add_internet_search_column():
        print("\n❌ Migration failed at step 1!")
        return False
    
    # Step 2: Update existing sessions
    if not update_existing_sessions():
        print("\n❌ Migration failed at step 2!")
        return False
    
    # Step 3: Verify migration
    if not verify_migration():
        print("\n❌ Migration failed at step 3!")
        return False
    
    # Step 4: Test model integration
    if not test_model_integration():
        print("\n❌ Migration failed at step 4!")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 Migration completed successfully!")
    print("=" * 70)
    
    print("\nNext steps:")
    print("1. Restart the backend server: cd backend && python main.py")
    print("2. Start the frontend: cd front_end && npm start")
    print("3. Go to admin panel and test creating sessions with internet search")
    print("4. Test the internet search functionality")
    
    print("\nFeatures now available:")
    print("• Internet search toggle in admin panel")
    print("• Session-based internet search control")
    print("• Automatic search detection for current information queries")
    print("• Combined responses from documents and internet")
    
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
