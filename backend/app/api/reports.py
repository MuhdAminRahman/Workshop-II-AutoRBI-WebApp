"""
Reports API Routes - FINAL VERSION
Users upload templates to work, then generate reports from them

POST /api/works/{workId}/templates/excel - Upload Excel template
POST /api/works/{workId}/templates/powerpoint - Upload PowerPoint template
POST /api/works/{workId}/reports/generate-excel - Generate Excel report
POST /api/works/{workId}/reports/generate-powerpoint - Generate PowerPoint report
GET /api/works/{workId}/reports - List all reports
GET /api/works/{workId}/reports/{fileId}/download - Download report
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.work import Work
from app.models.file import File as FileModel, FileType
from app.dependencies import get_current_user
from app.services.reports_service import generate_excel_report, generate_powerpoint_report
from app.utils.cloudinary_util import upload_excel_to_cloudinary, upload_ppt_to_cloudinary

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# UPLOAD TEMPLATES TO WORK
# ============================================================================

@router.post(
    "/{work_id}/templates/excel",
    status_code=status.HTTP_201_CREATED,
    summary="Upload Excel Template",
    description="Upload Masterfile Excel template for this work",
)
async def upload_excel_template(
    work_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload Excel Masterfile template for work.
    
    Stores template URL in Work record for later use in report generation.
    
    Args:
        work_id: Work project ID
        file: Excel template file (xlsx)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        {
            "work_id": 1,
            "file_type": "excel",
            "file_url": "https://...",
            "message": "Template uploaded successfully"
        }
    """
    try:
        logger.info(f"User {current_user.username} uploading Excel template for work {work_id}")
        
        # Verify work exists and belongs to user
        work = db.query(Work).filter(
            Work.id == work_id,
            Work.user_id == current_user.id
        ).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work not found"
            )
        
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must be Excel (.xlsx)"
            )
        
        # Read file
        file_content = await file.read()
        
        # Upload to Cloudinary
        file_url = await upload_excel_to_cloudinary(
            file_bytes=file_content,
            filename=f"work_{work_id}_excel_masterfile.xlsx"
        )
        
        logger.info(f"✅ Excel template uploaded: {file_url}")
        
        # Save URL to Work record
        work.excel_masterfile_url = file_url
        db.commit()
        
        return {
            "work_id": work_id,
            "file_type": "excel",
            "file_url": file_url,
            "message": "Excel template uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading Excel template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload template: {str(e)}"
        )


@router.post(
    "/{work_id}/templates/powerpoint",
    status_code=status.HTTP_201_CREATED,
    summary="Upload PowerPoint Template",
    description="Upload PowerPoint template for this work",
)
async def upload_powerpoint_template(
    work_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload PowerPoint template for work.
    
    Stores template URL in Work record for later use in report generation.
    
    Args:
        work_id: Work project ID
        file: PowerPoint template file (pptx)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        {
            "work_id": 1,
            "file_type": "powerpoint",
            "file_url": "https://...",
            "message": "Template uploaded successfully"
        }
    """
    try:
        logger.info(f"User {current_user.username} uploading PowerPoint template for work {work_id}")
        
        # Verify work exists and belongs to user
        work = db.query(Work).filter(
            Work.id == work_id,
            Work.user_id == current_user.id
        ).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work not found"
            )
        
        if not file.filename.endswith('.pptx'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File must be PowerPoint (.pptx)"
            )
        
        # Read file
        file_content = await file.read()
        
        # Upload to Cloudinary
        file_url = await upload_ppt_to_cloudinary(
            file_bytes=file_content,
            filename=f"work_{work_id}_ppt_template.pptx"
        )
        
        logger.info(f"✅ PowerPoint template uploaded: {file_url}")
        
        # Save URL to Work record
        work.ppt_template_url = file_url
        db.commit()
        
        return {
            "work_id": work_id,
            "file_type": "powerpoint",
            "file_url": file_url,
            "message": "PowerPoint template uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PowerPoint template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload template: {str(e)}"
        )


# ============================================================================
# GENERATE REPORTS
# ============================================================================

@router.post(
    "/{work_id}/reports/generate-excel",
    status_code=status.HTTP_201_CREATED,
    summary="Generate Excel Report",
    description="Generate Excel report from extracted equipment data",
)
async def generate_excel(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate Excel report from extracted equipment data.
    
    Requires Excel template to be uploaded first.
    Auto-generates as v1, user can regenerate as v2, v3, etc.
    
    Args:
        work_id: Work project ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        {
            "file_id": 123,
            "work_id": 1,
            "file_type": "excel",
            "version": 1,
            "file_url": "https://...",
            "created_at": "..."
        }
    """
    try:
        logger.info(f"User {current_user.username} generating Excel for work {work_id}")
        
        # Verify work exists and belongs to user
        work = db.query(Work).filter(
            Work.id == work_id,
            Work.user_id == current_user.id
        ).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work not found"
            )
        
        # Check template exists
        if not work.excel_masterfile_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel template not uploaded. Please upload template first."
            )
        
        # Check equipment exists
        from app.models.equipment import Equipment
        equipment_count = db.query(Equipment).filter(
            Equipment.work_id == work_id
        ).count()
        
        if equipment_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No equipment extracted yet. Please extract data first."
            )
        
        # Get next version
        latest_file = db.query(FileModel).filter(
            FileModel.work_id == work_id,
            FileModel.file_type == FileType.EXCEL
        ).order_by(FileModel.version_number.desc()).first()
        
        next_version = (latest_file.version_number + 1) if latest_file else 1
        
        logger.info(f"Generating Excel v{next_version} for work {work_id}")
        
        # Generate report
        file_url = await generate_excel_report(
            db=db,
            work_id=work_id,
            template_url=work.excel_masterfile_url
        )
        
        # Save to database
        file_record = FileModel(
            work_id=work_id,
            created_by=current_user.id,
            file_type=FileType.EXCEL,
            version_number=next_version,
            file_url=file_url
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        logger.info(f"✅ Excel v{next_version} generated and saved")
        
        return {
            "file_id": file_record.id,
            "work_id": work_id,
            "file_type": "excel",
            "version": next_version,
            "file_url": file_url,
            "created_at": file_record.created_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Excel: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel: {str(e)}"
        )


@router.post(
    "/{work_id}/reports/generate-powerpoint",
    status_code=status.HTTP_201_CREATED,
    summary="Generate PowerPoint Report",
    description="Generate PowerPoint report from extracted equipment data",
)
async def generate_powerpoint(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate PowerPoint report from extracted equipment data.
    
    Requires PowerPoint template to be uploaded first.
    Auto-generates as v1, user can regenerate as v2, v3, etc.
    
    Args:
        work_id: Work project ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        {
            "file_id": 124,
            "work_id": 1,
            "file_type": "powerpoint",
            "version": 1,
            "file_url": "https://...",
            "created_at": "..."
        }
    """
    try:
        logger.info(f"User {current_user.username} generating PowerPoint for work {work_id}")
        
        # Verify work exists and belongs to user
        work = db.query(Work).filter(
            Work.id == work_id,
            Work.user_id == current_user.id
        ).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work not found"
            )
        
        # Check template exists
        if not work.ppt_template_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PowerPoint template not uploaded. Please upload template first."
            )
        
        # Check equipment exists
        from app.models.equipment import Equipment
        equipment_count = db.query(Equipment).filter(
            Equipment.work_id == work_id
        ).count()
        
        if equipment_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No equipment extracted yet. Please extract data first."
            )
        
        # Get next version
        latest_file = db.query(FileModel).filter(
            FileModel.work_id == work_id,
            FileModel.file_type == FileType.POWERPOINT
        ).order_by(FileModel.version_number.desc()).first()
        
        next_version = (latest_file.version_number + 1) if latest_file else 1
        
        logger.info(f"Generating PowerPoint v{next_version} for work {work_id}")
        
        # Generate report
        file_url = await generate_powerpoint_report(
            db=db,
            work_id=work_id,
            template_url=work.ppt_template_url
        )
        
        # Save to database
        file_record = FileModel(
            work_id=work_id,
            created_by=current_user.id,
            file_type=FileType.POWERPOINT,
            version_number=next_version,
            file_url=file_url
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        logger.info(f"✅ PowerPoint v{next_version} generated and saved")
        
        return {
            "file_id": file_record.id,
            "work_id": work_id,
            "file_type": "powerpoint",
            "version": next_version,
            "file_url": file_url,
            "created_at": file_record.created_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PowerPoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PowerPoint: {str(e)}"
        )


# ============================================================================
# LIST AND DOWNLOAD REPORTS
# ============================================================================

@router.get(
    "/{work_id}/reports",
    summary="List Reports",
    description="Get all generated reports for a work project",
)
async def list_reports(
    work_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all reports (Excel and PowerPoint) for a work project.
    
    Returns:
        {
            "work_id": 1,
            "reports": [
                {
                    "file_id": 123,
                    "file_type": "excel",
                    "version": 1,
                    "file_url": "https://...",
                    "created_at": "..."
                },
                ...
            ]
        }
    """
    try:
        logger.info(f"User {current_user.username} listing reports for work {work_id}")
        
        # Verify work exists
        work = db.query(Work).filter(
            Work.id == work_id,
            Work.user_id == current_user.id
        ).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work not found"
            )
        
        # Get all reports
        files = db.query(FileModel).filter(
            FileModel.work_id == work_id
        ).order_by(FileModel.created_at.desc()).all()
        
        reports = [
            {
                "file_id": f.id,
                "file_type": f.file_type,
                "version": f.version_number,
                "file_url": f.file_url,
                "created_at": f.created_at
            }
            for f in files
        ]
        
        return {
            "work_id": work_id,
            "reports": reports
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list reports"
        )


@router.get(
    "/{work_id}/reports/{file_id}/download",
    summary="Download Report",
    description="Download a specific report file",
)
async def download_report(
    work_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download report file.
    
    Returns redirect URL to Cloudinary.
    
    Returns:
        { "file_url": "https://..." }
    """
    try:
        logger.info(f"User {current_user.username} downloading report {file_id}")
        
        # Verify work exists
        work = db.query(Work).filter(
            Work.id == work_id,
            Work.user_id == current_user.id
        ).first()
        
        if not work:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work not found"
            )
        
        # Get file
        file = db.query(FileModel).filter(
            FileModel.id == file_id,
            FileModel.work_id == work_id
        ).first()
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return {"file_url": file.file_url}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download report"
        )