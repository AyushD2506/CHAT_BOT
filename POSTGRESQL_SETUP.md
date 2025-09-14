# PostgreSQL Setup Guide for RAG Chatbot

This guide will help you set up PostgreSQL with pgAdmin on Windows and configure the RAG Chatbot system to use PostgreSQL instead of SQLite.

## 1. Install PostgreSQL and pgAdmin

### Option 1: Download from Official Website
1. Go to https://www.postgresql.org/download/windows/
2. Download the PostgreSQL installer (includes pgAdmin)
3. Run the installer with these settings:
   - **Port**: 5432 (default)
   - **Superuser password**: Choose a secure password (e.g., `postgres`)
   - **Locale**: Default
   - Make sure pgAdmin 4 is selected for installation

### Option 2: Using Chocolatey (if you have it)
```powershell
choco install postgresql
choco install pgadmin4
```

### Option 3: Using Winget
```powershell
winget install PostgreSQL.PostgreSQL
winget install pgAdmin.pgAdmin
```

## 2. Verify PostgreSQL Installation

1. **Check if PostgreSQL service is running**:
   - Open Services (Win + R, type `services.msc`)
   - Look for "postgresql-x64-15" (or similar)
   - Status should be "Running"

2. **Test command line access**:
   ```powershell
   psql --version
   ```

3. **Connect to PostgreSQL**:
   ```powershell
   psql -U postgres -h localhost
   ```
   Enter the password you set during installation.

## 3. Set up pgAdmin 4

1. **Launch pgAdmin 4**:
   - Start Menu → pgAdmin 4
   - Opens in your web browser (usually http://127.0.0.1:59xxx)

2. **Set master password** (first time only):
   - Create a master password for pgAdmin

3. **Connect to PostgreSQL server**:
   - Right-click "Servers" → Create → Server
   - **Name**: Local PostgreSQL
   - **Connection tab**:
     - Host: localhost
     - Port: 5432
     - Username: postgres
     - Password: [your postgres password]

## 4. Configure the RAG Chatbot for PostgreSQL

### Update Environment Variables
Edit `backend/.env` file with your PostgreSQL credentials:

```env
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_chatbot
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here

# ChatGroq API Key
GROQ_API_KEY=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

# JWT Secret Key (change in production)
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Install Python Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

The updated requirements include:
- `psycopg2-binary` - PostgreSQL adapter for Python
- `asyncpg` - Async PostgreSQL adapter
- `python-dotenv` - Environment variable loader

## 5. Set up the Database

### Method 1: Using the Setup Script (Recommended)
```powershell
cd backend
python setup_postgres.py
```

This script will:
- Create the `rag_chatbot` database
- Test the connection
- Provide next steps

### Method 2: Manual Setup via pgAdmin
1. Open pgAdmin 4
2. Connect to your PostgreSQL server
3. Right-click "Databases" → Create → Database
4. **Name**: `rag_chatbot`
5. **Owner**: postgres
6. Click "Save"

### Method 3: Command Line
```powershell
psql -U postgres -h localhost
CREATE DATABASE rag_chatbot;
\q
```

## 6. Initialize the Application

1. **Create database tables**:
   ```powershell
   cd backend
   python main.py
   ```
   This will create all the tables automatically via SQLAlchemy.

2. **Create demo users**:
   ```powershell
   python create_demo_users.py
   ```

3. **Start the backend**:
   ```powershell
   python main.py
   ```

## 7. Verify Setup in pgAdmin

1. Open pgAdmin 4
2. Navigate to: Servers → Local PostgreSQL → Databases → rag_chatbot → Schemas → public → Tables
3. You should see these tables:
   - `users`
   - `chat_sessions`
   - `documents`
   - `chat_messages`
   - `vector_stores`

## 8. Frontend Setup (No changes needed)

The frontend configuration remains the same:
```powershell
cd front_end
npm install
npm start
```

## 9. Testing the System

1. **Backend API**: http://localhost:8000/docs
2. **Frontend**: http://localhost:3000
3. **Login credentials**:
   - Admin: `admin` / `admin123`
   - User: `user` / `user123`

## Troubleshooting

### PostgreSQL Service Issues
```powershell
# Check if PostgreSQL is running
Get-Service postgresql*

# Start PostgreSQL service if stopped
Start-Service postgresql-x64-15  # Adjust version number
```

### Connection Issues
1. **Check firewall**: Make sure port 5432 is not blocked
2. **Check pg_hba.conf**: Located in PostgreSQL data directory
3. **Check postgresql.conf**: Ensure `listen_addresses = 'localhost'`

### Python Connection Issues
```python
# Test connection manually
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="rag_chatbot",
    user="postgres",
    password="your_password"
)
print("Connection successful!")
conn.close()
```

## Database Management via pgAdmin

### View Data
1. Navigate to Tables → [table_name] → Right-click → View/Edit Data → All Rows

### Run Queries
1. Right-click on `rag_chatbot` database → Query Tool
2. Write SQL queries:
```sql
SELECT * FROM users;
SELECT * FROM chat_sessions;
SELECT * FROM documents;
```

### Backup Database
1. Right-click `rag_chatbot` → Backup...
2. Choose format (Custom recommended)
3. Select file location and click "Backup"

### Monitor Performance
1. Dashboard → Server Activity
2. Statistics → Database statistics

## Key Changes from SQLite to PostgreSQL

1. **Database URLs**: Now using PostgreSQL connection strings
2. **Dependencies**: Added `psycopg2-binary` and `asyncpg`
3. **Environment Variables**: Database configuration via `.env`
4. **Concurrent Users**: PostgreSQL supports multiple simultaneous connections
5. **Data Types**: Better support for JSON, arrays, and custom types
6. **Performance**: Better performance for larger datasets and complex queries
7. **ACID Compliance**: Full ACID transactions support
8. **Scalability**: Can handle much larger databases and more users

## Production Considerations

1. **Security**: Change default passwords and restrict access
2. **Connection Pooling**: Consider using connection pooling for better performance
3. **Backup Strategy**: Set up automated backups
4. **Monitoring**: Use pgAdmin or other tools for monitoring
5. **SSL**: Enable SSL for secure connections
6. **Resource Limits**: Configure memory and connection limits appropriately

The system is now ready to use PostgreSQL with full production capabilities!