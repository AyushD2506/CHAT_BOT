from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, ChatSession, ChatMessage, Document, ChatThread
from schemas import (
    ChatRequest, ChatMessageResponse, ChatHistoryResponse,
    ChatSessionResponse, StreamResponse, DocumentResponse,
    ChatThreadCreate, ChatThreadResponse
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
    - Admins: chat use is disabled (return empty list)
    - Regular users: see all active sessions (admin-created included)
    """
    if current_user.is_admin:
        return []
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
    
    # Admins cannot use chat endpoints
    if current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot use chat")
    # Regular users: allow if owner or session is active
    if session.user_id != current_user.id and not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )
    
    # Get messages (isolate per-user)
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id
        )
        .order_by(ChatMessage.timestamp)
        .limit(50)  # Last 50 messages
    )
    messages = result.scalars().all()

    return ChatHistoryResponse(messages=messages)

# =========================
# Threaded chat endpoints
# =========================

@router.get("/sessions/{session_id}/threads", response_model=List[ChatThreadResponse])
async def list_threads(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate session access
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not current_user.is_admin and session.user_id != current_user.id and not session.is_active:
        raise HTTPException(status_code=403, detail="Access denied to this session")

    result = await db.execute(
        select(ChatThread)
        .join(ChatMessage, ChatMessage.thread_id == ChatThread.id)
        .where(ChatThread.session_id == session_id, ChatMessage.user_id == current_user.id)
        .order_by(ChatThread.updated_at.desc())
    )
    threads = result.scalars().unique().all()
    return [ChatThreadResponse.model_validate(t) for t in threads]

@router.post("/sessions/{session_id}/threads", response_model=ChatThreadResponse)
async def create_thread(
    session_id: str,
    payload: ChatThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate session access
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not current_user.is_admin and session.user_id != current_user.id and not session.is_active:
        raise HTTPException(status_code=403, detail="Access denied to this session")

    thread = ChatThread(session_id=session_id, title=payload.title)
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return ChatThreadResponse.model_validate(thread)

@router.get("/sessions/{session_id}/threads/{thread_id}/history", response_model=ChatHistoryResponse)
async def get_thread_history(
    session_id: str,
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate session and thread
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not current_user.is_admin and session.user_id != current_user.id and not session.is_active:
        raise HTTPException(status_code=403, detail="Access denied to this session")

    result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id, ChatThread.session_id == session_id))
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.thread_id == thread_id,
            ChatMessage.user_id == current_user.id
        )
        .order_by(ChatMessage.timestamp)
        .limit(200)
    )
    messages = result.scalars().all()
    return ChatHistoryResponse(messages=messages)

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get RAG/internet response with prioritization"""
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
        # Ensure a thread exists if provided or create one on demand
        thread_id = chat_request.thread_id
        if not thread_id:
            # Create a new thread with a provisional title (first message)
            new_thread = ChatThread(session_id=chat_request.session_id, title=None)
            db.add(new_thread)
            await db.commit()
            await db.refresh(new_thread)
            thread_id = new_thread.id

        # Save user message
        user_message = ChatMessage(
            session_id=chat_request.session_id,
            thread_id=thread_id,
            user_id=current_user.id,
            message_type="user",
            content=chat_request.message
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)

        # If thread title is empty, set it to first user message (trimmed)
        result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
        thread = result.scalar_one_or_none()
        if thread and (thread.title is None or thread.title.strip() == ""):
            thread.title = (chat_request.message[:80]).strip()
            await db.commit()

        # Get RAG configuration
        rag_config = chat_request.rag_config or {}
        strategy = rag_config.strategy or "contextual"
        k = rag_config.k or 5

        # Use session's chunking config if not provided
        chunk_size = rag_config.chunk_size or session.chunk_size
        chunk_overlap = rag_config.chunk_overlap or session.chunk_overlap

        # Prioritization flag from client per message
        prefer_internet_first = bool(getattr(chat_request, 'prefer_internet_first', False))

        # Branching based on prioritization and session internet setting
        response_content: str
        if prefer_internet_first and session.enable_internet_search:
            # Try internet first; force internet search (bypass heuristic) then fall back to RAG
            try:
                internet_results = await rag_service._get_internet_search_results(
                    chat_request.message, chat_request.session_id, db, force=True
                )
            except Exception:
                internet_results = None

            if internet_results:
                try:
                    combined_prompt = f"""
Based on the following internet search results, answer the user's question. If useful, you may also leverage document context.

User Question: {chat_request.message}

Internet Search Results:
{internet_results}
"""
                    from ..rag_service import rag_service as _svc
                    llm, identity, _ = await _svc._get_llm(chat_request.session_id, db)
                    resp = llm.invoke(combined_prompt)
                    response_content = getattr(resp, 'content', str(resp)) or ''
                    response_content = f"[assistant={identity}]\n{response_content}"
                except Exception:
                    response_content = internet_results  # already formatted text
            else:
                # Fall back to standard RAG
                response_content = await rag_service._get_rag_response(
                    chat_request.message, chat_request.session_id, current_user.id, db, strategy,
                    k=k, chunk_size=chunk_size, chunk_overlap=chunk_overlap
                )
        else:
            # Default pipeline: tools -> internet (if enabled) -> RAG, already handled in chat_with_memory
            response_content = await rag_service.chat_with_memory(
                query=chat_request.message,
                session_id=chat_request.session_id,
                user_id=current_user.id,
                db=db,
                strategy=strategy,
                k=k,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

        # Save assistant message
        assistant_message = ChatMessage(
            session_id=chat_request.session_id,
            thread_id=thread_id,
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
                user_id=current_user.id,
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