from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, ChatSession, ChatMessage, Document
from schemas import (
    ChatRequest, ChatMessageResponse, ChatHistoryResponse,
    ChatSessionResponse, StreamResponse, DocumentResponse
)
from auth_utils import get_current_user
from rag_service import rag_service
from typing import List, AsyncGenerator
import json
import asyncio

router = APIRouter()

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List available chat sessions
    - Admins: see all sessions
    - Regular users: see all active sessions (admin-created included)
    """
    if current_user.is_admin:
        result = await db.execute(
            select(ChatSession).order_by(ChatSession.created_at.desc())
        )
    else:
        # Show all active sessions to regular users
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.is_active == True)
            .order_by(ChatSession.created_at.desc())
        )

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

@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a session"""
    # Verify user has access to this session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check access: allow if admin OR owner OR session is active
    if not current_user.is_admin and session.user_id != current_user.id and not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )
    
    # Get messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
        .limit(50)  # Last 50 messages
    )
    messages = result.scalars().all()
    
    return ChatHistoryResponse(messages=messages)

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get RAG response"""
    # Verify user has access to this session
    result = await db.execute(select(ChatSession).where(ChatSession.id == chat_request.session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check access: allow if admin OR owner OR session is active
    if not current_user.is_admin and session.user_id != current_user.id and not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )
    
    try:
        # Save user message
        user_message = ChatMessage(
            session_id=chat_request.session_id,
            user_id=current_user.id,
            message_type="user",
            content=chat_request.message
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)
        
        # Get RAG configuration
        rag_config = chat_request.rag_config or {}
        strategy = rag_config.strategy or "contextual"
        k = rag_config.k or 5
        
        # Use session's chunking config if not provided
        chunk_size = rag_config.chunk_size or session.chunk_size
        chunk_overlap = rag_config.chunk_overlap or session.chunk_overlap
        
        # Get response from RAG service
        response_content = await rag_service.chat_with_memory(
            query=chat_request.message,
            session_id=chat_request.session_id,
            db=db,
            strategy=strategy,
            k=k,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=chat_request.session_id,
            user_id=current_user.id,
            message_type="assistant",
            content=response_content,
            rag_strategy=strategy
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)
        
        return assistant_message
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

@router.post("/stream")
async def stream_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get streaming RAG response"""
    # Verify user has access to this session
    result = await db.execute(select(ChatSession).where(ChatSession.id == chat_request.session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check access: allow if admin OR owner OR session is active
    if not current_user.is_admin and session.user_id != current_user.id and not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )
    
    async def generate_stream():
        try:
            # Save user message
            user_message = ChatMessage(
                session_id=chat_request.session_id,
                user_id=current_user.id,
                message_type="user",
                content=chat_request.message
            )
            db.add(user_message)
            await db.commit()
            await db.refresh(user_message)
            
            # Get RAG configuration
            rag_config = chat_request.rag_config or {}
            strategy = rag_config.strategy or "contextual"
            k = rag_config.k or 5
            
            # Use session's chunking config if not provided
            chunk_size = rag_config.chunk_size or session.chunk_size
            chunk_overlap = rag_config.chunk_overlap or session.chunk_overlap
            
            # Get response from RAG service
            response_content = await rag_service.chat_with_memory(
                query=chat_request.message,
                session_id=chat_request.session_id,
                db=db,
                strategy=strategy,
                k=k,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # Simulate streaming by chunking the response
            words = response_content.split()
            current_chunk = ""
            
            for i, word in enumerate(words):
                current_chunk += word + " "
                
                if i % 3 == 0 or i == len(words) - 1:  # Send every 3 words or at end
                    stream_data = StreamResponse(
                        content=current_chunk.strip(),
                        is_complete=(i == len(words) - 1),
                        rag_strategy=strategy
                    )
                    yield f"data: {stream_data.json()}\\n\\n"
                    current_chunk = ""
                    await asyncio.sleep(0.1)  # Small delay for streaming effect
            
            # Save assistant message
            assistant_message = ChatMessage(
                session_id=chat_request.session_id,
                user_id=current_user.id,
                message_type="assistant",
                content=response_content,
                rag_strategy=strategy
            )
            db.add(assistant_message)
            await db.commit()
            
        except Exception as e:
            error_data = StreamResponse(
                content=f"Error: {str(e)}",
                is_complete=True,
                rag_strategy=None
            )
            yield f"data: {error_data.json()}\\n\\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.get("/sessions/{session_id}/documents", response_model=List[DocumentResponse])
async def list_session_documents(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List documents in a session (user access)"""
    # Verify user has access to this session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check access: allow if admin OR owner OR session is active
    if not current_user.is_admin and session.user_id != current_user.id and not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )
    
    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.session_id == session_id)
        .order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()
    return documents

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat message"""
    result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if user owns the message or is admin
    if message.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await db.delete(message)
    await db.commit()
    
    return {"message": "Message deleted successfully"}