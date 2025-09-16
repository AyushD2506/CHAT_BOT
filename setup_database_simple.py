#!/usr/bin/env python3
"""
Simple Database Setup Script for RAG Chatbot Project
====================================================

A simplified version of the database setup script with minimal user interaction.
Uses default values for most configuration options.

Usage:
    python setup_database_simple.py
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - Failed: {e.stderr}")
        return False

def create_default_env():
    """Create .env file with default values"""
    env_content = """# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_chatbot
DB_USER=postgres
DB_PASSWORD=postgres

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GROQ API Configuration
GROQ_API_KEY=
"""
    
    env_file = Path("backend/.env")
    with open(env_file, 'w') as f:
        f.write(env_content)
    print(f"✓ Created .env file with default values")

def main():
    """Main setup function"""
    print("=" * 50)
    print("RAG Chatbot - Simple Database Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("Error: Please run this script from the project root directory")
        return False
    
    # Install requirements
    if not run_command("pip install -r backend/requirements.txt", "Installing Python packages"):
        return False
    
    # Create .env file
    create_default_env()
    
    # Create database
    if not run_command("cd backend && python setup_postgres.py", "Creating database"):
        return False
    
    # Initialize tables and create demo users
    if not run_command("cd backend && python -c \"import asyncio; from database import init_db; asyncio.run(init_db())\"", "Creating database tables"):
        return False
    
    if not run_command("cd backend && python create_demo_users.py", "Creating demo users"):
        return False
    
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Start backend: cd backend && python main.py")
    print("2. Start frontend: cd front_end && npm install && npm start")
    print("3. Access: http://localhost:3000")
    print("\nLogin credentials:")
    print("Admin: admin / admin123")
    print("User: user / user123")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
