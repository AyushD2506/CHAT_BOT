#!/usr/bin/env python3
"""
Quick start script for RAG Chatbot system
This script helps you start the backend and provides instructions for the frontend
"""
import subprocess
import sys
import os
from pathlib import Path
import time

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_dependencies():
    """Check if basic dependencies are installed"""
    print("Checking dependencies...")
    
    try:
        import psycopg2
        print("✅ psycopg2 is installed")
    except ImportError:
        print("❌ psycopg2 not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
    
    try:
        import asyncpg
        print("✅ asyncpg is installed")
    except ImportError:
        print("❌ asyncpg not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "asyncpg"], check=True)
    
    try:
        import fastapi
        print("✅ FastAPI is installed")
    except ImportError:
        print("❌ FastAPI not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi"], check=True)
    
    return True

def start_backend():
    """Start the FastAPI backend"""
    backend_dir = Path(__file__).parent / "backend"
    
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        return False
    
    print("🚀 Starting FastAPI backend...")
    print("Backend will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the backend")
    print("-" * 60)
    
    try:
        # Change to backend directory and start the server
        os.chdir(backend_dir)
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n✋ Backend stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend failed to start: {e}")
        return False
    except FileNotFoundError:
        print("❌ main.py not found in backend directory")
        return False

def main():
    print_header("RAG Chatbot - Quick Start")
    
    print("This script will start the backend server.")
    print("For the frontend, you'll need to run it separately in another terminal.")
    
    # Check dependencies
    try:
        if not check_dependencies():
            sys.exit(1)
    except Exception as e:
        print(f"⚠️ Dependency check failed: {e}")
        print("Continuing anyway...")
    
    print()
    print("📋 Before starting, make sure:")
    print("1. PostgreSQL is installed and running")
    print("2. Environment variables are set in backend/.env")
    print("3. Database 'rag_chatbot' exists")
    print()
    
    response = input("Continue? (y/n): ").lower()
    if response != 'y':
        print("Setup cancelled.")
        sys.exit(0)
    
    # Start backend
    success = start_backend()
    
    if success:
        print_header("Backend Started Successfully!")
        print("\n🎉 Your RAG Chatbot backend is running!")
        print("\n📱 To start the frontend:")
        print("1. Open a new terminal/PowerShell window")
        print("2. Navigate to your project directory")
        print("3. Run: cd front_end")
        print("4. Run: npm install (if not done before)")
        print("5. Run: npm start")
        print("\n🌐 Access points:")
        print("• Frontend: http://localhost:3000")
        print("• Backend: http://localhost:8000")
        print("• API Docs: http://localhost:8000/docs")
        print("\n🔑 Login credentials:")
        print("• Admin: admin / admin123")
        print("• User: user / user123")
    else:
        print("\n❌ Failed to start the system")
        print("\nTroubleshooting tips:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify backend/.env file exists with correct database credentials")
        print("3. Run: python backend/setup_postgres.py")
        print("4. Run: python backend/test_connection.py")

if __name__ == "__main__":
    main()