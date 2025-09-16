#!/usr/bin/env python3
"""
Database Setup Test Script
=========================

This script tests if the database setup was successful by verifying:
1. Database connection
2. Table existence
3. Demo user creation
4. Basic functionality

Usage:
    python test_database_setup.py
"""

import sys
import asyncio
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from backend.database import sync_engine, async_engine, test_connection
        from backend.models import User, ChatSession, Document, ChatMessage
        from backend.auth_utils import verify_password
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        from backend.database import test_connection
        if test_connection():
            print("✓ Database connection successful")
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False

def test_tables_exist():
    """Test if all required tables exist"""
    print("Testing table existence...")
    try:
        from backend.database import sync_engine
        from sqlalchemy import text
        
        with sync_engine.connect() as conn:
            # Check for required tables
            required_tables = ['users', 'chat_sessions', 'documents', 'chat_messages', 'vector_stores', 'mcp_tools']
            
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('users', 'chat_sessions', 'documents', 'chat_messages', 'vector_stores', 'mcp_tools')
            """))
            
            existing_tables = [row[0] for row in result]
            missing_tables = set(required_tables) - set(existing_tables)
            
            if missing_tables:
                print(f"✗ Missing tables: {missing_tables}")
                return False
            else:
                print(f"✓ All required tables exist: {existing_tables}")
                return True
                
    except Exception as e:
        print(f"✗ Table check error: {e}")
        return False

def test_demo_users():
    """Test if demo users were created"""
    print("Testing demo users...")
    try:
        from backend.database import sync_engine
        from backend.models import User
        from sqlalchemy import select
        
        with sync_engine.connect() as conn:
            # Check for admin user
            result = conn.execute(select(User).where(User.username == "admin"))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("✗ Admin user not found")
                return False
            
            # Check for regular user
            result = conn.execute(select(User).where(User.username == "user"))
            regular_user = result.scalar_one_or_none()
            
            if not regular_user:
                print("✗ Regular user not found")
                return False
            
            # Check user properties
            if not admin_user.is_admin:
                print("✗ Admin user is not marked as admin")
                return False
            
            if regular_user.is_admin:
                print("✗ Regular user is incorrectly marked as admin")
                return False
            
            print("✓ Demo users created correctly")
            print(f"  - Admin: {admin_user.username} (admin: {admin_user.is_admin})")
            print(f"  - User: {regular_user.username} (admin: {regular_user.is_admin})")
            return True
            
    except Exception as e:
        print(f"✗ Demo user check error: {e}")
        return False

def test_password_hashing():
    """Test password hashing functionality"""
    print("Testing password hashing...")
    try:
        from backend.auth_utils import get_password_hash, verify_password
        
        test_password = "test123"
        hashed = get_password_hash(test_password)
        
        if not verify_password(test_password, hashed):
            print("✗ Password verification failed")
            return False
        
        if verify_password("wrong_password", hashed):
            print("✗ Wrong password was accepted")
            return False
        
        print("✓ Password hashing works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Password hashing error: {e}")
        return False

def test_async_functionality():
    """Test async database functionality"""
    print("Testing async functionality...")
    try:
        from backend.database import AsyncSessionLocal
        from backend.models import User
        from sqlalchemy import select
        
        async def test_async():
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.username == "admin"))
                user = result.scalar_one_or_none()
                return user is not None
        
        result = asyncio.run(test_async())
        if result:
            print("✓ Async database operations work")
            return True
        else:
            print("✗ Async database operations failed")
            return False
            
    except Exception as e:
        print(f"✗ Async functionality error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Database Setup Test")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("Error: Please run this script from the project root directory")
        return False
    
    tests = [
        test_imports,
        test_database_connection,
        test_tables_exist,
        test_demo_users,
        test_password_hashing,
        test_async_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        else:
            print(f"Test failed: {test.__name__}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All tests passed! Database setup is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the database setup.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
