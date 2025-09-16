from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models import User, ChatSession, Document, MCPTool, ChatMessage, ChatThread, VectorStore
from schemas import (
    ChatSessionResponse, ChatSessionUpdate,
    DocumentResponse, MCPToolCreate, MCPToolResponse, MCPToolUpdate
)
from auth_utils import get_current_user
from rag_service import rag_service
from typing import List
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_my_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Sessions where the user is assigned session_admin or is global admin (returns all)
    if current_user.is_admin:
        result = await db.execute(select(ChatSession).order_by(ChatSession.created_at.desc()))
    else:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.session_admin_id == current_user.id)
            .order_by(ChatSession.created_at.desc())
        )
    sessions = result.scalars().all()
    # Count docs per session
    responses: List[ChatSessionResponse] = []
    for s in sessions:
        docs_res = await db.execute(select(Document).where(Document.session_id == s.id))
        doc_count = len(docs_res.scalars().all())
        resp = ChatSessionResponse.model_validate(s)
        resp.document_count = doc_count
        responses.append(resp)
    return responses

async def get_current_session_admin(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Validate session and that current_user is its session_admin or a global admin
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if not (current_user.is_admin or session.session_admin_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a session admin")

    return current_user

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session_for_admin(
    session_id: str,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add document count
    result = await db.execute(select(Document).where(Document.session_id == session.id))
    documents = result.scalars().all()

    resp = ChatSessionResponse.model_validate(session)
    resp.document_count = len(documents)
    return resp

@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session_config(
    session_id: str,
    payload: ChatSessionUpdate,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Session-admin can modify only config fields; ignore session_admin_id changes here
    if payload.session_name is not None:
        session.session_name = payload.session_name
    if payload.chunk_size is not None:
        session.chunk_size = payload.chunk_size
    if payload.chunk_overlap is not None:
        session.chunk_overlap = payload.chunk_overlap
    if payload.is_active is not None:
        session.is_active = payload.is_active
    if payload.enable_internet_search is not None:
        session.enable_internet_search = payload.enable_internet_search

    await db.commit()
    await db.refresh(session)

    # Build response with document_count
    result = await db.execute(select(Document).where(Document.session_id == session.id))
    documents = result.scalars().all()

    resp = ChatSessionResponse.model_validate(session)
    resp.document_count = len(documents)
    return resp

# Documents management (PDFs)
@router.post("/sessions/{session_id}/documents", response_model=DocumentResponse)
async def upload_pdf(
    session_id: str,
    file: UploadFile = File(...),
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate session exists
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    content = await file.read()
    try:
        docs = await rag_service.process_pdf(content, session_id, file.filename)
        db_doc = Document(
            filename=file.filename,
            original_filename=file.filename,
            file_path=f"storage/uploads/{session_id}_{file.filename}",
            file_size=len(content),
            session_id=session_id,
            processed=True,
            page_count=len(docs)
        )
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
        return db_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/sessions/{session_id}/documents", response_model=List[DocumentResponse])
async def list_pdfs(
    session_id: str,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.session_id == session_id))
    return result.scalars().all()

@router.get("/documents/{document_id}/file")
async def get_document_file(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stream a PDF document file for viewing (session admin only)."""
    # Ensure document belongs to a session the user administers
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    sess_res = await db.execute(select(ChatSession).where(ChatSession.id == document.session_id))
    sess = sess_res.scalar_one_or_none()
    if not sess or not (current_user.is_admin or sess.session_admin_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    file_path = document.file_path
    path_obj = Path(file_path)
    if not path_obj.is_absolute():
        base_dir = Path(__file__).resolve().parent.parent
        path_obj = (base_dir / file_path).resolve()

    if not path_obj.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")

    return FileResponse(
        path=str(path_obj),
        media_type="application/pdf",
        filename=document.original_filename or document.filename,
        headers={"Content-Disposition": f"inline; filename=\"{document.original_filename or document.filename}\""}
    )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Ensure document exists and belongs to a session the user administers
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    sess_res = await db.execute(select(ChatSession).where(ChatSession.id == document.session_id))
    sess = sess_res.scalar_one_or_none()
    if not sess or not (current_user.is_admin or sess.session_admin_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Remove file if exists
    try:
        if Path(document.file_path).exists():
            Path(document.file_path).unlink()
    except Exception:
        pass

    await db.delete(document)
    await db.commit()
    return {"message": "Document deleted successfully"}

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    # Validate session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete related data in FK-safe order
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    await db.execute(delete(Document).where(Document.session_id == session_id))
    await db.execute(delete(ChatThread).where(ChatThread.session_id == session_id))
    await db.execute(delete(MCPTool).where(MCPTool.session_id == session_id))
    await db.execute(delete(VectorStore).where(VectorStore.session_id == session_id))

    await db.delete(session)

    # Cleanup RAG stores
    await rag_service.delete_session_data(session_id)

    await db.commit()
    return {"message": "Session deleted successfully"}

# MCP tools management
@router.post("/sessions/{session_id}/mcp/tools", response_model=MCPToolResponse)
async def create_tool(
    session_id: str,
    tool: MCPToolCreate,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    # Validate session
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if tool.tool_type not in ("api", "python_function"):
        raise HTTPException(status_code=400, detail="Invalid tool_type")

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
async def list_tools(
    session_id: str,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MCPTool).where(MCPTool.session_id == session_id))
    return result.scalars().all()

@router.put("/sessions/{session_id}/mcp/tools/{tool_id}", response_model=MCPToolResponse)
async def update_tool(
    session_id: str,
    tool_id: str,
    updates: MCPToolUpdate,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    # Ensure tool belongs to the session
    result = await db.execute(select(MCPTool).where(MCPTool.id == tool_id, MCPTool.session_id == session_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if updates.name is not None:
        tool.name = updates.name
    if updates.tool_type is not None:
        if updates.tool_type not in ("api", "python_function"):
            raise HTTPException(status_code=400, detail="Invalid tool_type")
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

@router.delete("/sessions/{session_id}/mcp/tools/{tool_id}")
async def delete_tool(
    session_id: str,
    tool_id: str,
    _: User = Depends(get_current_session_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MCPTool).where(MCPTool.id == tool_id, MCPTool.session_id == session_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    await db.delete(tool)
    await db.commit()
    return {"message": "Tool deleted"}