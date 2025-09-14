from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from database import get_db
from models import User, ChatSession, Document, ChatMessage
from schemas import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate,
    DocumentResponse, UserResponse
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
        chunk_size=session_data.chunk_size,
        chunk_overlap=session_data.chunk_overlap
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
    
    # Delete related data
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    await db.execute(delete(Document).where(Document.session_id == session_id))
    await db.delete(session)
    
    # Delete RAG service data
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