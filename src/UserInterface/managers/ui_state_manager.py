from dataclasses import dataclass
from enum import Enum

from UserInterface.services.excel_validator import ExcelFileInfo, ExcelFileType


class UIState(Enum):
    """UI states for the NewWork flow"""
    NO_PERMISSION = "no_permission"
    NO_EXCEL = "no_excel"
    READY_FOR_UPLOAD = "ready_for_upload"
    FILES_UPLOADED = "files_uploaded"
    EXTRACTING = "extracting"
    EXTRACTION_COMPLETE = "extraction_complete"
    REVIEWING = "reviewing"
    VALIDATED = "validated"


@dataclass
class UIStateConfig:
    """Configuration for UI element states"""
    # Page 1
    work_selector_enabled: bool = True
    excel_upload_visible: bool = False
    file_browse_enabled: bool = False
    file_clear_enabled: bool = False
    start_extraction_enabled: bool = False
    next_button_enabled: bool = False
    
    # Page 2
    save_excel_enabled: bool = False
    export_powerpoint_enabled: bool = False
    
    # Messages
    info_message: str = ""
    show_blocking_message: bool = False


class UIStateController:
    """Controls UI element states based on business logic"""
    
    def __init__(self):
        self.current_state = UIState.NO_PERMISSION
    
    def compute_ui_state(
        self,
        has_permission: bool,
        excel_file_info: ExcelFileInfo,
        has_files_selected: bool,
        extraction_complete: bool,
        data_validated: bool,
        is_extracting: bool
    ) -> UIStateConfig:
        """
        Compute UI state configuration based on current conditions.
        
        This is the central logic that determines what the user can do.
        """
        config = UIStateConfig()
        
        # Step 1: Check permissions
        if not has_permission:
            self.current_state = UIState.NO_PERMISSION
            config.work_selector_enabled = False
            config.excel_upload_visible = False
            config.file_browse_enabled = False
            config.start_extraction_enabled = False
            config.info_message = "⚠️ You do not have any work assigned. Please contact your administrator."
            config.show_blocking_message = True
            return config
        
        # Step 2: Check Excel file
        if excel_file_info.file_type == ExcelFileType.NOT_FOUND:
            self.current_state = UIState.NO_EXCEL
            config.work_selector_enabled = True
            config.excel_upload_visible = True
            config.file_browse_enabled = False
            config.start_extraction_enabled = False
            config.info_message = "📋 Please upload the default Excel masterfile to begin."
            return config
        
        # Step 3: Excel exists - ready for file upload
        if not has_files_selected and not extraction_complete:
            self.current_state = UIState.READY_FOR_UPLOAD
            config.work_selector_enabled = True
            config.excel_upload_visible = False
            config.file_browse_enabled = True
            config.file_clear_enabled = False
            config.start_extraction_enabled = False
            config.info_message = "📁 Select GA Drawing PDF files to extract."
            return config
        
        # Step 4: Files selected but not extracting yet
        if has_files_selected and not is_extracting and not extraction_complete:
            self.current_state = UIState.FILES_UPLOADED
            config.work_selector_enabled = True
            config.excel_upload_visible = False
            config.file_browse_enabled = True
            config.file_clear_enabled = True
            config.start_extraction_enabled = True
            config.info_message = "✅ Ready to extract. Click 'Start Extraction' to begin."
            return config
        
        # Step 5: Currently extracting
        if is_extracting:
            self.current_state = UIState.EXTRACTING
            config.work_selector_enabled = False
            config.excel_upload_visible = False
            config.file_browse_enabled = False
            config.file_clear_enabled = False
            config.start_extraction_enabled = False
            config.info_message = "⏳ Extraction in progress..."
            return config
        
        # Step 6: Extraction complete - ready to review
        if extraction_complete and not data_validated:
            self.current_state = UIState.EXTRACTION_COMPLETE
            config.work_selector_enabled = False
            config.excel_upload_visible = False
            config.file_browse_enabled = False  # Cannot upload more files
            config.file_clear_enabled = False
            config.start_extraction_enabled = False
            config.next_button_enabled = True
            config.info_message = "✅ Extraction complete! Proceed to review the data."
            return config
        
        # Step 7: On review page - data not validated
        if extraction_complete and not data_validated:
            self.current_state = UIState.REVIEWING
            config.save_excel_enabled = False
            config.export_powerpoint_enabled = False
            config.info_message = "⚠️ Please fill all required fields before saving."
            return config
        
        # Step 8: Data validated - ready to save
        if extraction_complete and data_validated:
            self.current_state = UIState.VALIDATED
            config.save_excel_enabled = True
            config.export_powerpoint_enabled = True
            config.info_message = "✅ Data validated! You can now save to Excel or export to PowerPoint."
            return config
        
        # Default state
        return config