"""
Extraction Service - DECOUPLED VERSION
Separates fast database operations from slow upload/extraction operations

KEY CHANGE:
  - New upload_and_extract() function handles all slow work in background
  - run_extraction() is now called only by the background task
  - Endpoint returns immediately without waiting for uploads
"""

import logging
import json
import asyncio
import io
import base64
import re
from typing import Optional, Dict, List
from datetime import datetime

from sqlalchemy.orm import Session
import anthropic
import httpx
from PIL import Image

from app.models.extraction import Extraction, ExtractionStatus
from app.models.equipment import Equipment
from app.models.component import Component
from app.db.database import SessionLocal
from app.config import settings
from app.utils.extraction_rules import ExtractionRules
from app.utils.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


# ============================================================================
# BACKGROUND TASK: UPLOAD AND EXTRACT
# ============================================================================

async def upload_and_extract(
    extraction_id: int,
    work_id: int,
    file_bytes: bytes,
    filename: str,
) -> None:
    """
    Background task that handles PDF upload to Cloudinary and extraction.
    
    Called by the extraction endpoint AFTER extraction record is created.
    This function does ALL the slow work:
    1. Upload PDF to Cloudinary (can take 30-60 seconds)
    2. Call run_extraction() to process the PDF
    
    The HTTP response has already been sent to the client by this point,
    so timeouts here don't affect the user experience.
    
    Args:
        extraction_id: Extraction record ID
        work_id: Work project ID
        file_bytes: PDF file content as bytes
        filename: PDF filename for logging
    """
    db = SessionLocal()
    extraction = None
    
    try:
        logger.info(f"[Background Task] Starting upload_and_extract for extraction {extraction_id}")
        
        # Get the extraction record
        extraction = db.query(Extraction).filter(
            Extraction.id == extraction_id
        ).first()
        
        if not extraction:
            logger.error(f"[Background Task] Extraction {extraction_id} not found")
            return
        
        # ===== STEP 1: Upload PDF to Cloudinary =====
        logger.info(f"[Background Task] Uploading PDF to Cloudinary: {filename}")
        logger.info(f"[Background Task] File size: {len(file_bytes) / (1024*1024):.2f}MB")
        
        try:
            from app.utils.cloudinary_util import upload_pdf_to_cloudinary_from_bytes
            pdf_url = await upload_pdf_to_cloudinary_from_bytes(file_bytes, filename)
            logger.info(f"[Background Task] ✅ PDF uploaded: {pdf_url}")
        except Exception as e:
            logger.error(f"[Background Task] ❌ Cloudinary upload failed: {str(e)}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = f"Cloudinary upload failed: {str(e)}"
            db.commit()
            return
        
        # ===== STEP 2: Update extraction with PDF URL =====
        extraction.pdf_url = pdf_url
        db.commit()
        logger.info(f"[Background Task] Updated extraction {extraction_id} with pdf_url")
        
        # ===== STEP 3: Run extraction (this is the main processing) =====
        logger.info(f"[Background Task] Starting extraction pipeline for extraction {extraction_id}")
        
        try:
            await run_extraction(
                work_id=work_id,
                extraction_id=extraction_id,
                pdf_url=pdf_url,
                pdf_filename=filename,
            )
            logger.info(f"[Background Task] ✅ Extraction {extraction_id} completed successfully")
        except Exception as e:
            logger.error(f"[Background Task] ❌ Extraction failed: {str(e)}", exc_info=True)
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = f"Extraction processing failed: {str(e)}"
            db.commit()
            return
    
    except Exception as e:
        logger.error(f"[Background Task] Unexpected error in upload_and_extract: {str(e)}", exc_info=True)
        if extraction:
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = f"Unexpected error: {str(e)}"
            db.commit()
    
    finally:
        db.close()


# ============================================================================
# FILENAME PARSING
# ============================================================================

def parse_equipment_from_filename(filename: str) -> tuple[Optional[str], Optional[str]]:
    """Parse equipment_number and pmt_number from filename"""
    try:
        name = filename.replace('.pdf', '').strip()
        match = re.search(r'-\s*([VH]-\d{3})$', name)
        if not match:
            logger.warning(f"Could not parse equipment number from: {filename}")
            return None, None
        
        equipment_number = match.group(1)
        pmt_match = re.search(r'(PMT\s+\d+)', name, re.IGNORECASE)
        pmt_number = pmt_match.group(1).replace(' ', ' ') if pmt_match else None
        
        logger.info(f"Parsed from {filename}: equipment={equipment_number}, pmt={pmt_number}")
        return equipment_number, pmt_number
    
    except Exception as e:
        logger.error(f"Error parsing filename {filename}: {str(e)}")
        return None, None


# ============================================================================
# PDF TO IMAGES
# ============================================================================

async def convert_pdf_to_images(pdf_url: str) -> List:
    """Download PDF from Cloudinary and convert to images"""
    try:
        from pdf2image import convert_from_bytes
        
        logger.info(f"Downloading PDF from: {pdf_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content
        
        logger.info(f"Downloaded PDF: {len(pdf_bytes)} bytes")
        
        logger.info("Converting PDF to images...")
        images = convert_from_bytes(pdf_bytes, fmt='png')
        
        logger.info(f"✅ Converted PDF to {len(images)} images")
        return images
    
    except Exception as e:
        logger.error(f"❌ Failed to convert PDF: {str(e)}")
        raise


# ============================================================================
# CLAUDE API EXTRACTION
# ============================================================================

def compress_image_bytes_for_api(image_bytes: bytes) -> bytes:
    """
    Compress PNG image bytes if they would exceed Claude's 5MB limit after base64 encoding.
    Uses PNG-only compression methods following your exact approach.
    Returns compressed image bytes.
    """
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    OPTIMAL_LONG_EDGE = 1568  # Anthropic's recommended max dimension
    
    try:
        # Base64 encoding increases size by ~33%, so check if encoded size will exceed limit
        # Use 3.75MB threshold (3.75 * 1.33 ≈ 5MB) - YOUR EXACT LOGIC
        SAFE_SIZE_BEFORE_BASE64 = int(MAX_SIZE_BYTES * 0.75)  # 3.75MB
        
        # If under safe threshold, return original without modification
        if len(image_bytes) <= SAFE_SIZE_BEFORE_BASE64:
            size_mb = len(image_bytes) / (1024 * 1024)
            logger.debug(f"  ✅ Original size {size_mb:.2f}MB - no compression needed")
            return image_bytes
        
        # Image is too large, need to compress
        logger.info(f"  ⚠️ Original size {len(image_bytes) / (1024 * 1024):.2f}MB exceeds 5MB - compressing PNG...")
        
        with Image.open(io.BytesIO(image_bytes)) as img:
            original_mode = img.mode
            
            # Step 1: Try optimize + compress_level=9 on original size
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            # Check ACTUAL base64 size (not approximation)
            compressed_data = buffer.getvalue()
            base64_size = len(base64.b64encode(compressed_data))  # ACTUAL base64 size
            
            if base64_size <= MAX_SIZE_BYTES:
                size_mb = base64_size / (1024 * 1024)
                logger.info(f"  ✅ Compressed to {size_mb:.2f}MB base64 (PNG optimize + compress_level=9)")
                return compressed_data
            
            # Step 2: Try resizing to optimal dimension
            width, height = img.size
            max_dimension = max(width, height)
            
            if max_dimension > OPTIMAL_LONG_EDGE:
                scale_factor = OPTIMAL_LONG_EDGE / max_dimension
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"  Resized from {width}x{height} to {new_size[0]}x{new_size[1]}")
                
                buffer = io.BytesIO()
                img_resized.save(buffer, format='PNG', optimize=True, compress_level=9)
                buffer.seek(0)
                
                # Check ACTUAL base64 size
                compressed_data = buffer.getvalue()
                base64_size = len(base64.b64encode(compressed_data))
                
                if base64_size <= MAX_SIZE_BYTES:
                    size_mb = base64_size / (1024 * 1024)
                    logger.info(f"  ✅ Compressed to {size_mb:.2f}MB base64 (PNG resized + optimized)")
                    return compressed_data
                
                img = img_resized  # Use resized for next steps
            
            # Step 3: Try color quantization (24-bit → 8-bit, 256 colors)
            # This is still PNG, just with fewer colors
            logger.info(f"  Applying color quantization (256 colors)...")
            if img.mode != 'P':  # Only quantize if not already palettized
                # Convert to RGB first if RGBA - YOUR EXACT LOGIC
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                
                img_quantized = img.quantize(colors=256)
            else:
                img_quantized = img
            
            buffer = io.BytesIO()
            img_quantized.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            # Check ACTUAL base64 size
            compressed_data = buffer.getvalue()
            base64_size = len(base64.b64encode(compressed_data))
            
            if base64_size <= MAX_SIZE_BYTES:
                size_mb = base64_size / (1024 * 1024)
                logger.info(f"  ✅ Compressed to {size_mb:.2f}MB base64 (PNG 256-color)")
                return compressed_data
            
            # Step 4: Emergency - more aggressive resize - YOUR EXACT LOGIC
            logger.info(f"  ⚠️ Applying emergency resize (50%)...")
            width, height = img.size
            new_size = (int(width * 0.5), int(height * 0.5))
            img_emergency = img.resize(new_size, Image.Resampling.LANCZOS)
            
            if img_emergency.mode != 'P':
                img_emergency = img_emergency.quantize(colors=256)
            
            buffer = io.BytesIO()
            img_emergency.save(buffer, format='PNG', optimize=True, compress_level=9)
            buffer.seek(0)
            
            compressed_data = buffer.getvalue()
            base64_size = len(base64.b64encode(compressed_data))
            size_mb = base64_size / (1024 * 1024)
            
            logger.info(f"  Final size: {size_mb:.2f}MB base64 (PNG 50% resize + 256 colors)")
            return compressed_data
            
    except Exception as e:
        logger.error(f"  ❌ Error processing image: {e}")
        # Last resort: try original image
        return image_bytes

async def extract_from_image(
    image_bytes: bytes,
    equipment_number: str,
    pmt_number: str,
    description: str,
    components: Dict[str, Dict],
    prompt: Optional[str] = None
) -> str:
    """Extract component data from image using equipment-specific prompt"""
    try:

        # Compress image if it's too large for Claude
        logger.debug(f"Original image size: {len(image_bytes):,} bytes")
        compressed_bytes = compress_image_bytes_for_api(image_bytes)
        logger.debug(f"Compressed image size: {len(compressed_bytes):,} bytes")
        
        image_base64 = base64.standard_b64encode(compressed_bytes).decode("utf-8")

        # Verify we're under the limit
        base64_size = len(compressed_bytes) * 3 / 4  # Approximate byte size
        max_size = 5 * 1024 * 1024  # 5MB
        
        if base64_size > max_size:
            logger.error(f"Image still too large: {base64_size:.0f} bytes > {max_size} bytes")
            raise ValueError(f"Image exceeds Claude's 5MB limit after compression: {base64_size:.0f} bytes")
        
        logger.debug(f"Base64 image size: ~{base64_size:.0f} bytes")

        
        # Build prompt if not provided
        if not prompt:
            rules = ExtractionRules()
            components_with_expected = rules.get_components_for_equipment(equipment_number)
            prompt = PromptBuilder.build_extraction_prompt(
                equipment_number, pmt_number, description, components_with_expected,
                retry_missing_fields=None
            )
        
        logger.debug(f"Calling Claude API for {equipment_number}")
        
        # Run blocking Claude API call in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            _call_claude_api,
            image_base64,
            prompt
        )
        
        response_text = message.content[0].text
        logger.debug(f"Claude response: {len(response_text)} chars")
        
        return response_text
    
    except Exception as e:
        logger.error(f"❌ Claude API error: {str(e)}")
        raise


def _call_claude_api(image_base64: str, prompt: str):
    """
    Blocking wrapper for Claude API call.
    Runs in executor to prevent blocking event loop.
    
    This function is synchronous and called via asyncio.run_in_executor()
    so that the blocking HTTP request to Claude API doesn't prevent other
    tasks from running on the event loop.
    """
    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
    
    return client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64,
                    },
                },
                {"type": "text", "text": prompt}
            ],
        }],
    )


# ============================================================================
# PARSE RESPONSE
# ============================================================================

def parse_extraction_response(response: str) -> Dict:
    """Parse Claude's JSON response"""
    try:
        data = json.loads(response)
        logger.debug(f"Parsed JSON: {len(data.get('components', []))} components")
        return data
    
    except json.JSONDecodeError:
        try:
            match = re.search(r'```(?:json)?\n?(.*?)\n?```', response, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                logger.debug(f"Parsed JSON from markdown: {len(data.get('components', []))} components")
                return data
        except:
            pass
        
        logger.error(f"Failed to parse response: {response[:100]}...")
        raise ValueError("Could not parse extraction response as JSON")


# ============================================================================
# STORE DATA
# ============================================================================

async def store_equipment_data(
    db: Session,
    work_id: int,
    equipment_number: str,
    pmt_number: str,
    description: str,
    components_data: List[Dict],
) -> int:
    """Store extracted equipment and components in database"""
    try:
        logger.info(f"Storing {equipment_number} data for work {work_id}")
        
        # Create or update equipment
        equipment = db.query(Equipment).filter(
            Equipment.work_id == work_id,
            Equipment.equipment_number == equipment_number
        ).first()
        
        if not equipment:
            equipment = Equipment(
                work_id=work_id,
                equipment_number=equipment_number,
                pmt_number=pmt_number,
                description=description,
                extracted_date=datetime.utcnow(),
            )
            db.add(equipment)
            db.flush()
            logger.debug(f"Created equipment: {equipment_number}")
        else:
            equipment.pmt_number = pmt_number
            equipment.description = description
            equipment.extracted_date = datetime.utcnow()
        
        # Store components
        component_count = 0
        for comp_data in components_data:
            existing = db.query(Component).filter(
                Component.equipment_id == equipment.id,
                Component.component_name == comp_data.get('component_name')
            ).first()
            
            if existing:
                # Update
                for key in ['phase', 'fluid', 'material_spec', 'material_grade',
                           'insulation', 'design_temp', 'design_pressure',
                           'operating_temp', 'operating_pressure']:
                    if comp_data.get(key):
                        setattr(existing, key, comp_data.get(key))
            else:
                # Create new
                component = Component(
                    equipment_id=equipment.id,
                    component_name=comp_data.get('component_name'),
                    phase=comp_data.get('phase'),
                    fluid=comp_data.get('fluid'),
                    material_spec=comp_data.get('material_spec'),
                    material_grade=comp_data.get('material_grade'),
                    insulation=comp_data.get('insulation'),
                    design_temp=comp_data.get('design_temp'),
                    design_pressure=comp_data.get('design_pressure'),
                    operating_temp=comp_data.get('operating_temp'),
                    operating_pressure=comp_data.get('operating_pressure'),
                )
                db.add(component)
            
            component_count += 1
        
        db.commit()
        logger.info(f"✅ Stored {equipment_number}: {component_count} components")
        
        return component_count
    
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to store data: {str(e)}")
        raise


# ============================================================================
# MAIN EXTRACTION PIPELINE
# ============================================================================

async def run_extraction(
    work_id: int,
    extraction_id: int,
    pdf_url: str,
    pdf_filename: str,
) -> None:
    """
    Main extraction pipeline with intelligent retry logic.
    
    Called by upload_and_extract() background task.
    By this point, the PDF has already been uploaded to Cloudinary.
    
    Process:
    1. Parse filename to get equipment_number and pmt_number
    2. Load equipment metadata
    3. Convert PDF to images
    4. Pass 1: Initial extraction on all pages
    5. Check completeness (target: 85%)
    6. Pass 2+: Retry for missing fields (max 2 retries)
    7. Store data when complete
    """
    
    db = SessionLocal()
    extraction = None
    
    try:
        logger.info(f"Starting extraction pipeline for work {work_id}, extraction {extraction_id}")
        
        extraction = db.query(Extraction).filter(
            Extraction.id == extraction_id
        ).first()
        
        if not extraction:
            logger.error(f"Extraction {extraction_id} not found")
            return
        
        # Mark as in progress
        extraction.status = ExtractionStatus.IN_PROGRESS
        db.commit()
        
        # ===== STEP 1: PARSE FILENAME =====
        logger.info("Step 1: Parsing equipment from filename...")
        equipment_number, pmt_number = parse_equipment_from_filename(pdf_filename)
        
        if not equipment_number:
            error = f"Could not parse equipment number from filename: {pdf_filename}"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        # ===== STEP 2: LOAD EQUIPMENT METADATA =====
        rules = ExtractionRules()
        equipment_meta = rules.get_equipment(equipment_number)
        
        if not equipment_meta:
            error = f"Equipment {equipment_number} not found in rules"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        description = equipment_meta.get('description', '')
        components_with_expected = equipment_meta.get('components', {})
        
        logger.info(f"✅ Equipment: {equipment_number} ({description})")
        logger.info(f"   Components: {', '.join(components_with_expected.keys())}")
        
        # ===== STEP 3: CONVERT PDF =====
        logger.info("Step 2: Converting PDF to images...")
        try:
            images = await convert_pdf_to_images(pdf_url)
        except Exception as e:
            error = f"Failed to convert PDF: {str(e)}"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        extraction.total_pages = len(images)
        db.commit()
        logger.info(f"Step 2 complete: {len(images)} pages")
        
        # ===== STEP 4: EXTRACT DATA (WITH RETRY) =====
        logger.info("Step 3: Extracting component data...")
        extracted_data = None
        completeness_threshold = 85
        
        # PASS 1: Initial extraction
        logger.info("📖 Pass 1: Initial extraction...")
        for page_num, image in enumerate(images):
            try:
                logger.info(f"  Processing page {page_num + 1}/{len(images)}...")
                
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                image_data = img_bytes.getvalue()
                
                response = await extract_from_image(
                    image_data, equipment_number, pmt_number, description, 
                    components_with_expected, prompt=None
                )
                
                page_data = parse_extraction_response(response)
                
                if page_data.get('components'):
                    extracted_data = page_data
                    completeness, missing = rules.get_completeness_score(equipment_number, page_data)
                    logger.info(f"  ✅ Page {page_num + 1} extracted (completeness: {completeness:.0f}%)")
                    
                    if completeness >= completeness_threshold:
                        logger.info(f"     Completeness {completeness:.0f}% >= threshold, done with Pass 1")
                        extraction.processed_pages = len(images)
                        break
                    else:
                        logger.info(f"     Completeness {completeness:.0f}% < {completeness_threshold}%, will retry")
                
                extraction.processed_pages = page_num + 1
                db.commit()
            
            except Exception as e:
                logger.warning(f"  ⚠️  Error on page {page_num + 1}: {str(e)}")
                continue
        
        # Check if we have data
        if not extracted_data:
            error = "Pass 1: No extraction data from any page"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        # PASS 2+: Retry for missing fields
        completeness, missing_by_comp = rules.get_completeness_score(equipment_number, extracted_data)
        
        for retry_num in range(1, 3):  # Max 2 retries
            if completeness >= completeness_threshold:
                logger.info(f"✅ Completeness {completeness:.0f}% is sufficient, stopping retries")
                break
            
            logger.info(f"📖 Pass {retry_num + 1}: Retry for missing fields...")
            logger.info(f"   Current completeness: {completeness:.0f}%")
            logger.info(f"   Missing: {missing_by_comp}")
            
            # Build retry prompt
            retry_prompt = PromptBuilder.build_extraction_prompt(
                equipment_number, pmt_number, description,
                components_with_expected, retry_missing_fields=missing_by_comp
            )
            
            # Try each page again
            for page_num, image in enumerate(images):
                try:
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    image_data = img_bytes.getvalue()
                    
                    response = await extract_from_image(
                        image_data, equipment_number, pmt_number, description,
                        components_with_expected, prompt=retry_prompt
                    )
                    
                    retry_data = parse_extraction_response(response)
                    
                    # Merge: update existing components with retry data
                    for retry_comp in retry_data.get('components', []):
                        for existing_comp in extracted_data.get('components', []):
                            if existing_comp.get('component_name') == retry_comp.get('component_name'):
                                # Only update if retry has non-empty value
                                for key in ['fluid', 'material_spec', 'material_grade', 'insulation',
                                          'design_temp', 'design_pressure', 'operating_temp', 'operating_pressure']:
                                    if retry_comp.get(key) and str(retry_comp.get(key)).strip():
                                        existing_comp[key] = retry_comp.get(key)
                                break
                    
                    logger.info(f"   ✅ Page {page_num + 1} merged")
                
                except Exception as e:
                    logger.warning(f"   ⚠️  Retry error on page {page_num + 1}: {str(e)}")
                    continue
            
            # Recalculate completeness
            completeness, missing_by_comp = rules.get_completeness_score(equipment_number, extracted_data)
            logger.info(f"   Updated completeness: {completeness:.0f}%")
        
        # ===== STEP 5: FINAL CHECK =====
        final_completeness, final_missing = rules.get_completeness_score(equipment_number, extracted_data)
        logger.info(f"Step 3 complete: Extraction done")
        logger.info(f"  Final completeness: {final_completeness:.0f}%")
        
        if final_missing:
            logger.warning(f"  ⚠️  Some fields still missing: {final_missing}")
        
        # ===== STEP 6: STORE DATA =====
        try:
            logger.info("Step 4: Storing data in database...")
            component_count = await store_equipment_data(
                db=db,
                work_id=work_id,
                equipment_number=equipment_number,
                pmt_number=pmt_number,
                description=description,
                components_data=extracted_data.get('components', [])
            )
            logger.info(f"Step 4 complete: Stored {component_count} components")
        except Exception as e:
            error = f"Failed to store data: {str(e)}"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        # ===== SUCCESS =====
        extraction.status = ExtractionStatus.COMPLETED
        extraction.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Extraction {extraction_id} completed successfully!")
    
    except Exception as e:
        error = f"Unexpected error: {str(e)}"
        logger.error(f"❌ {error}", exc_info=True)
        
        if extraction:
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
    
    finally:
        db.close()


# ============================================================================
# GET PROGRESS
# ============================================================================

def get_extraction_progress(db: Session, extraction_id: int) -> Dict:
    """Get extraction job progress"""
    
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id
    ).first()
    
    if not extraction:
        return {}
    
    total = extraction.total_pages or 1
    processed = extraction.processed_pages or 0
    percent = (processed / total * 100) if total > 0 else 0
    
    return {
        "id": extraction.id,
        "work_id": extraction.work_id,
        "status": extraction.status,
        "total_pages": total,
        "processed_pages": processed,
        "progress_percent": percent,
        "error_message": extraction.error_message,
        "created_at": extraction.created_at,
        "completed_at": extraction.completed_at,
    }