"""
Extraction Service - UPDATED
Extracts component data for known equipment
"""

import logging
import json
import io
import base64
import re
from typing import Optional, Dict, List
from datetime import datetime

from sqlalchemy.orm import Session
import anthropic
import httpx

from app.models.extraction import Extraction, ExtractionStatus
from app.models.equipment import Equipment
from app.models.component import Component
from app.db.database import SessionLocal
from app.config import settings
from app.utils.extraction_rules import ExtractionRules
from app.utils.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


# ============================================================================
# FILENAME PARSING
# ============================================================================


def parse_equipment_from_filename(filename: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse equipment_number and pmt_number from filename.
    
    Expected format: "MLK PMT 10103 - V-003.pdf"
    Returns: (equipment_number, pmt_number) or (None, None) if parse fails
    """
    try:
        # Remove file extension
        name = filename.replace('.pdf', '').strip()
        
        # Pattern: "... - EQUIPMENT_NUMBER"
        match = re.search(r'-\s*([VH]-\d{3})$', name)
        if not match:
            logger.warning(f"Could not parse equipment number from: {filename}")
            return None, None
        
        equipment_number = match.group(1)
        
        # Pattern: "PMT \d+"
        pmt_match = re.search(r'(PMT\s+\d+)', name, re.IGNORECASE)
        pmt_number = pmt_match.group(1).replace(' ', ' ') if pmt_match else None
        
        logger.info(f"Parsed from {filename}: equipment={equipment_number}, pmt={pmt_number}")
        return equipment_number, pmt_number
    
    except Exception as e:
        logger.error(f"Error parsing filename {filename}: {str(e)}")
        return None, None


# ============================================================================
# PDF TO IMAGES CONVERSION
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


async def extract_from_image(
    image_bytes: bytes,
    equipment_number: str,
    pmt_number: str,
    description: str,
    components: Dict[str, str]
) -> str:
    """
    Extract component data from image using equipment-specific prompt.
    
    Args:
        image_bytes: Image data (PNG)
        equipment_number: e.g., 'V-003'
        pmt_number: e.g., 'MLK PMT 10103'
        description: Equipment description
        components: {component_name: phase}
    
    Returns:
        JSON string with extracted data
    """
    try:
        image_base64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        
        # Load expected values from rules
        rules = ExtractionRules()
        components_with_expected = rules.get_components_for_equipment(equipment_number)
        
        # Build equipment-specific prompt with expected value hints
        prompt = PromptBuilder.build_extraction_prompt(
            equipment_number, pmt_number, description, components_with_expected
        )
        
        logger.debug(f"Calling Claude API for {equipment_number}")
        
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        
        message = client.messages.create(
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
        
        response_text = message.content[0].text
        logger.debug(f"Claude response: {len(response_text)} chars")
        
        return response_text
    
    except Exception as e:
        logger.error(f"❌ Claude API error: {str(e)}")
        raise


# ============================================================================
# PARSE CLAUDE RESPONSE
# ============================================================================


def parse_extraction_response(response: str) -> Dict:
    """Parse Claude's JSON response"""
    try:
        # Try direct JSON parse
        data = json.loads(response)
        logger.debug(f"Parsed JSON: {len(data.get('components', []))} components")
        return data
    
    except json.JSONDecodeError:
        try:
            # Fallback: extract JSON from markdown code blocks
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
# VALIDATE EXTRACTED DATA
# ============================================================================


def validate_extracted_data(
    data: Dict,
    expected_components: Dict[str, str]
) -> tuple[bool, List[str]]:
    """
    Validate extracted data has expected components.
    Returns (is_complete, missing_components)
    """
    extracted_comps = set(c.get('component_name') for c in data.get('components', []))
    expected_comps = set(expected_components.keys())
    
    missing = list(expected_comps - extracted_comps)
    
    if missing:
        logger.warning(f"Missing components: {missing}")
    
    return len(missing) == 0, missing


# ============================================================================
# STORE EXTRACTED DATA
# ============================================================================


async def store_equipment_data(
    db: Session,
    work_id: int,
    equipment_number: str,
    pmt_number: str,
    description: str,
    components_data: List[Dict],
) -> int:
    """
    Store extracted equipment and components in database.
    
    Returns:
        Number of components stored
    """
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
            # Update existing equipment
            equipment.pmt_number = pmt_number
            equipment.description = description
            equipment.extracted_date = datetime.utcnow()
        
        # Store components
        component_count = 0
        for comp_data in components_data:
            # Skip if component already exists
            existing = db.query(Component).filter(
                Component.equipment_id == equipment.id,
                Component.component_name == comp_data.get('component_name')
            ).first()
            
            if existing:
                # Update existing component
                for key in ['phase', 'fluid', 'material_spec', 'material_grade',
                           'insulation', 'design_temp', 'design_pressure',
                           'operating_temp', 'operating_pressure']:
                    if comp_data.get(key):
                        setattr(existing, key, comp_data.get(key))
            else:
                # Create new component
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
    Extract component data from PDF for known equipment.
    
    1. Parse filename to get equipment_number and pmt_number
    2. Load equipment metadata (components, description)
    3. Extract component data from each page with targeted prompt
    4. Store in database
    """
    
    db = SessionLocal()
    extraction = None
    
    try:
        logger.info(f"Starting extraction for work {work_id}, file: {pdf_filename}")
        
        extraction = db.query(Extraction).filter(
            Extraction.id == extraction_id
        ).first()
        
        if not extraction:
            logger.error(f"Extraction {extraction_id} not found")
            return
        
        # Mark as in progress
        extraction.status = ExtractionStatus.IN_PROGRESS
        db.commit()
        
        # Step 1: Parse filename to get equipment_number and pmt_number
        logger.info("Step 1: Parsing equipment from filename...")
        equipment_number, pmt_number = parse_equipment_from_filename(pdf_filename)
        
        if not equipment_number:
            error = f"Could not parse equipment number from filename: {pdf_filename}"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        # Step 2: Load equipment metadata
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
        components = equipment_meta.get('components', {})
        
        logger.info(f"✅ Equipment: {equipment_number} ({description})")
        logger.info(f"   Components: {', '.join(components.keys())}")
        
        # Step 3: Convert PDF to images
        try:
            logger.info("Step 2: Converting PDF to images...")
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
        
        # Step 4: Extract component data from images
        logger.info("Step 3: Extracting component data from images...")
        extracted_data = None
        
        for page_num, image in enumerate(images):
            try:
                logger.info(f"Processing page {page_num + 1}/{len(images)}...")
                
                # Convert PIL Image to PNG bytes
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                image_data = img_bytes.getvalue()
                
                # Extract from Claude
                response = await extract_from_image(
                    image_data,
                    equipment_number,
                    pmt_number,
                    description,
                    components
                )
                
                # Parse response
                page_data = parse_extraction_response(response)
                
                # Validate response
                is_complete, missing = validate_extracted_data(page_data, components)
                
                if is_complete or page_data.get('components'):
                    # Check extraction quality against expected values
                    rules = ExtractionRules()
                    expected_comps = rules.get_components_for_equipment(equipment_number)
                    confidence_score = 0
                    valid_fields = 0
                    
                    for comp in page_data.get('components', []):
                        comp_name = comp.get('component_name')
                        validation = rules.validate_extracted_data(equipment_number, comp_name, comp)
                        valid_fields += sum(1 for v in validation.values() if v)
                        
                        for field, is_valid in validation.items():
                            if not is_valid:
                                logger.debug(f"   ⚠️ {comp_name}.{field} may differ from expected")
                    
                    # Calculate confidence (% of fields matching expected)
                    total_fields = len(expected_comps) * 9  # 9 fields per component
                    if total_fields > 0:
                        confidence_score = (valid_fields / total_fields) * 100
                    
                    logger.info(f"✅ Page {page_num + 1} extraction successful (confidence: {confidence_score:.0f}%)")
                    
                    if is_complete:
                        logger.info(f"   All components found, moving to storage...")
                        break  # Stop processing if we have all components
                else:
                    logger.warning(f"⚠️  Page {page_num + 1} incomplete, continuing...")
                
                # Update progress
                extraction.processed_pages = page_num + 1
                db.commit()
            
            except Exception as e:
                logger.warning(f"⚠️  Error processing page {page_num + 1}: {str(e)}")
                continue
        
        if not extracted_data:
            error = "No valid extraction data from any page"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        logger.info(f"Step 3 complete: extracted {len(extracted_data.get('components', []))} components")
        
        # Step 5: Store data
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
            logger.info(f"Step 4 complete: {component_count} components stored")
        except Exception as e:
            error = f"Failed to store data: {str(e)}"
            logger.error(f"❌ {error}")
            extraction.status = ExtractionStatus.FAILED
            extraction.error_message = error
            db.commit()
            return
        
        # Mark as complete
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
# GET EXTRACTION PROGRESS
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