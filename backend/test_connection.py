import asyncio
import sys
from database import get_db, init_db, async_engine
from models import User, ChatSession, Document, ChatMessage
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

async def test_database_connection():
    """Test PostgreSQL database connection and setup"""
    print("Testing PostgreSQL Database Connection...")
    print("=" * 50)
    
    try:
        # Test basic connection
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ PostgreSQL Connection: SUCCESS")
            print(f"📊 Version: {version[0]}")
            
        # Test database initialization
        print("\n🔧 Initializing database tables...")
        await init_db()
        print("✅ Database tables created/verified")
        
        # Test table access
        async with async_engine.begin() as conn:
            # Check if tables exist
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            result = await conn.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            print(f"\n📋 Tables found: {len(tables)}")
            for table in tables:
                print(f"   - {table}")
        
        # Test CRUD operations
        print(f"\n🧪 Testing database operations...")
        async for db in get_db():
            # Test user creation
            test_user = User(
                username="test_connection",
                email="test@example.com",
                password_hash="test_hash",
                is_admin=False
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            print(f"✅ User creation: SUCCESS (ID: {test_user.id})")
            
            # Test user query
            result = await db.execute(
                select(User).where(User.username == "test_connection")
            )
            found_user = result.scalar_one_or_none()
            if found_user:
                print(f"✅ User query: SUCCESS")
            else:
                print(f"❌ User query: FAILED")
            
            # Clean up test user
            await db.delete(found_user)
            await db.commit()
            print(f"✅ User deletion: SUCCESS")
            
            break  # Exit the async generator
        
        print(f"\n🎉 All tests passed! PostgreSQL is ready for the RAG Chatbot.")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

async def test_environment_variables():
    """Test that all required environment variables are set"""
    print("Testing Environment Variables...")
    print("=" * 50)
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        ("DB_HOST", "Database host"),
        ("DB_PORT", "Database port"),
        ("DB_NAME", "Database name"),
        ("DB_USER", "Database user"),
        ("DB_PASSWORD", "Database password"),
        ("GROQ_API_KEY", "ChatGroq API key"),
        ("SECRET_KEY", "JWT secret key")
    ]
    
    all_good = True
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            display_value = "***" if "PASSWORD" in var_name or "KEY" in var_name else value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: NOT SET ({description})")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("RAG Chatbot - PostgreSQL Database Test")
    print("=" * 60)
    
    # Test environment variables first
    env_ok = asyncio.run(test_environment_variables())
    
    if not env_ok:
        print("\n⚠️  Please check your .env file and set missing variables.")
        sys.exit(1)
    
    print()  # Add spacing
    
    # Test database connection
    db_ok = asyncio.run(test_database_connection())
    
    if db_ok:
        print("\n🚀 System is ready! You can now:")
        print("   1. Run: python create_demo_users.py")
        print("   2. Run: python main.py")
        print("   3. Access the API at: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("\n❌ Database setup failed. Please check:")
        print("   1. PostgreSQL is running")
        print("   2. Database credentials in .env file")
        print("   3. Database 'rag_chatbot' exists")
        print("   4. Network connectivity to database")
        sys.exit(1)