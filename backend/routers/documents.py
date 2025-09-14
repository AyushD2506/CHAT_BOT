from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, Document
from schemas import DocumentResponse
from auth_utils import get_current_user
from typing import List

router = APIRouter()

@router.get("/", response_model=List[DocumentResponse])
async def list_user_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents accessible to the user"""
    if current_user.is_admin:
        # Admin can see all documents
        result = await db.execute(
            select(Document).order_by(Document.uploaded_at.desc())
        )
    else:
        # Regular users see only documents from their sessions
        result = await db.execute(
            select(Document)
            .join(Document.session)
            .where(Document.session.has(user_id=current_user.id))
            .order_by(Document.uploaded_at.desc())
        )
    
    documents = result.scalars().all()
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document details"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check access - user must own the session or be admin
    if not current_user.is_admin:
        session_result = await db.execute(
            select(Document.session).where(Document.id == document_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document"
            )
    
    return document