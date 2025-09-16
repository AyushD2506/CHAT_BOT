# Database Setup Guide for RAG Chatbot

This guide provides multiple ways to set up the PostgreSQL database for the RAG Chatbot project on a new device.

## Prerequisites

Before running any setup script, ensure you have:

1. **PostgreSQL installed and running**
   - Download from: https://www.postgresql.org/download/
   - Default installation settings are fine
   - Make sure the PostgreSQL service is running

2. **Python 3.8+ installed**
   - Download from: https://www.python.org/downloads/
   - Make sure Python is added to your PATH

3. **Node.js installed** (for frontend)
   - Download from: https://nodejs.org/

## Setup Options

### Option 1: Automated Setup (Recommended)

Use the comprehensive setup script that handles everything automatically:

```bash
python setup_database.py
```

**Features:**
- ✅ Checks Python and PostgreSQL installation
- ✅ Installs all required Python packages
- ✅ Interactive configuration (with sensible defaults)
- ✅ Creates database and tables
- ✅ Sets up demo users
- ✅ Verifies the complete setup
- ✅ Provides clear next steps

### Option 2: Simple Setup

Use the simplified script for quick setup with default values:

```bash
python setup_database_simple.py
```

**Features:**
- ✅ Uses default configuration values
- ✅ Minimal user interaction required
- ✅ Faster setup process
- ⚠️ Uses default password "postgres" (change in production)

### Option 3: Manual Setup

Follow the step-by-step manual process:

1. **Install Python packages:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Create environment file:**
   ```bash
   # Create backend/.env file with your database configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=rag_chatbot
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   SECRET_KEY=your-super-secret-jwt-key-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Create database:**
   ```bash
   cd backend
   python setup_postgres.py
   ```

4. **Initialize tables:**
   ```bash
   python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
   ```

5. **Create demo users:**
   ```bash
   python create_demo_users.py
   ```

## Configuration Details

### Database Configuration

The setup scripts will create a `.env` file in the `backend` directory with these settings:

```env
# PostgreSQL Database Configuration
DB_HOST=localhost          # Database server host
DB_PORT=5432              # Database server port
DB_NAME=rag_chatbot       # Database name
DB_USER=postgres          # Database username
DB_PASSWORD=postgres      # Database password (change in production)

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GROQ API Configuration (optional)
GROQ_API_KEY=your_groq_api_key_here
```

### Default Demo Users

The setup creates two demo users for testing:

| Username | Password | Role  | Email              |
|----------|----------|-------|--------------------|
| admin    | admin123 | Admin | admin@example.com  |
| user     | user123  | User  | user@example.com   |

## After Setup

Once the database setup is complete:

1. **Start the backend server:**
   ```bash
   cd backend
   python main.py
   ```

2. **Start the frontend** (in a new terminal):
   ```bash
   cd front_end
   npm install
   npm start
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## Troubleshooting

### Common Issues

1. **PostgreSQL not found:**
   - Make sure PostgreSQL is installed and running
   - Check if `psql` command is available in PATH
   - On Windows, restart your terminal after installation

2. **Connection refused:**
   - Ensure PostgreSQL service is running
   - Check if port 5432 is not blocked by firewall
   - Verify database credentials in `.env` file

3. **Permission denied:**
   - Make sure the database user has proper permissions
   - Try connecting as superuser (postgres) first

4. **Python package installation fails:**
   - Update pip: `python -m pip install --upgrade pip`
   - Try installing packages individually
   - Check Python version compatibility

### Verification Commands

Test your setup with these commands:

```bash
# Test PostgreSQL connection
psql -U postgres -h localhost -c "SELECT version();"

# Test Python database connection
cd backend
python -c "from database import test_connection; print('Connection:', test_connection())"

# Check if tables exist
python -c "from database import sync_engine; from sqlalchemy import text; conn = sync_engine.connect(); result = conn.execute(text('SELECT tablename FROM pg_tables WHERE schemaname = \\'public\\'')); print('Tables:', [row[0] for row in result]); conn.close()"
```

## Production Considerations

For production deployment:

1. **Change default passwords:**
   - Update database password in `.env`
   - Change JWT secret key
   - Use strong, unique passwords

2. **Security settings:**
   - Enable SSL for database connections
   - Restrict database user permissions
   - Use environment variables for sensitive data

3. **Backup strategy:**
   - Set up automated database backups
   - Test backup restoration process

4. **Monitoring:**
   - Monitor database performance
   - Set up logging and alerts
   - Regular security updates

## File Structure

After setup, your project should have:

```
project_root/
├── backend/
│   ├── .env                    # Database configuration
│   ├── database.py            # Database connection
│   ├── models.py              # Database models
│   ├── setup_postgres.py      # Database creation
│   ├── create_demo_users.py   # Demo user creation
│   └── requirements.txt       # Python dependencies
├── setup_database.py          # Comprehensive setup script
├── setup_database_simple.py   # Simple setup script
└── DATABASE_SETUP_README.md   # This file
```

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Check the console output for specific error messages
4. Ensure you're running commands from the correct directory

The setup scripts provide detailed error messages to help diagnose issues. Most common problems are related to PostgreSQL not being installed or running, or missing Python packages.
