"""
File Upload Router - KYC Document Management
Handles file uploads for KYC verification using GridFS
"""
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status, Request
from fastapi.responses import StreamingResponse

from auth import get_current_user
from database import get_database
from dependencies import get_db
from services.gridfs_storage import GridFSStorageService
from services.telegram_bot import telegram_bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


# Allowed file types and sizes
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file(file: UploadFile) -> None:
    """Validate file type and size"""
    
    # Check file extension
    filename_lower = file.filename.lower() if file.filename else ''
    if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Note: File size validation happens during read


@router.post("/upload/kyc", summary="Upload KYC Document")
async def upload_kyc_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form(...),  # id_front, id_back, selfie, proof_of_address
    current_user: dict = Depends(get_current_user)
):
    """
    Upload KYC document for verification.
    
    Allowed document types:
    - id_front: Front of government ID
    - id_back: Back of government ID
    - selfie: Selfie holding ID
    - proof_of_address: Utility bill or bank statement
    """
    db = get_db()
    
    # Validate document type
    valid_types = ['id_front', 'id_back', 'selfie', 'proof_of_address']
    if document_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Validate file
    validate_file(file)
    
    try:
        # Read file data with size limit
        file_data = await file.read()
        
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Get GridFS service
        gridfs_service = GridFSStorageService(db)
        
        # Upload to GridFS
        file_id = await gridfs_service.upload_file(
            file_data=file_data,
            filename=file.filename or 'document',
            content_type=file.content_type or 'application/octet-stream',
            metadata={
                'user_id': current_user['id'],
                'document_type': document_type,
                'uploaded_via': 'kyc_submission'
            }
        )
        
        # Add to user's KYC documents
        doc_entry = {
            'type': document_type,
            'file_id': file_id,
            'filename': file.filename,
            'uploaded_at': file_data.__class__.__name__  # Placeholder, will be set in DB
        }
        
        await db.users.update_one(
            {"id": current_user['id']},
            {"$push": {"kyc_docs": doc_entry}}
        )
        
        logger.info(f"✅ KYC document uploaded: {document_type} for user {current_user['id']}")
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "file_id": file_id,
            "document_type": document_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload KYC document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document. Please try again."
        )


@router.get("/download/{file_id}", summary="Download File")
async def download_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download a file by ID (user can only download their own files)"""
    db = get_db()
    
    try:
        # Get GridFS service
        gridfs_service = GridFSStorageService(db)
        
        # Download file
        file_data, metadata = await gridfs_service.download_file(file_id)
        
        # Check if user owns this file
        if metadata.get('user_id') != current_user['id']:
            # Check if user is admin
            admin = await db.admins.find_one({"id": current_user['id']})
            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Return file as streaming response
        return StreamingResponse(
            iter([file_data]),
            media_type=metadata['content_type'],
            headers={
                'Content-Disposition': f'attachment; filename="{metadata["filename"]}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to download file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )


@router.delete("/delete/{file_id}", summary="Delete File")
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a file by ID (user can only delete their own files)"""
    db = get_db()
    
    try:
        # Verify ownership
        user = await db.users.find_one({"id": current_user['id']})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if file belongs to user
        kyc_docs = user.get('kyc_docs', [])
        file_belongs_to_user = any(doc.get('file_id') == file_id for doc in kyc_docs)
        
        if not file_belongs_to_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete from GridFS
        gridfs_service = GridFSStorageService(db)
        await gridfs_service.delete_file(file_id)
        
        # Remove from user's KYC documents
        await db.users.update_one(
            {"id": current_user['id']},
            {"$pull": {"kyc_docs": {"file_id": file_id}}}
        )
        
        logger.info(f"✅ File deleted: {file_id} by user {current_user['id']}")
        
        return {
            "success": True,
            "message": "File deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.get("/user/documents", summary="Get User's KYC Documents")
async def get_user_documents(
    current_user: dict = Depends(get_current_user)
):
    """Get list of current user's uploaded KYC documents"""
    db = get_db()
    
    user = await db.users.find_one({"id": current_user['id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    kyc_docs = user.get('kyc_docs', [])
    
    return {
        "documents": kyc_docs,
        "kyc_status": user.get('kyc_status', 'pending'),
        "kyc_tier": user.get('kyc_tier', 0)
    }
