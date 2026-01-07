from typing import Dict, List, Callable
from concurrent.futures import as_completed
from models import Equipment

class ExtractionManager:
    """Manages the extraction process with progress tracking"""
    
    def __init__(
        self, 
        equipment_service,
        file_service,
        thread_executor,
        ui_updater,
        log_callback: Callable[[str], None]
    ):
        self.equipment_service = equipment_service
        self.file_service = file_service
        self.executor = thread_executor
        self.ui_updater = ui_updater
        self.log_callback = log_callback
    
    def run_extraction(
        self,
        equipment_numbers: List[str],
        images_dir: str
    ) -> Dict[str, Equipment]:
        """Run extraction for multiple equipment items"""
        
        # Initialize
        self.ui_updater.queue_update('progress', {'value': 0.0, 'text': 'Initializing...'})
        equipment_map = self.equipment_service.initialize_extraction()
        
        # Process files
        total = len(equipment_numbers)
        completed = 0
        results = {}
        
        # Submit all extraction tasks
        futures = {}
        for idx, eq_no in enumerate(equipment_numbers):
            future = self.executor.submit(
                self._extract_with_progress,
                equipment_map,
                eq_no,
                images_dir,
                idx,
                total
            )
            futures[future] = eq_no
        
        # Collect results as they complete
        for future in as_completed(futures):
            eq_no = futures[future]
            try:
                result = future.result()
                if result:
                    results[eq_no] = result
                    equipment_map[eq_no] = result  # Update main map
                
                completed += 1
                progress = completed / total
                self.ui_updater.queue_update('progress', {
                    'value': progress,
                    'text': f'Completed {completed}/{total}'
                })
            
            except Exception as e:
                self.log_callback(f"❌ Error processing {eq_no}: {e}")
        
        # Finalize
        self.ui_updater.queue_update('progress', {
            'value': 1.0,
            'text': 'Extraction complete!'
        })
        self.log_callback("✅ All files extracted successfully.")
        
        return equipment_map
    
    def _extract_with_progress(
        self,
        equipment_map: Dict[str, Equipment],
        equipment_number: str,
        images_dir: str,
        index: int,
        total: int
    ) -> Equipment:
        """Extract single equipment with progress updates"""
        
        progress = (index + 1) / total
        status = f"Processing {index + 1}/{total}: {equipment_number}"
        
        self.ui_updater.queue_update('progress', {
            'value': progress,
            'text': status
        })
        
        return self.equipment_service.extract_single_equipment(
            equipment_map,
            equipment_number,
            images_dir
        )