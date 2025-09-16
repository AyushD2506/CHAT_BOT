#!/usr/bin/env python3
"""
Setup Help Script for RAG Chatbot Project
=========================================

This script provides information about all available setup options
and helps users choose the right approach for their needs.

Usage:
    python setup_help.py
"""

import sys
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def print_option(number, title, description, command, notes=""):
    """Print a setup option"""
    print(f"\n{number}. {title}")
    print(f"   {description}")
    print(f"   Command: {command}")
    if notes:
        print(f"   Notes: {notes}")

def check_environment():
    """Check the current environment"""
    print_header("Environment Check")
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Error: Not in project root directory")
        print("   Please run this script from the directory containing the 'backend' folder")
        return False
    
    print("✓ Project structure looks correct")
    
    # Check for existing .env file
    env_file = Path("backend/.env")
    if env_file.exists():
        print("✓ .env file already exists")
    else:
        print("⚠ .env file not found (will be created during setup)")
    
    # Check for requirements.txt
    req_file = Path("backend/requirements.txt")
    if req_file.exists():
        print("✓ requirements.txt found")
    else:
        print("❌ requirements.txt not found")
        return False
    
    return True

def show_setup_options():
    """Show all available setup options"""
    print_header("Available Setup Options")
    
    print_option(
        1,
        "Automated Setup (Recommended)",
        "Comprehensive setup with interactive configuration and full verification",
        "python setup_database.py",
        "Best for first-time setup or when you want full control over configuration"
    )
    
    print_option(
        2,
        "Simple Setup",
        "Quick setup with default values and minimal interaction",
        "python setup_database_simple.py",
        "Fastest option, uses default password 'postgres'"
    )
    
    print_option(
        3,
        "Manual Setup",
        "Step-by-step manual setup process",
        "Follow instructions in DATABASE_SETUP_README.md",
        "Best for learning or when you need to customize specific steps"
    )
    
    print_option(
        4,
        "Test Setup",
        "Verify that your database setup is working correctly",
        "python test_database_setup.py",
        "Run after setup to ensure everything is working"
    )

def show_prerequisites():
    """Show prerequisites"""
    print_header("Prerequisites")
    
    print("Before running any setup script, ensure you have:")
    print()
    print("1. PostgreSQL installed and running")
    print("   - Download: https://www.postgresql.org/download/")
    print("   - Default settings are fine")
    print("   - Make sure the service is running")
    print()
    print("2. Python 3.8+ installed")
    print("   - Download: https://www.python.org/downloads/")
    print("   - Make sure Python is in your PATH")
    print()
    print("3. Node.js installed (for frontend)")
    print("   - Download: https://nodejs.org/")

def show_quick_start():
    """Show quick start guide"""
    print_header("Quick Start Guide")
    
    print("For the fastest setup experience:")
    print()
    print("1. Install PostgreSQL (if not already installed)")
    print("2. Run: python setup_database_simple.py")
    print("3. Start backend: cd backend && python main.py")
    print("4. Start frontend: cd front_end && npm install && npm start")
    print("5. Access: http://localhost:3000")
    print()
    print("Login credentials:")
    print("- Admin: admin / admin123")
    print("- User: user / user123")

def show_troubleshooting():
    """Show common troubleshooting tips"""
    print_header("Common Issues & Solutions")
    
    issues = [
        ("PostgreSQL not found", "Make sure PostgreSQL is installed and 'psql' command is available"),
        ("Connection refused", "Check if PostgreSQL service is running and port 5432 is open"),
        ("Permission denied", "Make sure database user has proper permissions"),
        ("Python packages fail to install", "Update pip: python -m pip install --upgrade pip"),
        ("Import errors", "Make sure you're running from the project root directory"),
        ("Database already exists", "This is normal - the script will handle it gracefully")
    ]
    
    for issue, solution in issues:
        print(f"• {issue}: {solution}")

def show_file_structure():
    """Show expected file structure"""
    print_header("Expected File Structure")
    
    structure = """
project_root/
├── backend/
│   ├── .env                    # Database configuration (created during setup)
│   ├── database.py            # Database connection
│   ├── models.py              # Database models
│   ├── setup_postgres.py      # Database creation
│   ├── create_demo_users.py   # Demo user creation
│   └── requirements.txt       # Python dependencies
├── front_end/                 # React frontend
├── setup_database.py          # Comprehensive setup script
├── setup_database_simple.py   # Simple setup script
├── test_database_setup.py     # Setup verification script
├── setup_help.py              # This help script
└── DATABASE_SETUP_README.md   # Detailed documentation
"""
    
    print(structure)

def main():
    """Main help function"""
    print_header("RAG Chatbot Database Setup Help")
    
    print("This script helps you choose the right database setup approach")
    print("for the RAG Chatbot project on a new device.")
    
    # Check environment
    if not check_environment():
        return False
    
    # Show all options
    show_setup_options()
    show_prerequisites()
    show_quick_start()
    show_troubleshooting()
    show_file_structure()
    
    print_header("Recommendation")
    print("For most users, we recommend starting with the Simple Setup:")
    print("python setup_database_simple.py")
    print()
    print("If you need more control or encounter issues, use the")
    print("Automated Setup: python setup_database.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nHelp cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
