# RAG Chatbot Setup Guide

## Overview
A contextual RAG chatbot system with FastAPI backend and React frontend, featuring:
- Admin and user authentication
- Session-based document management
- Multiple RAG strategies (naive, chunking, contextual, multi-query)
- ChatGroq integration with memory
- PDF upload and processing
- Configurable chunking parameters

## Directory Structure
```
chatb/
├── backend/
│   ├── main.py              # FastAPI main app
│   ├── database.py          # Database setup
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── auth_utils.py       # Authentication utilities
│   ├── rag_service.py      # RAG implementation
│   ├── requirements.txt    # Python dependencies
│   └── routers/
│       ├── auth.py         # Authentication routes
│       ├── admin.py        # Admin management routes
│       ├── chat.py         # Chat and messaging routes
│       └── documents.py    # Document management routes
├── front_end/
│   ├── package.json        # Node.js dependencies
│   ├── src/
│   │   ├── App.tsx         # Main React app
│   │   ├── contexts/       # React contexts
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript interfaces
│   │   ├── pages/          # React pages
│   │   └── components/     # React components
│   └── public/
└── stream_code.py          # Original Streamlit implementation (reference)
```

## Backend Setup

### 1. Set up PostgreSQL
First, install and configure PostgreSQL following the detailed guide:
```bash
# See POSTGRESQL_SETUP.md for complete PostgreSQL installation guide
```

### 2. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Update `backend/.env` with your PostgreSQL credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_chatbot
DB_USER=postgres
DB_PASSWORD=your_postgres_password
```

### 4. Set up Database
```bash
cd backend
python setup_postgres.py  # Create database
```

### 5. Create Demo Users
Create `backend/create_demo_users.py`:

```python
import asyncio
from database import init_db, AsyncSessionLocal
from models import User
from auth_utils import get_password_hash

async def create_demo_users():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(admin)
        
        # Create regular user
        user = User(
            username="user",
            email="user@example.com",
            password_hash=get_password_hash("user123"),
            is_admin=False
        )
        db.add(user)
        
        await db.commit()
        print("Demo users created!")
        print("Admin: admin / admin123")
        print("User: user / user123")

if __name__ == "__main__":
    asyncio.run(create_demo_users())
```

### 6. Run Backend
```bash
cd backend
python create_demo_users.py  # Create demo users
python main.py               # Start FastAPI server
```

Backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

## Frontend Setup

### 1. Install Dependencies
```bash
cd front_end
npm install
```

### 2. Run Frontend
```bash
npm start
```

Frontend will be available at: http://localhost:3000

## Testing the System

### 1. Authentication Testing
- Navigate to http://localhost:3000
- Test login with demo accounts:
  - Admin: `admin` / `admin123`
  - User: `user` / `user123`
- Test registration of new users

### 2. Admin Workflow
1. Login as admin
2. Create a new chat session
3. Upload PDF documents to the session
4. Configure chunk size and overlap settings
5. View analytics and manage users

### 3. User Workflow
1. Login as regular user
2. Select available chat sessions
3. Ask questions about uploaded documents
4. Test different RAG strategies
5. Review chat history with memory

## Key Features Implemented

### Backend Features
- ✅ FastAPI with async support
- ✅ JWT authentication with admin/user roles
- ✅ PostgreSQL database with async SQLAlchemy
- ✅ ChatGroq integration (llama-3.3-70b-versatile)
- ✅ Multiple RAG strategies
- ✅ PDF processing with configurable chunking
- ✅ FAISS vector storage
- ✅ Conversation memory per session
- ✅ File upload and management
- ✅ Streaming chat responses
- ✅ Session-based document isolation

### Frontend Features
- ✅ React 18 with TypeScript
- ✅ Tailwind CSS styling
- ✅ React Router for navigation
- ✅ Authentication context
- ✅ Protected routes
- ✅ Admin and user interfaces
- ✅ Responsive design
- ✅ Error handling

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user
- `GET /api/auth/users` - List users (admin only)

### Admin Management
- `POST /api/admin/sessions` - Create session
- `GET /api/admin/sessions` - List all sessions
- `PUT /api/admin/sessions/{id}` - Update session
- `DELETE /api/admin/sessions/{id}` - Delete session
- `POST /api/admin/sessions/{id}/documents` - Upload document
- `GET /api/admin/analytics` - System analytics

### Chat
- `GET /api/chat/sessions` - List user sessions
- `GET /api/chat/sessions/{id}/history` - Get chat history
- `POST /api/chat/message` - Send message
- `POST /api/chat/stream` - Stream message response

## RAG Strategies Available
1. **Naive RAG** - Simple top-k document retrieval
2. **Chunking RAG** - Document chunking with configurable parameters
3. **Contextual RAG** - Retrieval with conversation memory
4. **Multi-Query RAG** - Multiple query variations for comprehensive results

## Configuration Options
- Chunk size (default: 1000 characters)
- Chunk overlap (default: 200 characters)
- Number of retrieved documents (k=5)
- RAG strategy selection
- Session isolation

## Next Steps for Full Implementation
1. Implement complete admin dashboard functionality
2. Build full-featured chat interface with real-time messaging
3. Add document preview and management
4. Implement streaming responses in the frontend
5. Add more RAG configuration options
6. Enhance error handling and validation
7. Add unit and integration tests
8. Optimize performance and add caching
9. Add deployment configuration

## Technology Stack
- **Backend**: FastAPI, SQLAlchemy, ChatGroq, LangChain, FAISS
- **Frontend**: React, TypeScript, Tailwind CSS, Axios
- **Database**: PostgreSQL with pgAdmin
- **AI**: ChatGroq with Llama 3.3 70B model
- **Vector Store**: FAISS for document embeddings
- **Database Drivers**: psycopg2-binary, asyncpg

This system provides a solid foundation for a production-ready RAG chatbot with proper authentication, session management, and multiple RAG strategies.