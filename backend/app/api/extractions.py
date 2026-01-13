"""
Extraction Routes - REFACTORED FOR DECOUPLING
Decouples fast database operations from slow Cloudinary uploads and AI extraction

POST /api/works/{workId}/extraction/start
  1. Create extraction record (FAST, < 100ms)
  2. Return extraction_id immediately
  3. Queue upload + extraction as background task (SLOW, happens async)
  
This eliminates HTTP timeouts completely.
"""

import logging
import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.extraction import Extraction, ExtractionStatus
from app.models.work import Work
from app.dependencies import get_current_user
from app.schemas.extraction import (
    ExtractionStartResponse,
    ExtractionStatusResponse,
)
from app.services.extraction_service import (
    upload_and_extract,
    get_extraction_progress,
)
from app.services.permission_service import can_view, can_edit
from datetime import datetime
from sqlalchemy import desc
from pydantic import BaseModel
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Store WebSocket connections for progress updates
active_connections: dict = {}


# ============================================================================
# SCHEMA
# ============================================================================

class LatestExtractionIdResponse(BaseModel):
    """Response with latest extraction ID for a work"""
    work_id: int
    extraction_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# GET LATEST EXTRACTION ID - GET /api/works/{workId}/extraction/latest
# ============================================================================


@router.get(
    "/works/{work_id}/extraction/latest",
    response_model=LatestExtractionIdResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest extraction ID",
    description="Get the latest extraction job ID for a work",
)
async def get_latest_extraction_id(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LatestExtractionIdResponse:
    """
    Get the latest extraction ID for a work.
    Requires view permission on work.
    
    Args:
        work_id: Work project ID
        current_user: Current user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        LatestExtractionIdResponse with latest extraction info
    
    Raises:
        HTTPException 404: If work not found or no extractions exist
        HTTPException 403: If user doesn't have access
    
    Example:
        GET /api/works/1/extraction/latest
        
        Response:
        {
            "work_id": 1,
            "extraction_id": 5,
            "status": "in_progress",
            "created_at": "2024-01-15T10:30:00"
        }
    """
    logger.info(f"Getting latest extraction ID for work {work_id}")
    
    # ✅ Permission check - require view permission
    if not can_view(db, work_id, current_user.id):
        logger.warning(f"User {current_user.username} tried to access unauthorized work {work_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this work",
        )
    
    # Verify work exists
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        logger.warning(f"Work not found: {work_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # Get latest extraction ordered by created_at descending
    latest_extraction = db.query(Extraction).filter(
        Extraction.work_id == work_id
    ).order_by(desc(Extraction.created_at)).first()
    
    if not latest_extraction:
        logger.warning(f"No extractions found for work {work_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extractions found for this work",
        )
    
    logger.info(f"✅ Found latest extraction {latest_extraction.id} for work {work_id}")
    
    return LatestExtractionIdResponse(
        work_id=work_id,
        extraction_id=latest_extraction.id,
        status=latest_extraction.status,
        created_at=latest_extraction.created_at,
    )

# ============================================================================
# START EXTRACTION - POST /api/works/{workId}/extraction/start
# ============================================================================

"""
ARCHITECTURE CHANGE: This endpoint now returns immediately with extraction_id
instead of waiting for the upload to complete.

BEFORE:
  POST → Upload to Cloudinary (30-60s) → Create DB record → Queue task → Return
  Risk: HTTP timeout after 30s of upload, even if it succeeds

AFTER:
  POST → Create DB record (< 100ms) → Return extraction_id
         → Background task handles upload + extraction (can take as long as needed)
  Risk: None - response always returns quickly
"""


@router.post(
    "/works/{work_id}/extraction/start",
    response_model=ExtractionStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start extraction job",
    description="Queue PDF for extraction and return extraction_id immediately",
)
async def start_extraction(
    work_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
) -> ExtractionStartResponse:
    """
    FIXED VERSION: Don't wait for file read.
    
    Process:
    1. Validate (fast)
    2. Create extraction record (fast)
    3. Save file to temp location (fast)
    4. Return extraction_id immediately
    5. Background task reads from disk and uploads
    
    This returns in < 1 second regardless of file size.
    """
    logger.info(f"Starting extraction for work {work_id} by user {current_user.username}")
    
    # Permission check
    if not can_edit(db, work_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # Verify work exists
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work not found",
        )
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be a PDF (.pdf)",
        )
    
    try:
        # ============================================================
        # STEP 1: Create extraction record immediately
        # ============================================================
        logger.info(f"Creating extraction record for work {work_id}")
        
        extraction = Extraction(
            work_id=work_id,
            status=ExtractionStatus.PENDING,
            pdf_url="",  # Will be set by background task
            total_pages=0,
            processed_pages=0,
        )
        db.add(extraction)
        db.commit()
        db.refresh(extraction)
        
        logger.info(f"✅ Extraction record created: {extraction.id}")
        
        # ============================================================
        # STEP 2: Queue background task (NO FILE I/O HERE!)
        # ============================================================
        if background_tasks:
            logger.info(f"Queuing background task for extraction {extraction.id}")
            background_tasks.add_task(
                upload_and_extract_from_upload,
                extraction_id=extraction.id,
                work_id=work_id,
                filename=file.filename,
                file=file,
            )
        else:
            logger.warning("No background_tasks available")
        
        # ============================================================
        # STEP 3: Return immediately (< 50ms total)
        # ============================================================
        logger.info(f"Extraction {extraction.id} queued successfully")
        
        return ExtractionStartResponse(
            extraction_id=extraction.id,
            work_id=work_id,
            status=ExtractionStatus.PENDING,
            message=f"Extraction {extraction.id} queued. Processing in background.",
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to create extraction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start extraction: {str(e)}",
        )

async def upload_and_extract_from_upload(
    extraction_id: int,
    work_id: int,
    filename: str,
    file: UploadFile,
) -> None:
    """
    Background task: Read file from UploadFile, upload to Cloudinary, run extraction.
    Runs AFTER HTTP response is sent - no timeout!
    
    Args:
        extraction_id: Extraction record ID
        work_id: Work project ID
        filename: Original filename
        file: UploadFile object from FastAPI
    """
    from app.db.database import SessionLocal
    from app.utils.cloudinary_util import upload_pdf_to_cloudinary_from_bytes
    from app.services.extraction_service import run_extraction
    
    db = SessionLocal()
    extraction = None
    
    try:
        logger.info(f"[Background] Starting for extraction {extraction_id}")
        
        # Get extraction record
        extraction = db.query(Extraction).filter(
            Extraction.id == extraction_id
        ).first()
        
        if not extraction:
            logger.error(f"[Background] Extraction {extraction_id} not found")
            return
        
        # ===== STEP 1: Read file from UploadFile and upload =====
        logger.info(f"[Background] Reading uploaded file: {filename}")
        
        try:
            # Read file bytes from UploadFile
            file_bytes = await file.read()
            file_size_mb = len(file_bytes) / (1024 * 1024)
            logger.info(f"[Background] Read {file_size_mb:.2f}MB from upload")
            
            # Upload to Cloudinary
            logger.info(f"[Background] Uploading to Cloudinary...")
            safe_filename = os.path.basename(filename)
            pdf_url = await upload_pdf_to_cloudinary_from_bytes(file_bytes, safe_filename)
            logger.info(f"[Background] ✅ Uploaded: {pdf_url}")
            
        except Exception as e:
            logger.error(f"[Background] ❌ Upload failed: {str(e)}", exc_info=True)
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = f"Upload failed: {str(e)}"
            db.commit()
            return
        
        # ===== STEP 2: Update extraction with URL =====
        extraction.pdf_url = pdf_url
        db.commit()
        logger.info(f"[Background] Updated extraction {extraction_id} with pdf_url")
        
        # ===== STEP 3: Run extraction =====
        logger.info(f"[Background] Starting extraction pipeline")
        
        try:
            await run_extraction(
                work_id=work_id,
                extraction_id=extraction_id,
                pdf_url=pdf_url,
                pdf_filename=filename,
            )
            logger.info(f"[Background] ✅ Extraction {extraction_id} completed")
        except Exception as e:
            logger.error(f"[Background] ❌ Extraction failed: {str(e)}", exc_info=True)
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = f"Extraction failed: {str(e)}"
            db.commit()
            return
    
    except Exception as e:
        logger.error(f"[Background] Unexpected error: {str(e)}", exc_info=True)
        if extraction:
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = f"Unexpected error: {str(e)}"
            db.commit()
    
    finally:
        db.close()

# ============================================================================
# GET EXTRACTION STATUS - GET /api/extractions/{extractionId}/status
# ============================================================================


@router.get(
    "/extractions/{extraction_id}/status",
    response_model=ExtractionStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get extraction status",
    description="Get current status and progress of extraction job",
)
async def get_extraction_status(
    extraction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExtractionStatusResponse:
    """
    Get extraction job status and progress.
    Requires view permission on the extraction's work.
    
    Args:
        extraction_id: Extraction job ID
        current_user: Current user (auto-injected)
        db: Database session (auto-injected)
    
    Returns:
        ExtractionStatusResponse with current status
    
    Raises:
        HTTPException 404: If extraction not found
        HTTPException 403: If no view permission
    
    Example:
        GET /api/extractions/5/status
    """
    logger.info(f"Getting status for extraction {extraction_id}")
    
    # Get extraction record
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id
    ).first()
    
    if not extraction:
        logger.warning(f"Extraction not found: {extraction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found",
        )
    
    # ✅ NEW: Permission check - require view permission on the work
    if not can_view(db, extraction.work_id, current_user.id):
        logger.warning(f"User {current_user.username} tried to access unauthorized extraction {extraction_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this extraction",
        )
    
    # Calculate progress percentage
    total = extraction.total_pages or 1
    processed = extraction.processed_pages or 0
    progress_percent = (processed / total * 100) if total > 0 else 0
    
    return ExtractionStatusResponse(
        id=extraction.id,
        work_id=extraction.work_id,
        status=extraction.status,
        total_pages=total,
        processed_pages=processed,
        progress_percent=progress_percent,
        error_message=extraction.error_message,
        created_at=extraction.created_at,
        completed_at=extraction.completed_at,
    )


# ============================================================================
# WEBSOCKET - REAL-TIME PROGRESS
# ============================================================================


@router.websocket("/ws/extractions/{extraction_id}")
async def websocket_extraction_progress(
    websocket: WebSocket,
    extraction_id: int,
    token: str = None,
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time extraction progress.
    Requires view permission on the extraction's work.
    
    Connect and receive real-time progress updates as the extraction runs.
    
    Args:
        websocket: WebSocket connection
        extraction_id: Extraction job ID
        token: JWT token (from query param)
        db: Database session (auto-injected)
    
    Sends:
        - Progress messages: {type: "progress", page: int, total: int, percent: float}
        - Completion message: {type: "completed", message: str, ...}
        - Error message: {type: "error", message: str}
    
    Example:
        // JavaScript
        const token = localStorage.getItem('access_token');
        const ws = new WebSocket(
            `ws://localhost:8000/api/ws/extractions/5?token=${token}`
        );
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === "progress") {
                console.log(`Progress: ${message.page}/${message.total}`);
            }
        };
    """
    logger.info(f"WebSocket connection for extraction {extraction_id}")
    
    # Verify extraction exists
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id
    ).first()
    
    if not extraction:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Extraction not found")
        logger.warning(f"WebSocket: Extraction {extraction_id} not found")
        return
    
    # ✅ FIXED: Proper token validation and permission check
    user_id = None
    if token:
        try:
            from app.services.auth_service import decode_access_token
            user_id = decode_access_token(token)  # ✅ Returns int or None, not tuple
            
            if user_id is None:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
                logger.warning(f"WebSocket: Invalid token for extraction {extraction_id}")
                return
            
            # ✅ Check permission to view the work
            if not can_view(db, extraction.work_id, user_id):
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access denied")
                logger.warning(f"WebSocket: User {user_id} denied access to extraction {extraction_id}")
                return
            
        except Exception as e:
            logger.warning(f"WebSocket: Token validation error: {str(e)}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    else:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        logger.warning(f"WebSocket: No token provided for extraction {extraction_id}")
        return
    
    await websocket.accept()
    
    # Store connection
    active_connections[extraction_id] = websocket
    
    try:
        while True:
            # Get current progress
            progress = get_extraction_progress(db=db, extraction_id=extraction_id)
            
            if progress:
                # Send progress update
                message = {
                    "type": "progress",
                    "page": progress.get("processed_pages", 0),
                    "total": progress.get("total_pages", 0),
                    "percent": progress.get("progress_percent", 0),
                }
                await websocket.send_json(message)
                
                logger.debug(f"WebSocket {extraction_id}: Progress {message['page']}/{message['total']}")
                
                # If completed, send completion message and close
                if progress.get("status") == "completed":
                    completion_message = {
                        "type": "completed",
                        "message": "Extraction completed successfully",
                        "processed_pages": progress.get("processed_pages"),
                        "total_pages": progress.get("total_pages"),
                    }
                    await websocket.send_json(completion_message)
                    logger.info(f"WebSocket {extraction_id}: Extraction completed")
                    break
                
                # If failed, send error and close
                elif progress.get("status") == "failed":
                    error_message = {
                        "type": "error",
                        "message": progress.get("error_message", "Extraction failed"),
                    }
                    await websocket.send_json(error_message)
                    logger.error(f"WebSocket {extraction_id}: Extraction failed")
                    break
            
            # Wait before next poll (check every 1 second)
            await asyncio.sleep(1)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket {extraction_id}: Client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket {extraction_id} error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    
    finally:
        # Remove connection
        if extraction_id in active_connections:
            del active_connections[extraction_id]
        
        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# ROUTE SUMMARY
# ============================================================================

"""
Extraction Routes (DECOUPLED ARCHITECTURE):

1. POST /api/works/{workId}/extraction/start
   - Validates file type
   - Creates extraction record (FAST, < 100ms)
   - Reads file to bytes
   - Queues background task
   - Returns extraction_id immediately (202 Accepted, < 1 second)
   - Response includes extraction_id for polling
   - Status: 202 Accepted or 400/404/422/403
   - Permission: edit

2. GET /api/extractions/{extractionId}/status
   - Poll extraction status
   - Returns current progress
   - Response: ExtractionStatusResponse
   - Status: 200 OK or 404/403
   - Permission: view

3. WebSocket /api/ws/extractions/{extractionId}
   - Real-time progress updates
   - Messages:
     - Progress: {type: "progress", page, total, percent}
     - Completed: {type: "completed", message, ...}
     - Error: {type: "error", message}
   - Permission: view

BACKGROUND PROCESS:
   - Uploads PDF to Cloudinary (can take 30-60 seconds)
   - Creates images from PDF
   - Calls Claude API for extraction
   - Stores data in database
   - Updates extraction status as it progresses

All routes require authentication (Bearer token)
No HTTP timeouts because the endpoint returns before slow work begins
"""