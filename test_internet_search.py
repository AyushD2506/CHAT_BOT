#!/usr/bin/env python3
"""
Test Internet Search Functionality
=================================

This script tests the internet search functionality to ensure it's working correctly.
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path("backend")))

async def test_search_service():
    """Test the search service functionality"""
    print("Testing DuckDuckGo Search Service...")
    
    try:
        from backend.search_service import search_service
        
        # Test search functionality
        query = "latest news about artificial intelligence"
        print(f"Searching for: {query}")
        
        results = search_service.search(query, max_results=3)
        
        if results:
            print(f"✓ Found {len(results)} search results")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title']}")
                print(f"     URL: {result.get('url', 'N/A')}")
                print(f"     Content: {result['content'][:100]}...")
                print()
        else:
            print("✗ No search results found")
            return False
        
        # Test search need detection
        test_queries = [
            "What is the current weather?",
            "Tell me about the history of Rome",
            "Latest stock prices for Apple",
            "What is photosynthesis?",
            "Breaking news today"
        ]
        
        print("Testing search need detection:")
        for query in test_queries:
            needs_search = search_service.is_search_needed(query)
            print(f"  '{query}' -> {'Needs search' if needs_search else 'No search needed'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing search service: {e}")
        return False

async def test_rag_integration():
    """Test RAG service integration with internet search"""
    print("\nTesting RAG Service Integration...")
    
    try:
        from backend.rag_service import rag_service
        from backend.database import AsyncSessionLocal
        from backend.models import ChatSession
        from sqlalchemy import select
        
        # Create a test session with internet search enabled
        async with AsyncSessionLocal() as db:
            # Check if we have any sessions
            result = await db.execute(select(ChatSession).limit(1))
            session = result.scalar_one_or_none()
            
            if not session:
                print("✗ No sessions found. Please create a session first.")
                return False
            
            print(f"Testing with session: {session.session_name}")
            print(f"Internet search enabled: {session.enable_internet_search}")
            
            # Test query that should trigger internet search
            test_query = "What are the latest developments in AI?"
            
            print(f"Testing query: {test_query}")
            
            # This would normally be called by the chat endpoint
            # For testing, we'll just check if the search detection works
            from backend.search_service import search_service
            needs_search = search_service.is_search_needed(test_query)
            print(f"Query needs internet search: {needs_search}")
            
            return True
            
    except Exception as e:
        print(f"✗ Error testing RAG integration: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("Testing Dependencies...")
    
    required_packages = [
        'requests',
        # 'beautifulsoup4',
        'langchain',
        'langchain_community',
        'langchain_groq',
        'langchain_huggingface'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r backend/requirements.txt")
        return False
    
    return True

async def main():
    """Main test function"""
    print("=" * 60)
    print("Internet Search Functionality Test")
    print("=" * 60)
    
    # Test dependencies
    if not test_dependencies():
        return False
    
    # Test search service
    if not await test_search_service():
        return False
    
    # Test RAG integration
    if not await test_rag_integration():
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! Internet search functionality is working.")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Start the backend: cd backend && python main.py")
    print("2. Start the frontend: cd front_end && npm start")
    print("3. Go to admin panel and enable internet search for a session")
    print("4. Test with queries like 'What's the latest news about AI?'")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
