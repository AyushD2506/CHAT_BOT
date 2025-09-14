from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_name = Column(String(100), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Chunking configuration
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    documents = relationship("Document", back_populates="session")
    messages = relationship("ChatMessage", back_populates="session")

class ChatThread(Base):
    __tablename__ = "chat_threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("ChatMessage", back_populates="thread")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    page_count = Column(Integer, default=0)
    
    # Relationships
    session = relationship("ChatSession", back_populates="documents")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    # Thread support (nullable for backward compatibility / migration)
    thread_id = Column(String, ForeignKey("chat_threads.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    rag_strategy = Column(String(50), nullable=True)  # Which RAG strategy was used
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User", back_populates="chat_messages")
    thread = relationship("ChatThread", back_populates="messages")

class VectorStore(Base):
    __tablename__ = "vector_stores"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    store_path = Column(String(500), nullable=False)  # Path to FAISS index
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MCPTool(Base):
    __tablename__ = "mcp_tools"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    name = Column(String(100), nullable=False)
    tool_type = Column(String(50), nullable=False)  # 'api' or 'python_function'

    # API tool fields
    api_url = Column(String(1000), nullable=True)
    http_method = Column(String(10), default="GET")

    # Python function tool fields
    function_code = Column(Text, nullable=True)

    # Documentation
    description = Column(Text, nullable=True)
    params_docstring = Column(Text, nullable=True)
    returns_docstring = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)