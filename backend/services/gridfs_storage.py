"""
GridFS Storage Service for File Uploads
MongoDB GridFS for storing KYC documents and other files
"""
import logging
import secrets
from typing import Optional, BinaryIO
from datetime import datetime, timezone
from io import BytesIO

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from gridfs import GridOut
from bson import ObjectId

logger = logging.getLogger(__name__)


class GridFSStorageService:
    """GridFS storage service for file uploads"""
    
    def __init__(self, db):
        """Initialize GridFS bucket"""
        self.fs = AsyncIOMotorGridFSBucket(db)
        logger.info("✅ GridFS storage service initialized")
    
    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Upload file to GridFS and return file ID"""
        
        try:
            # Generate unique filename
            file_id = secrets.token_hex(16)
            safe_filename = f"{file_id}_{filename}"
            
            # Prepare metadata
            file_metadata = metadata or {}
            file_metadata.update({
                'original_filename': filename,
                'content_type': content_type,
                'uploaded_at': datetime.now(timezone.utc),
                'size': len(file_data)
            })
            
            # Upload to GridFS
            grid_in = self.fs.open_upload_stream(
                safe_filename,
                metadata=file_metadata
            )
            
            await grid_in.write(file_data)
            await grid_in.close()
            
            file_id_str = str(grid_in._id)
            
            logger.info(f"✅ File uploaded: {filename} (ID: {file_id_str}, Size: {len(file_data)} bytes)")
            
            return file_id_str
            
        except Exception as e:
            logger.error(f"❌ Failed to upload file {filename}: {str(e)}")
            raise
    
    async def download_file(self, file_id: str) -> tuple[bytes, dict]:
        """Download file from GridFS"""
        
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(file_id)
            
            # Open download stream
            grid_out = await self.fs.open_download_stream(object_id)
            
            # Read file data
            file_data = await grid_out.read()
            
            # Get metadata
            metadata = {
                'filename': grid_out.filename,
                'content_type': grid_out.metadata.get('content_type', 'application/octet-stream'),
                'size': grid_out.metadata.get('size', len(file_data)),
                'uploaded_at': grid_out.metadata.get('uploaded_at')
            }
            
            logger.info(f"✅ File downloaded: {metadata['filename']} (Size: {metadata['size']} bytes)")
            
            return file_data, metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to download file {file_id}: {str(e)}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from GridFS"""
        
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(file_id)
            
            # Delete file
            await self.fs.delete(object_id)
            
            logger.info(f"✅ File deleted: {file_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete file {file_id}: {str(e)}")
            return False
    
    async def get_file_url(self, file_id: str) -> str:
        """Generate download URL for file"""
        # This would typically be an API endpoint
        return f"/api/files/{file_id}"


async def get_gridfs_service(db):
    """Get GridFS service instance"""
    return GridFSStorageService(db)
