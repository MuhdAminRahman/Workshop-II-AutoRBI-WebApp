import os
import logging
import time
from typing import Dict, List
from dotenv import load_dotenv
from anthropic import Anthropic

from models import Equipment
from .extraction_rules import ExtractionRules
from .test_extraction_rules import TestExtractionRules
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser
from .data_updater import DataUpdater
from .utils import compress_image_for_api, find_equipment_images

logger = logging.getLogger(__name__)

class MasterfileExtractor:
    """Main class for extracting technical data from equipment images"""
    
    def __init__(self,no_expected_value=None, log_callback=None):
        load_dotenv()
        self.log_callback = log_callback
        self.client = Anthropic()
        self.max_retries = 5
        self.base_delay = 1
        
        if no_expected_value is not None:
            self.rules = TestExtractionRules()
        else:
            self.rules = ExtractionRules()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser(self.rules, log_callback=self.log_callback)
        self.data_updater = DataUpdater(self.rules, log_callback=self.log_callback)
        
    
    def extract_technical_data(self, image_path: str, equipment: Equipment) -> Dict[str, List[Dict[str, any]]]:
        """Extract technical data from image"""
        equipment_number = equipment.equipment_number
        
        for attempt in range(self.max_retries):
            try:
                if not os.path.exists(image_path):
                    self.log_error(f"File not found: {image_path}")
                    return {}
                
                image_data = compress_image_for_api(image_path)
                prompt = self._build_prompt(equipment_number, equipment)
                
                message = self.client.messages.create(
                    model="claude-haiku-4-5-20251001", #claude-haiku-4-5-20251001 #claude-sonnet-4-20250514
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                            {"type": "text", "text": prompt}
                        ]
                    }]
                )
                
                return self.response_parser.parse_response(message.content[0].text, equipment.components, equipment_number)
                
            except Exception as e:
                if self._should_retry(e, attempt):
                    continue
                self.log_error(f"Error extracting data from {image_path}: {str(e)}")
                return {}
        
        self.log_error(f"❌ Failed to extract data from {image_path} after {self.max_retries} attempts")
        return {}
    
    def _build_prompt(self, equipment_number: str, equipment: Equipment) -> str:
        """Build the appropriate prompt for the equipment"""
        if equipment_number in self.rules.INSULATION_ONLY_EQUIPMENT:
            insulation_config = self.rules.INSULATION_CONFIGS[equipment_number]
            return self.prompt_builder.build_insulation_only_prompt(equipment_number, equipment, insulation_config)
        
        if equipment_number in self.rules.FIELD_INSTRUCTIONS:
            field_instructions = self.rules.FIELD_INSTRUCTIONS[equipment_number]
            insulation_config = self.rules.INSULATION_CONFIGS[equipment_number]
            skip_operation_pressure_temp = equipment_number in self.rules.SKIP_OPERATING_PRESSURE_TEMPERATURE
            
            return self.prompt_builder.build_full_extraction_prompt(
                equipment_number, equipment, field_instructions, insulation_config, skip_operation_pressure_temp
            )
        
        return f"Extract technical data for {equipment_number} - {equipment.equipment_description}"
    
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if a request should be retried"""
        error_msg = str(error)
        if '529' in error_msg or 'overloaded' in error_msg.lower():
            delay = 0 #self.base_delay #* (2 ** attempt)
            self.log_warning(f"⚠️ API overloaded (attempt {attempt + 1}/{self.max_retries}). Retrying in {delay} seconds...")
            time.sleep(delay)
            return True
        return False
    
    def process_equipment_images(self, equipment_map: Dict[str, Equipment],
                                 only_missing: bool = False, work_path: str = "converted_to_image",
                                 specific_equipment_number_list: List[str] = {},
                                 specific_equipment_number: str = "") -> Dict[str, Dict[str, any]]:
        """
        Process images for equipment
        
        Args:
            equipment_map: Dictionary of equipment
            only_missing: If True, only process equipment that still has missing data
        """
        extracted_data = {}
        
        if specific_equipment_number != "":
            if specific_equipment_number in equipment_map:
                equipment = equipment_map[specific_equipment_number]
                extracted_data.update(self._process_single_equipment(specific_equipment_number, equipment, work_path))
        elif specific_equipment_number_list != {}:
            for equipment_number in specific_equipment_number_list:
                if equipment_number in equipment_map:
                    if only_missing and equipment_number not in self.data_updater.missing_equipment:
                        continue
                    equipment = equipment_map[equipment_number]
                    extracted_data.update(self._process_single_equipment(equipment_number, equipment, work_path))
        else:
            for equipment_number, equipment in equipment_map.items():
                # Skip if only_missing is True and this equipment is not in missing list
                if only_missing and equipment_number not in self.data_updater.missing_equipment:
                    continue
                    
                extracted_data.update(self._process_single_equipment(equipment_number, equipment, work_path))
        return extracted_data
    
    def _process_single_equipment(self, equipment_number: str, equipment: Equipment, work_path: str = "converted_to_image") -> Dict[str, Dict[str, any]]:
        """Process a single equipment"""
        self.log_info(f"🔍 Processing equipment: {equipment_number} - {equipment.pmt_number}")
        
        image_files = find_equipment_images(equipment.pmt_number, work_path)
        if not image_files:
            self.log_warning(f"❌ No images found for {equipment.pmt_number}")
            return {}
        
        for image_file in image_files:
            self.log_info(f"  📄 Analyzing {image_file.name}...")
            technical_data = self.extract_technical_data(str(image_file), equipment)
            
            if technical_data and technical_data.get('components_data'):
                self.log_info(f"  ✅ Successfully extracted data from {image_file.name}")
                return {equipment_number: technical_data}
            else:
                self.log_warning(f"  ⚠️ No data extracted from {image_file.name}")
        
        self.log_error(f"  ❌ Failed to extract data for {equipment_number}")
        return {}
    
    def update_equipment_with_extracted_data(self, equipment_map: Dict[str, Equipment], extracted_data: Dict[str, Dict[str, any]]) -> None:
        """Update equipment with extracted data"""
        self.data_updater.update_equipment(equipment_map, extracted_data)

    def process_and_update_single_equipment(self, equipment_map: Dict[str, Equipment], equipment_number: str, work_path: str = "converted_to_image") -> Dict[str, Equipment]:
        """Process and update a single equipment by its number"""
        self.log_info(f"🚀 Starting data extraction for equipment {equipment_number}...")
        
        retry_count = 0
        while retry_count < self.max_retries:
            if retry_count == 0:
                self.log_info(f"\n📋 Initial extraction (attempt {retry_count + 1})...")
                extracted_data = self.process_equipment_images(equipment_map, only_missing=False, work_path=work_path, specific_equipment_number=equipment_number)
            else:
                self.log_info(f"\n🔄 Retry {retry_count} for equipment {equipment_number}...")
                extracted_data = self.process_equipment_images(equipment_map, only_missing=True, work_path=work_path, specific_equipment_number=equipment_number)
            # Update equipment with extracted data
            self.update_equipment_with_extracted_data(equipment_map, extracted_data)
            # Check if we're done
            if equipment_number not in self.data_updater.missing_equipment:
                self.log_info(f"✅ Equipment {equipment_number} has complete data after {retry_count + 1} attempt(s)")
                break
            retry_count += 1
        
        if self.data_updater.missing_equipment:
            self.log_warning(f"⚠️ {len(self.data_updater.missing_equipment)} equipment still missing data after {retry_count} retries:")
            for eq_num in self.data_updater.missing_equipment:
                self.log_warning(f"  - {eq_num}")
        
        return equipment_map
    
    def process_and_update_specific_equipment(self, equipment_map: Dict[str, Equipment], equipment_numbers: List[str], work_path: str = "converted_to_image") -> Dict[str, Equipment]:
        """Process and update specific equipment by their numbers"""
        self.log_info("🚀 Starting specific equipment data extraction...")
        
        retry_count = 0
        while retry_count < self.max_retries:
            if retry_count == 0:
                self.log_info(f"\n📋 Initial extraction (attempt {retry_count + 1})...")
                extracted_data = self.process_equipment_images(equipment_map, only_missing=False, work_path=work_path, specific_equipment_number_list=equipment_numbers)
            else:
                self.log_info(f"\n🔄 Retry {retry_count} for equipment {equipment_numbers}...")
                extracted_data = self.process_equipment_images(equipment_map, only_missing=True, work_path=work_path, specific_equipment_number_list=equipment_numbers)
            # Update equipment with extracted data
            self.update_equipment_with_extracted_data(equipment_map, extracted_data)
            # Check if we're done
            if not self.data_updater.missing_equipment:
                self.log_info(f"✅ All equipment have complete data after {retry_count + 1} attempt(s)")
                break
            retry_count += 1
        
        if self.data_updater.missing_equipment:
            self.log_warning(f"⚠️ {len(self.data_updater.missing_equipment)} equipment still missing data after {retry_count} retries:")
            for eq_num in self.data_updater.missing_equipment:
                self.log_warning(f"  - {eq_num}")

        
        return equipment_map

    def process_and_update_equipment(self, equipment_map: Dict[str, Equipment]) -> Dict[str, Equipment]:
        """Complete pipeline: extract data and update equipment with retries"""
        self.log_info("🚀 Starting equipment data extraction pipeline...")
        
        retry_count = 0
        
        while retry_count < self.max_retries:
            if retry_count == 0:
                self.log_info(f"\n📋 Initial extraction (attempt {retry_count + 1})...")
                # First pass: process all equipment
                extracted_data = self.process_equipment_images(equipment_map, only_missing=False)
            else:
                self.log_info(f"\n🔄 Retry {retry_count} for {len(self.data_updater.missing_equipment)} equipment...")
                # Subsequent passes: only process missing equipment
                extracted_data = self.process_equipment_images(equipment_map, only_missing=True)
            
            # Update equipment with extracted data
            self.update_equipment_with_extracted_data(equipment_map, extracted_data)
            
            # Check if we're done
            if not self.data_updater.missing_equipment:
                self.log_info(f"✅ All equipment have complete data after {retry_count + 1} attempt(s)")
                break
            
            retry_count += 1
        
        # Report final status
        if self.data_updater.missing_equipment:
            self.log_warning(f"⚠️ {len(self.data_updater.missing_equipment)} equipment still missing data after {retry_count} retries:")
            for eq_num in self.data_updater.missing_equipment:
                self.log_warning(f"  - {eq_num}")
        
        return equipment_map
    
    def log_info(self, message: str) -> None:
        """Log info message to both console and UI"""
        logger.info(message)
        if self.log_callback:
            self.log_callback(f"ℹ️ {message}")

    def log_warning(self, message: str) -> None:
        """Log warning message to both console and UI"""
        logger.warning(message)
        if self.log_callback:
            self.log_callback(f"⚠️ {message}")

    def log_error(self, message: str) -> None:
        """Log error message to both console and UI"""
        logger.error(message)
        if self.log_callback:
            self.log_callback(f"❌ {message}")