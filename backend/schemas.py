from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Chat Session schemas
class ChatSessionCreate(BaseModel):
    session_name: str
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class ChatSessionUpdate(BaseModel):
    session_name: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    is_active: Optional[bool] = None

class ChatSessionResponse(BaseModel):
    id: str
    session_name: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    chunk_size: int
    chunk_overlap: int
    document_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# Chat Thread schemas
class ChatThreadCreate(BaseModel):
    title: Optional[str] = None

class ChatThreadResponse(BaseModel):
    id: str
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Document schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    session_id: str
    uploaded_at: datetime
    processed: bool
    page_count: int

    model_config = ConfigDict(from_attributes=True)

# Chat Message schemas
class ChatMessageCreate(BaseModel):
    content: str

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    message_type: str
    content: str
    timestamp: datetime
    rag_strategy: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]

# RAG Configuration schema
class RAGConfig(BaseModel):
    strategy: str = "contextual"  # naive, chunking, contextual, multi_query
    k: int = 5
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None

# Chat Request schema
class ChatRequest(BaseModel):
    message: str
    session_id: str
    thread_id: Optional[str] = None
    rag_config: Optional[RAGConfig] = None

# Streaming response schema
class StreamResponse(BaseModel):
    content: str
    is_complete: bool
    rag_strategy: Optional[str] = None

# MCP Tool schemas
class MCPToolCreate(BaseModel):
    name: str
    tool_type: str  # 'api' | 'python_function'
    api_url: Optional[str] = None
    http_method: Optional[str] = "GET"
    function_code: Optional[str] = None
    description: Optional[str] = None
    params_docstring: Optional[str] = None
    returns_docstring: Optional[str] = None

class MCPToolUpdate(BaseModel):
    name: Optional[str] = None
    tool_type: Optional[str] = None
    api_url: Optional[str] = None
    http_method: Optional[str] = None
    function_code: Optional[str] = None
    description: Optional[str] = None
    params_docstring: Optional[str] = None
    returns_docstring: Optional[str] = None

class MCPToolResponse(BaseModel):
    id: str
    session_id: str
    name: str
    tool_type: str
    api_url: Optional[str] = None
    http_method: Optional[str] = None
    function_code: Optional[str] = None
    description: Optional[str] = None
    params_docstring: Optional[str] = None
    returns_docstring: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)