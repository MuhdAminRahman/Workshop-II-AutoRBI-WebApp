"""
Cloudinary Utility Functions
Upload files to Cloudinary for storage
"""

import logging
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


async def upload_pdf_to_cloudinary(file: UploadFile) -> str:
    """
    Upload PDF file to Cloudinary.
    
    Args:
        file: UploadFile object from FastAPI
    
    Returns:
        Secure URL to uploaded file
    
    Raises:
        Exception: If upload fails
    
    Example:
        url = await upload_pdf_to_cloudinary(file)
        # Returns: https://res.cloudinary.com/.../pdf.pdf
    """
    try:
        # Read file content
        content = await file.read()
        
        logger.debug(f"Uploading PDF: {file.filename} ({len(content)} bytes)")
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            content,
            resource_type="raw",  # For PDFs
            folder="autorbi/pdfs",
            public_id=f"{file.filename}_{int(__import__('time').time())}",
            overwrite=True,
        )
        
        url = result["secure_url"]
        
        logger.info(f"✅ PDF uploaded to Cloudinary: {url}")
        
        return url
    
    except Exception as e:
        logger.error(f"Failed to upload PDF to Cloudinary: {str(e)}")
        raise

async def upload_pdf_to_cloudinary_from_uploadfile(file: UploadFile, filename: str) -> str:
    """
    Stream UploadFile directly to Cloudinary without loading into memory.
    
    Args:
        file: UploadFile object (file-like stream)
        filename: Original filename
    
    Returns:
        Secure URL of uploaded PDF
    
    Raises:
        Exception: If upload fails
    """
    try:
        logger.info(f"Streaming {filename} to Cloudinary...")
        
        # Cloudinary's uploader.upload() accepts file-like objects
        # It will stream the file without loading it entirely into memory
        result = cloudinary.uploader.upload(
            file.file,  # Pass file-like object directly
            resource_type="raw",
            folder="autorbi/pdfs",
            public_id=filename.replace('.pdf', ''),
            overwrite=True,
        )
        
        pdf_url = result.get('secure_url')
        logger.info(f"✅ PDF streamed to Cloudinary: {pdf_url}")
        
        return pdf_url
    
    except Exception as e:
        logger.error(f"❌ Failed to stream PDF to Cloudinary: {str(e)}")
        raise


async def upload_pdf_to_cloudinary_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Upload PDF file to Cloudinary from bytes.
    
    This version accepts bytes directly (for background tasks where UploadFile
    is not available). Follows the same pattern as upload_excel_to_cloudinary
    and upload_ppt_to_cloudinary.
    
    Args:
        file_bytes: File content as bytes
        filename: Filename for storage
    
    Returns:
        Secure URL to uploaded file
    
    Raises:
        Exception: If upload fails
    
    Example:
        url = await upload_pdf_to_cloudinary_from_bytes(file_bytes, "document.pdf")
        # Returns: https://res.cloudinary.com/.../document.pdf_1234567890
    """
    try:
        logger.debug(f"Uploading PDF: {filename} ({len(file_bytes)} bytes)")
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_bytes,
            resource_type="raw",  # For PDFs
            folder="autorbi/pdfs",
            public_id=f"{filename}_{int(__import__('time').time())}",
            overwrite=True,
        )
        
        url = result["secure_url"]
        
        logger.info(f"✅ PDF uploaded to Cloudinary: {url}")
        
        return url
    
    except Exception as e:
        logger.error(f"Failed to upload PDF to Cloudinary: {str(e)}")
        raise


async def upload_excel_to_cloudinary(file_bytes: bytes, filename: str) -> str:
    """
    Upload Excel file to Cloudinary.
    
    Args:
        file_bytes: File content as bytes
        filename: Filename for storage
    
    Returns:
        Secure URL to uploaded file
    """
    try:
        logger.debug(f"Uploading Excel: {filename} ({len(file_bytes)} bytes)")
        
        result = cloudinary.uploader.upload(
            file_bytes,
            resource_type="raw",
            folder="autorbi/excel",
            public_id=filename,
            overwrite=True,
        )
        
        url = result["secure_url"]
        
        logger.info(f"✅ Excel uploaded: {url}")
        
        return url
    
    except Exception as e:
        logger.error(f"Failed to upload Excel: {str(e)}")
        raise


async def upload_ppt_to_cloudinary(file_bytes: bytes, filename: str) -> str:
    """
    Upload PowerPoint file to Cloudinary.
    
    Args:
        file_bytes: File content as bytes
        filename: Filename for storage
    
    Returns:
        Secure URL to uploaded file
    """
    try:
        logger.debug(f"Uploading PPT: {filename} ({len(file_bytes)} bytes)")
        
        result = cloudinary.uploader.upload(
            file_bytes,
            resource_type="raw",
            folder="autorbi/ppt",
            public_id=filename,
            overwrite=True,
        )
        
        url = result["secure_url"]
        
        logger.info(f"✅ PPT uploaded: {url}")
        
        return url
    
    except Exception as e:
        logger.error(f"Failed to upload PPT: {str(e)}")
        raise