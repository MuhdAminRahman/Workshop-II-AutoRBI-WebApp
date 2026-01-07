import customtkinter as ctk
from typing import Callable, List
from .constants import Fonts, Colors, Sizes, Messages, TableColumns

class PageBuilderBase:
    """Base class for page builders"""
    
    def __init__(self, parent: ctk.CTk, view):
        self.parent = parent
        self.view = view
        self.main_frame = None
    
    def _create_root_frame(self) -> ctk.CTkFrame:
        """Create the root frame for a page"""
        root_frame = ctk.CTkFrame(
            self.parent, 
            corner_radius=0, 
            fg_color=Colors.TRANSPARENT
        )
        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)
        return root_frame
    
    def _build_header(
        self, 
        parent: ctk.CTkFrame,
        back_text: str,
        back_command: Callable
    ) -> ctk.CTkFrame:
        """Build header with back button and title"""
        header = ctk.CTkFrame(parent, fg_color=Colors.TRANSPARENT)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        
        back_btn = ctk.CTkButton(
            header,
            text=back_text,
            command=back_command,
            width=180,
            height=Sizes.BUTTON_HEIGHT_SM,
            font=Fonts.SUBTITLE,
            fg_color=Colors.TRANSPARENT,
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        back_btn.grid(row=0, column=0, sticky="w")
        
        title_label = ctk.CTkLabel(
            header,
            text="AutoRBI",
            font=Fonts.TITLE,
        )
        title_label.grid(row=0, column=1, sticky="e")
        
        return header
    
    def _create_scroll_container(self, parent: ctk.CTkFrame) -> ctk.CTkScrollableFrame:
        """Create scrollable container"""
        scroll = ctk.CTkScrollableFrame(
            parent,
            corner_radius=Sizes.CORNER_RADIUS,
            border_width=1,
            border_color=Colors.BORDER,
        )
        scroll.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        return scroll
    
    def _create_section_frame(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        """Create a standard section frame"""
        section = ctk.CTkFrame(
            parent,
            fg_color=Colors.SECTION_BG,
            corner_radius=Sizes.CORNER_RADIUS_SM
        )
        return section


class Page1Builder(PageBuilderBase):
    """Builds Page 1 - Upload & Extract"""
    def backToMainMenuButtonEvent(self):
        self.view.setInitialized(False)
        self.view.controller.show_main_menu()

    def build(self) -> ctk.CTkFrame:
        """Build the complete Page 1"""
        root_frame = self._create_root_frame()
        root_frame.pack(expand=True, fill="both", padx=Sizes.PADDING_OUTER, pady=24)
        
        # Header
        self._build_header(
            root_frame,
            "← Back to Main Menu",
            self.backToMainMenuButtonEvent        
            )
        
        # Scrollable content
        scroll = self._create_scroll_container(root_frame)
        scroll.grid_rowconfigure(4, weight=1)
        scroll.grid_columnconfigure(0, weight=1)
        
        # Page title
        self._build_page_title(scroll)
        
        # Sections
        self._build_work_selection(scroll, row=2)
        self._build_file_upload(scroll, row=3)
        self._build_extraction_section(scroll, row=4)
        self._build_action_buttons(scroll, row=5)
        
        return root_frame
    
    def _build_page_title(self, parent: ctk.CTkFrame):
        """Build page title and subtitle"""
        title = ctk.CTkLabel(
            parent,
            text="New Work - Step 1: Upload & Extract",
            font=Fonts.SECTION_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=Sizes.PADDING_SECTION, pady=(18, 6))
        
        subtitle = ctk.CTkLabel(
            parent,
            text="Select work, upload Excel masterfile, and GA drawings for extraction.",
            font=Fonts.SUBTITLE,
            text_color=("gray25", "gray80"),
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=Sizes.PADDING_SECTION, pady=(0, 18))
    
    def _build_work_selection(self, parent: ctk.CTkFrame, row: int):
        """Build work selection section"""
        section = self._create_section_frame(parent)
        section.grid(row=row, column=0, sticky="ew", padx=Sizes.PADDING_SECTION, pady=(0, 16))
        section.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(
            section,
            text="Work Assignment:",
            font=Fonts.SECTION_LABEL,
        )
        label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))
        
        # Get work names
        work_names = [
            w.get("work_name", w.get("work_id", "Unknown")) 
            for w in self.view.controller.available_works
        ]
        
        # Find current work index
        current_index = 0
        if self.view.controller.current_work:
            current_id = self.view.controller.current_work.get("work_id")
            for idx, work in enumerate(self.view.controller.available_works):
                if work.get("work_id") == current_id:
                    current_index = idx
                    break
        
        self.view.work_combobox = ctk.CTkComboBox(
            section,
            values=work_names,
            state="readonly",
            font=Fonts.SUBTITLE,
            height=Sizes.BUTTON_HEIGHT_SM,
            command=self.view._on_work_selected,
        )
        self.view.work_combobox.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=(12, 6))
        
        if work_names:
            self.view.work_combobox.set(work_names[current_index])
    
    def _build_file_upload(self, parent: ctk.CTkFrame, row: int):
        """Build file upload section"""
        section = self._create_section_frame(parent)
        section.grid(row=row, column=0, sticky="ew", padx=Sizes.PADDING_SECTION, pady=(0, 16))
        section.grid_columnconfigure(0, weight=1)
        
        # Section label
        label = ctk.CTkLabel(
            section,
            text="Files:",
            font=Fonts.SECTION_LABEL,
        )
        label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 12))
        
        # File display
        display_frame = ctk.CTkFrame(section, fg_color=Colors.TRANSPARENT)
        display_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        display_frame.grid_columnconfigure(0, weight=1)
        
        # File listbox
        self.view.file_listbox = ctk.CTkTextbox(
            display_frame,
            height=80,
            font=Fonts.SMALL,
            fg_color=Colors.WHITE_BLACK,
        )
        self.view.file_listbox.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.view.file_listbox.configure(state="disabled")
        
        # Buttons
        self._build_file_buttons(display_frame)
    
    def _build_file_buttons(self, parent: ctk.CTkFrame):
        """Build file operation buttons"""
        button_row = ctk.CTkFrame(parent, fg_color=Colors.TRANSPARENT)
        button_row.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        # Check if Excel exists
        workpath = self.view.controller.current_work.get("work_name") if self.view.controller.current_work else None
        excel_exists = self.view.file_service.get_work_excel_path(
            workpath, 
            self.view.project_root
        ) is not None if workpath else False
        
        # Upload Excel button (only if no Excel exists)
        if not excel_exists:
            excel_btn = ctk.CTkButton(
                button_row,
                text="📋 Upload Excel",
                command=lambda: self.view.upload_default_excel(),
                height=Sizes.BUTTON_HEIGHT_SM,
                width=120,
                font=Fonts.SUBTITLE,
            )
            excel_btn.pack(side="left", padx=(0, 8))
        
        # Browse GA Files
        ga_btn = ctk.CTkButton(
            button_row,
            text="📁 Browse GA Files (PDF)",
            command=lambda: self.view.select_files(self.view.file_mode.get().lower()),
            height=Sizes.BUTTON_HEIGHT_SM,
            width=150,
            font=Fonts.SUBTITLE,
        )
        ga_btn.pack(side="left", padx=(0, 8))
        
        # Mode selector
        mode_label = ctk.CTkLabel(
            button_row,
            text="Mode:",
            font=Fonts.SMALL,
            text_color=("gray50", "gray70"),
        )
        mode_label.pack(side="left", padx=(0, 6))
        
        self.view.file_mode = ctk.StringVar(value="single")
        mode_switch = ctk.CTkSegmentedButton(
            button_row,
            values=["Single", "Multiple", "Folder"],
            variable=self.view.file_mode,
            font=Fonts.SMALL,
            height=Sizes.BUTTON_HEIGHT_XS,
        )
        mode_switch.pack(side="left", padx=(0, 8))
        
        # Clear button
        clear_btn = ctk.CTkButton(
            button_row,
            text="Clear All",
            command=self.view.clear_files,
            height=Sizes.BUTTON_HEIGHT_SM,
            width=80,
            font=Fonts.SUBTITLE,
            fg_color=Colors.TRANSPARENT,
            hover_color=("gray85", "gray30"),
            border_width=1,
            border_color=("gray70", "gray50"),
        )
        clear_btn.pack(side="left")
    
    def _build_extraction_section(self, parent: ctk.CTkFrame, row: int):
        """Build extraction progress section"""
        section = self._create_section_frame(parent)
        section.grid(row=row, column=0, sticky="nsew", padx=Sizes.PADDING_SECTION, pady=(0, 16))
        section.grid_rowconfigure(2, weight=1)
        section.grid_columnconfigure(0, weight=1)
        
        # Progress label
        label = ctk.CTkLabel(
            section,
            text="Extraction Progress:",
            font=Fonts.SECTION_LABEL,
        )
        label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        
        # Progress bar
        self.view.progress_bar = ctk.CTkProgressBar(section, height=12)
        self.view.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self.view.progress_bar.set(0.0)
        
        self.view.progress_label = ctk.CTkLabel(
            section,
            text="Ready to extract.",
            font=Fonts.SMALL,
            text_color=("gray70", "gray80"),
        )
        self.view.progress_label.grid(row=1, column=0, sticky="e", padx=16, pady=(0, 4))
        
        # Log title
        log_title = ctk.CTkLabel(
            section,
            text="Log:",
            font=Fonts.SUBTITLE,
        )
        log_title.grid(row=2, column=0, sticky="w", padx=16, pady=(8, 4))
        
        # Log textbox
        self.view.extraction_log_textbox = ctk.CTkTextbox(
            section,
            height=120,
            font=Fonts.TINY,
            fg_color=Colors.WHITE_BLACK,
        )
        self.view.extraction_log_textbox.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.view.extraction_log_textbox.configure(state="disabled")
        
        # Extract button
        extract_btn = ctk.CTkButton(
            section,
            text="▶ Start Extraction",
            command=self.view.start_extraction,
            height=Sizes.BUTTON_HEIGHT,
            font=Fonts.BUTTON_BOLD,
        )
        extract_btn.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 12))
    
    def _build_action_buttons(self, parent: ctk.CTkFrame, row: int):
        """Build bottom action buttons"""
        action_section = ctk.CTkFrame(parent, fg_color=Colors.TRANSPARENT)
        action_section.grid(row=row, column=0, sticky="ew", padx=Sizes.PADDING_SECTION, pady=(12, 24))
        
        self.view.next_button = ctk.CTkButton(
            action_section,
            text="➜ Next: Review Extracted Data",
            command=self.view.show_page_2,
            height=Sizes.BUTTON_HEIGHT,
            font=Fonts.BUTTON_BOLD,
            fg_color=Colors.PRIMARY,
            state="disabled",
        )
        self.view.next_button.pack(side="right")


class Page2Builder(PageBuilderBase):
    """Builds Page 2 - Review & Save"""
    
    def build(self) -> ctk.CTkFrame:
        """Build the complete Page 2"""
        root_frame = self._create_root_frame()
        root_frame.pack(expand=True, fill="both", padx=Sizes.PADDING_OUTER, pady=24)
        
        # Header
        self._build_header(
            root_frame,
            "← Back to Step 1",
            self.view.show_page_1
        )
        
        # Scrollable content
        scroll = self._create_scroll_container(root_frame)
        scroll.grid_rowconfigure(2, weight=1)
        scroll.grid_columnconfigure(0, weight=1)
        
        # Page title
        self._build_page_title(scroll)
        
        # Data section
        self._build_data_section(scroll, row=2)
        
        # Action buttons
        self._build_action_buttons(scroll, row=3)
        
        return root_frame
    
    def _build_page_title(self, parent: ctk.CTkFrame):
        """Build page title"""
        title = ctk.CTkLabel(
            parent,
            text="New Work - Step 2: Review & Save",
            font=Fonts.SECTION_TITLE,
        )
        title.grid(row=0, column=0, sticky="w", padx=Sizes.PADDING_SECTION, pady=(18, 6))
        
        subtitle = ctk.CTkLabel(
            parent,
            text="Review extracted data, edit if needed, then save to Excel and database.",
            font=Fonts.SUBTITLE,
            text_color=("gray25", "gray80"),
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=Sizes.PADDING_SECTION, pady=(0, 18))
    
    def _build_data_section(self, parent: ctk.CTkFrame, row: int):
        """Build data review section"""
        data_section = ctk.CTkFrame(parent, fg_color=Colors.TRANSPARENT)
        data_section.grid(row=row, column=0, sticky="nsew", padx=Sizes.PADDING_SECTION, pady=(0, 24))
        data_section.grid_rowconfigure(2, weight=1)
        data_section.grid_columnconfigure(0, weight=1)
        
        label = ctk.CTkLabel(
            data_section,
            text="Extracted Data (Editable):",
            font=Fonts.SECTION_LABEL,
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        helper = ctk.CTkLabel(
            data_section,
            text="Review and edit extracted values below. They will be saved to Excel and the database.",
            font=Fonts.SUBTITLE,
            text_color=("gray50", "gray70"),
        )
        helper.grid(row=1, column=0, sticky="w", pady=(0, 12))
        
        # Container for editable data tables
        self.view.files_edit_container = ctk.CTkFrame(
            data_section,
            fg_color=Colors.TRANSPARENT,
        )
        self.view.files_edit_container.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        self.view.files_edit_container.grid_columnconfigure(0, weight=1)
        self.view.files_edit_container.grid_rowconfigure(0, weight=1)
        
        # Initialize with "No data" message
        no_data_label = ctk.CTkLabel(
            self.view.files_edit_container,
            text="No data available. Please go back to Step 1 and extract data first.",
            font=Fonts.SUBTITLE,
            text_color=("gray50", "gray70"),
        )
        no_data_label.pack(pady=40)
    
    def _build_action_buttons(self, parent: ctk.CTkFrame, row: int):
        """Build action buttons"""
        action_section = ctk.CTkFrame(parent, fg_color=Colors.TRANSPARENT)
        action_section.grid(row=row, column=0, sticky="ew", padx=Sizes.PADDING_SECTION, pady=(12, 24))
        
        # Save button
        save_btn = ctk.CTkButton(
            action_section,
            text="Save & Update Excel",
            command=self.view.save_to_excel,
            height=Sizes.BUTTON_HEIGHT,
            font=Fonts.BUTTON_BOLD,
            fg_color=Colors.PRIMARY,
        )
        save_btn.pack(side="right", padx=(8, 0))
        
        # Back button
        back_btn = ctk.CTkButton(
            action_section,
            text="← Back to Extraction",
            command=self.view.show_page_1,
            height=Sizes.BUTTON_HEIGHT,
            font=Fonts.BUTTON,
        )
        back_btn.pack(side="right")
        
        # PowerPoint button (if data available)
        if self.view.state.has_equipment_data:
            ppt_btn = ctk.CTkButton(
                action_section,
                text="📊 Export to PowerPoint",
                command=self.view.export_to_powerpoint,
                height=Sizes.BUTTON_HEIGHT,
                font=Fonts.BUTTON,
                fg_color=("#0066CC", "#004C99"),
                hover_color=("#0052A3", "#003366")
            )
            ppt_btn.pack(side="right", padx=(8, 0))