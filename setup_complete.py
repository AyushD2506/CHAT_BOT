#!/usr/bin/env python3
"""
Complete setup script for RAG Chatbot with PostgreSQL
This script will guide you through the entire setup process.
"""
import asyncio
import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_step(step, text):
    """Print a formatted step"""
    print(f"\n📋 Step {step}: {text}")
    print("-" * 40)

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Command succeeded: {command}")
            return True
        else:
            print(f"❌ Command failed: {command}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Command error: {e}")
        return False

def check_postgresql():
    """Check if PostgreSQL is installed and running"""
    print("Checking PostgreSQL installation...")
    
    # Check if psql is available
    psql_available = run_command("psql --version")
    
    if not psql_available:
        print("\n❌ PostgreSQL is not installed or not in PATH")
        print("Please install PostgreSQL first:")
        print("1. Download from: https://www.postgresql.org/download/windows/")
        print("2. Or run: winget install PostgreSQL.PostgreSQL")
        print("3. Make sure to include pgAdmin during installation")
        return False
    
    # Check if PostgreSQL service is running
    print("Checking PostgreSQL service...")
    service_check = run_command("sc query postgresql-x64-15")
    
    if not service_check:
        print("⚠️ PostgreSQL service might not be running")
        print("Try starting it with: net start postgresql-x64-15")
    
    return True

def setup_environment():
    """Set up the environment file"""
    print("Setting up environment variables...")
    
    backend_dir = Path(__file__).parent / "backend"
    env_file = backend_dir / ".env"
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Get database credentials
    print("Please provide PostgreSQL connection details:")
    db_host = input("Database host (default: localhost): ").strip() or "localhost"
    db_port = input("Database port (default: 5432): ").strip() or "5432"
    db_name = input("Database name (default: rag_chatbot): ").strip() or "rag_chatbot"
    db_user = input("Database user (default: postgres): ").strip() or "postgres"
    db_password = input("Database password: ").strip()
    
    if not db_password:
        print("❌ Database password is required")
        return False
    
    # Create .env content
    env_content = f"""# PostgreSQL Database Configuration
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}

# ChatGroq API Key
GROQ_API_KEY=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

# JWT Secret Key (change in production)
SECRET_KEY=your-super-secret-jwt-key-change-in-production-{os.urandom(16).hex()}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    backend_dir = Path(__file__).parent / "backend"
    
    success = run_command("pip install -r requirements.txt", cwd=backend_dir)
    if success:
        print("✅ Python dependencies installed")
    return success

def setup_database():
    """Set up the PostgreSQL database"""
    print("Setting up PostgreSQL database...")
    backend_dir = Path(__file__).parent / "backend"
    
    # Create database
    success = run_command("python setup_postgres.py", cwd=backend_dir)
    if not success:
        return False
    
    # Test connection
    success = run_command("python test_connection.py", cwd=backend_dir)
    if not success:
        return False
    
    # Create demo users
    success = run_command("python create_demo_users.py", cwd=backend_dir)
    if success:
        print("✅ Database setup completed")
    
    return success

def install_node_dependencies():
    """Install Node.js dependencies"""
    print("Installing Node.js dependencies...")
    frontend_dir = Path(__file__).parent / "front_end"
    
    # Check if npm is available
    npm_available = run_command("npm --version")
    if not npm_available:
        print("❌ npm is not installed. Please install Node.js first:")
        print("Download from: https://nodejs.org/")
        return False
    
    success = run_command("npm install", cwd=frontend_dir)
    if success:
        print("✅ Node.js dependencies installed")
    return success

def main():
    """Main setup function"""
    print_header("RAG Chatbot - Complete Setup")
    print("This script will set up the entire RAG Chatbot system with PostgreSQL")
    
    # Step 1: Check PostgreSQL
    print_step(1, "Checking PostgreSQL Installation")
    if not check_postgresql():
        print("\n❌ Setup failed: PostgreSQL is not properly installed")
        sys.exit(1)
    
    # Step 2: Set up environment
    print_step(2, "Setting up Environment Variables")
    if not setup_environment():
        print("\n❌ Setup failed: Could not set up environment variables")
        sys.exit(1)
    
    # Step 3: Install Python dependencies
    print_step(3, "Installing Python Dependencies")
    if not install_python_dependencies():
        print("\n❌ Setup failed: Could not install Python dependencies")
        sys.exit(1)
    
    # Step 4: Set up database
    print_step(4, "Setting up PostgreSQL Database")
    if not setup_database():
        print("\n❌ Setup failed: Could not set up database")
        sys.exit(1)
    
    # Step 5: Install Node.js dependencies
    print_step(5, "Installing Node.js Dependencies")
    if not install_node_dependencies():
        print("\n⚠️  Frontend setup failed, but backend should work")
        print("You can install Node.js dependencies manually later")
    
    # Success!
    print_header("Setup Completed Successfully! 🎉")
    print("Your RAG Chatbot system is ready to use!")
    print()
    print("To start the system:")
    print("1. Backend:")
    print("   cd backend")
    print("   python main.py")
    print()
    print("2. Frontend (in another terminal):")
    print("   cd front_end")
    print("   npm start")
    print()
    print("Access points:")
    print("• Frontend: http://localhost:3000")
    print("• Backend API: http://localhost:8000/docs")
    print("• pgAdmin: Check your Start Menu")
    print()
    print("Login credentials:")
    print("• Admin: admin / admin123")
    print("• User: user / user123")
    print()
    print("For database management:")
    print("• Use pgAdmin to view/manage your PostgreSQL database")
    print("• Database name: rag_chatbot")
    print()
    print("Happy chatting! 🤖")

if __name__ == "__main__":
    main()