#!/usr/bin/env python3
"""
Database Setup Script for RAG Chatbot Project
=============================================

This script sets up the PostgreSQL database for the RAG Chatbot project on a new device.
It handles database creation, table initialization, and demo user creation.

Requirements:
- PostgreSQL must be installed and running
- Python 3.8+ with pip
- All required Python packages will be installed automatically

Usage:
    python setup_database.py

The script will:
1. Check for PostgreSQL installation
2. Install required Python packages
3. Create .env file with database configuration
4. Create the database if it doesn't exist
5. Initialize all database tables
6. Create demo users for testing
7. Verify the setup is working correctly
"""

import os
import sys
import subprocess
import platform
import getpass
import asyncio
from pathlib import Path

# ANSI color codes for better output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message, color=Colors.WHITE):
    """Print colored output"""
    print(f"{color}{message}{Colors.END}")

def print_header(message):
    """Print a formatted header"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f" {message}", Colors.CYAN)
    print_colored(f"{'='*60}", Colors.CYAN)

def print_step(step, message):
    """Print a step with formatting"""
    print_colored(f"\n[STEP {step}] {message}", Colors.BLUE)

def print_success(message):
    """Print success message"""
    print_colored(f"✓ {message}", Colors.GREEN)

def print_error(message):
    """Print error message"""
    print_colored(f"✗ {message}", Colors.RED)

def print_warning(message):
    """Print warning message"""
    print_colored(f"⚠ {message}", Colors.YELLOW)

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ is required. Current version: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_postgresql():
    """Check if PostgreSQL is installed and running"""
    print_step(2, "Checking PostgreSQL installation...")
    
    # Check if psql command is available
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_success(f"PostgreSQL found: {result.stdout.strip()}")
        else:
            print_error("PostgreSQL not found in PATH")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_error("PostgreSQL not found. Please install PostgreSQL first.")
        print_warning("Visit: https://www.postgresql.org/download/")
        return False
    
    # Test connection to PostgreSQL server
    try:
        result = subprocess.run(['psql', '-U', 'postgres', '-h', 'localhost', '-c', 'SELECT 1;'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_success("PostgreSQL server is running and accessible")
            return True
        else:
            print_error("Cannot connect to PostgreSQL server")
            print_warning("Make sure PostgreSQL service is running")
            return False
    except subprocess.TimeoutExpired:
        print_error("Connection to PostgreSQL timed out")
        return False

def install_requirements():
    """Install required Python packages"""
    print_step(3, "Installing Python requirements...")
    
    requirements_file = Path("backend/requirements.txt")
    if not requirements_file.exists():
        print_error("requirements.txt not found in backend directory")
        return False
    
    try:
        print_colored("Installing packages from requirements.txt...", Colors.YELLOW)
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], check=True, capture_output=True, text=True)
        print_success("All Python packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install packages: {e}")
        print_colored(f"Error output: {e.stderr}", Colors.RED)
        return False

def create_env_file():
    """Create .env file with database configuration"""
    print_step(4, "Creating environment configuration...")
    
    env_file = Path("backend/.env")
    if env_file.exists():
        print_warning(".env file already exists. Backing up to .env.backup")
        env_file.rename("backend/.env.backup")
    
    # Get database configuration from user
    print_colored("\nDatabase Configuration:", Colors.CYAN)
    print_colored("Press Enter to use default values (shown in brackets)", Colors.YELLOW)
    
    db_host = input("Database Host [localhost]: ").strip() or "localhost"
    db_port = input("Database Port [5432]: ").strip() or "5432"
    db_name = input("Database Name [rag_chatbot]: ").strip() or "rag_chatbot"
    db_user = input("Database User [postgres]: ").strip() or "postgres"
    
    # Get password securely
    while True:
        db_password = getpass.getpass("Database Password: ")
        if db_password:
            break
        print_error("Password cannot be empty")
    
    # Get other configuration
    secret_key = input("JWT Secret Key [your-super-secret-jwt-key-change-in-production]: ").strip() or "your-super-secret-jwt-key-change-in-production"
    groq_api_key = input("GROQ API Key (optional): ").strip()
    
    # Create .env content
    env_content = f"""# PostgreSQL Database Configuration
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}

# JWT Configuration
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GROQ API Configuration
GROQ_API_KEY={groq_api_key}
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_success(f"Environment file created: {env_file}")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    print_step(5, "Creating database...")
    
    try:
        # Import here to avoid issues if packages aren't installed yet
        from backend.setup_postgres import create_database, test_connection
        
        create_database()
        if test_connection():
            print_success("Database created and connection verified")
            return True
        else:
            print_error("Database creation failed")
            return False
    except Exception as e:
        print_error(f"Database creation failed: {e}")
        return False

def initialize_tables():
    """Initialize database tables"""
    print_step(6, "Initializing database tables...")
    
    try:
        # Import here to avoid issues if packages aren't installed yet
        from backend.database import init_db
        
        async def init_tables():
            await init_db()
            print_success("Database tables created successfully")
        
        asyncio.run(init_tables())
        return True
    except Exception as e:
        print_error(f"Table initialization failed: {e}")
        return False

def create_demo_users():
    """Create demo users for testing"""
    print_step(7, "Creating demo users...")
    
    try:
        # Import here to avoid issues if packages aren't installed yet
        from backend.create_demo_users import create_demo_users
        
        asyncio.run(create_demo_users())
        return True
    except Exception as e:
        print_error(f"Demo user creation failed: {e}")
        return False

def verify_setup():
    """Verify the complete setup"""
    print_step(8, "Verifying setup...")
    
    try:
        # Test database connection
        from backend.database import test_connection
        if not test_connection():
            print_error("Database connection test failed")
            return False
        
        # Test if tables exist
        from backend.database import sync_engine
        from backend.models import User
        
        with sync_engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            
            if user_count >= 2:  # Should have at least admin and user
                print_success(f"Setup verified! Found {user_count} users in database")
                return True
            else:
                print_warning(f"Only {user_count} users found. Expected at least 2.")
                return False
                
    except Exception as e:
        print_error(f"Setup verification failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")
    
    print_colored("\n🎉 Database setup completed successfully!", Colors.GREEN)
    print_colored("\nNext steps:", Colors.CYAN)
    print_colored("1. Start the backend server:", Colors.WHITE)
    print_colored("   cd backend", Colors.YELLOW)
    print_colored("   python main.py", Colors.YELLOW)
    
    print_colored("\n2. Start the frontend (in a new terminal):", Colors.WHITE)
    print_colored("   cd front_end", Colors.YELLOW)
    print_colored("   npm install", Colors.YELLOW)
    print_colored("   npm start", Colors.YELLOW)
    
    print_colored("\n3. Access the application:", Colors.WHITE)
    print_colored("   Frontend: http://localhost:3000", Colors.GREEN)
    print_colored("   Backend API: http://localhost:8000/docs", Colors.GREEN)
    
    print_colored("\n4. Login credentials:", Colors.WHITE)
    print_colored("   Admin: admin / admin123", Colors.GREEN)
    print_colored("   User: user / user123", Colors.GREEN)
    
    print_colored("\n5. Troubleshooting:", Colors.WHITE)
    print_colored("   - Check PostgreSQL service is running", Colors.YELLOW)
    print_colored("   - Verify .env file configuration", Colors.YELLOW)
    print_colored("   - Check firewall settings for port 5432", Colors.YELLOW)

def main():
    """Main setup function"""
    print_header("RAG Chatbot Database Setup")
    print_colored("This script will set up the PostgreSQL database for the RAG Chatbot project.", Colors.WHITE)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print_error("Please run this script from the project root directory")
        print_colored("The script should be in the same directory as the 'backend' folder", Colors.YELLOW)
        return False
    
    # Run setup steps
    steps = [
        check_python_version,
        check_postgresql,
        install_requirements,
        create_env_file,
        create_database,
        initialize_tables,
        create_demo_users,
        verify_setup
    ]
    
    for step_func in steps:
        if not step_func():
            print_error("Setup failed. Please fix the issue and run the script again.")
            return False
    
    print_next_steps()
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_colored("\n\nSetup cancelled by user.", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
