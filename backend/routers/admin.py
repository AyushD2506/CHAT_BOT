from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from database import get_db
from models import User, ChatSession, Document, ChatMessage, MCPTool, ChatThread, VectorStore
from schemas import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate,
    DocumentResponse, UserResponse, MCPToolCreate, MCPToolResponse, MCPToolUpdate
)
from auth_utils import get_current_admin
from rag_service import rag_service
from typing import List
import os

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session_data: ChatSessionCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session (admin only)"""
    # For admin-created sessions, we can assign to any user or keep as admin's session
    db_session = ChatSession(
        session_name=session_data.session_name,
        user_id=current_admin.id,
        session_admin_id=session_data.session_admin_id or current_admin.id,
        chunk_size=session_data.chunk_size,
        chunk_overlap=session_data.chunk_overlap,
        enable_internet_search=session_data.enable_internet_search or False,
    )
    
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    
    # Add document count
    result = await db.execute(
        select(func.count(Document.id)).where(Document.session_id == db_session.id)
    )
    document_count = result.scalar()
    
    response = ChatSessionResponse.model_validate(db_session)
    response.document_count = document_count
    return response

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_all_sessions(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all chat sessions (admin only)"""
    result = await db.execute(select(ChatSession).order_by(ChatSession.created_at.desc()))
    sessions = result.scalars().all()
    
    # Add document count for each session
    response_sessions = []
    for session in sessions:
        result = await db.execute(
            select(func.count(Document.id)).where(Document.session_id == session.id)
        )
        document_count = result.scalar()
        
        session_response = ChatSessionResponse.model_validate(session)
        session_response.document_count = document_count
        response_sessions.append(session_response)
    
    return response_sessions

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get session details (admin only)"""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Add document count
    result = await db.execute(
        select(func.count(Document.id)).where(Document.session_id == session.id)
    )
    document_count = result.scalar()
    
    response = ChatSessionResponse.model_validate(session)
    response.document_count = document_count
    return response

@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: str,
    session_update: ChatSessionUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update session configuration (admin only)"""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Update fields
    if session_update.session_name is not None:
        session.session_name = session_update.session_name
    if session_update.chunk_size is not None:
        session.chunk_size = session_update.chunk_size
    if session_update.chunk_overlap is not None:
        session.chunk_overlap = session_update.chunk_overlap
    if session_update.is_active is not None:
        session.is_active = session_update.is_active
    if session_update.enable_internet_search is not None:
        session.enable_internet_search = session_update.enable_internet_search
    # Allow global admin to change session_admin_id
    if session_update.session_admin_id is not None:
        # Validate user exists
        result = await db.execute(select(User).where(User.id == session_update.session_admin_id))
        new_admin = result.scalar_one_or_none()
        if not new_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_admin_id user not found")
        session.session_admin_id = session_update.session_admin_id
    
    await db.commit()
    await db.refresh(session)
    
    # Add document count
    result = await db.execute(
        select(func.count(Document.id)).where(Document.session_id == session.id)
    )
    document_count = result.scalar()
    
    response = ChatSessionResponse.model_validate(session)
    response.document_count = document_count
    return response

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a session and all its data (admin only)"""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Delete related data in FK-safe order
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    await db.execute(delete(Document).where(Document.session_id == session_id))
    await db.execute(delete(ChatThread).where(ChatThread.session_id == session_id))
    await db.execute(delete(MCPTool).where(MCPTool.session_id == session_id))
    await db.execute(delete(VectorStore).where(VectorStore.session_id == session_id))

    # Finally delete the session
    await db.delete(session)

    # Delete RAG service data on disk/external stores
    await rag_service.delete_session_data(session_id)

    await db.commit()

    return {"message": "Session deleted successfully"}

@router.post("/sessions/{session_id}/documents", response_model=DocumentResponse)
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Upload a PDF document to a session (admin only)"""
    # Verify session exists
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process PDF with RAG service
        documents = await rag_service.process_pdf(file_content, session_id, file.filename)
        
        # Save document info to database
        db_document = Document(
            filename=file.filename,
            original_filename=file.filename,
            file_path=f"storage/uploads/{session_id}_{file.filename}",
            file_size=len(file_content),
            session_id=session_id,
            processed=True,
            page_count=len(documents)
        )
        
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)
        
        return db_document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/sessions/{session_id}/documents", response_model=List[DocumentResponse])
async def list_session_documents(
    session_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all documents in a session (admin only)"""
    result = await db.execute(
        select(Document)
        .where(Document.session_id == session_id)
        .order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()
    return documents

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document (admin only)"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Remove file if it exists
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}

@router.get("/documents/{document_id}/file")
async def get_document_file(
    document_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Stream a PDF document file for viewing (admin only)."""
    from fastapi.responses import FileResponse
    from pathlib import Path

    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Resolve file path (handle relative paths)
    file_path = document.file_path
    path_obj = Path(file_path)
    if not path_obj.is_absolute():
        # backend root directory is two levels up from this file (routers/..)
        base_dir = Path(__file__).resolve().parent.parent
        path_obj = (base_dir / file_path).resolve()

    if not path_obj.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    return FileResponse(
        path=str(path_obj),
        media_type="application/pdf",
        filename=document.original_filename or document.filename,
        headers={"Content-Disposition": f"inline; filename=\"{document.original_filename or document.filename}\""}
    )

@router.get("/analytics")
async def get_analytics(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system analytics (admin only)"""
    # Count users
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar()
    
    # Count sessions
    result = await db.execute(select(func.count(ChatSession.id)))
    session_count = result.scalar()
    
    # Count documents
    result = await db.execute(select(func.count(Document.id)))
    document_count = result.scalar()
    
    # Count messages
    result = await db.execute(select(func.count(ChatMessage.id)))
    message_count = result.scalar()
    
    return {
        "users": user_count,
        "sessions": session_count,
        "documents": document_count,
        "messages": message_count
    }

# MCP Tools (admin-only)
@router.post("/sessions/{session_id}/mcp/tools", response_model=MCPToolResponse)
async def create_mcp_tool(
    session_id: str,
    tool: MCPToolCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Validate session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if tool.tool_type not in ("api", "python_function"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tool_type")

    db_tool = MCPTool(
        session_id=session_id,
        name=tool.name,
        tool_type=tool.tool_type,
        api_url=tool.api_url,
        http_method=tool.http_method or "GET",
        function_code=tool.function_code,
        description=tool.description,
        params_docstring=tool.params_docstring,
        returns_docstring=tool.returns_docstring,
    )
    db.add(db_tool)
    await db.commit()
    await db.refresh(db_tool)
    return db_tool

@router.get("/sessions/{session_id}/mcp/tools", response_model=List[MCPToolResponse])
async def list_mcp_tools(
    session_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MCPTool).where(MCPTool.session_id == session_id))
    return result.scalars().all()

@router.put("/mcp/tools/{tool_id}", response_model=MCPToolResponse)
async def update_mcp_tool(
    tool_id: str,
    updates: MCPToolUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MCPTool).where(MCPTool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

    # Update fields if provided
    if updates.name is not None:
        tool.name = updates.name
    if updates.tool_type is not None:
        if updates.tool_type not in ("api", "python_function"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tool_type")
        tool.tool_type = updates.tool_type
    if updates.api_url is not None:
        tool.api_url = updates.api_url
    if updates.http_method is not None:
        tool.http_method = updates.http_method
    if updates.function_code is not None:
        tool.function_code = updates.function_code
    if updates.description is not None:
        tool.description = updates.description
    if updates.params_docstring is not None:
        tool.params_docstring = updates.params_docstring
    if updates.returns_docstring is not None:
        tool.returns_docstring = updates.returns_docstring

    await db.commit()
    await db.refresh(tool)
    return tool

@router.delete("/mcp/tools/{tool_id}")
async def delete_mcp_tool(
    tool_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MCPTool).where(MCPTool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    await db.delete(tool)
    await db.commit()
    return {"message": "Tool deleted"}