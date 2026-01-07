"""Work History view for AutoRBI application (CustomTkinter)."""

from typing import List, Dict, Any, Optional
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timezone


class WorkHistoryView:
    """Handles the Work History Menu interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.history_rows: List[Dict[str, Any]] = []
        self.table_body: Optional[ctk.CTkScrollableFrame] = None
        self.current_filter: str = "all"

        # Pagination state
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 1
        self.total_items = 0

        # Pagination widgets (to update states)
        self.prev_button: Optional[ctk.CTkButton] = None
        self.next_button: Optional[ctk.CTkButton] = None
        self.page_info_label: Optional[ctk.CTkLabel] = None

        # Filter buttons (to update states)
        self.filter_buttons: Dict[str, ctk.CTkButton] = {}

    def load_history(
        self, history_items: List[Dict[str, Any]], total: int = 0, total_pages: int = 1
    ) -> None:
        """
        Populate the work history table.

        Args:
            history_items: List of history entry dictionaries
            total: Total number of items (for pagination)
            total_pages: Total number of pages
        """
        self.history_rows = history_items
        self.total_items = total
        self.total_pages = total_pages

        if self.table_body is not None:
            # Clear current rows
            for child in self.table_body.winfo_children():
                child.destroy()

            # Rebuild table
            if history_items:
                for idx, item in enumerate(history_items, start=1):
                    self._add_history_row(idx, item)
            else:
                # Show hint if no data
                hint_label = ctk.CTkLabel(
                    self.table_body,
                    text="No work history found for the selected filter.",
                    font=("Segoe UI", 11),
                    text_color=("gray40", "gray75"),
                    justify="left",
                )
                hint_label.grid(row=0, column=0, columnspan=6, sticky="w", pady=(8, 8))

        # Update pagination display
        self._update_pagination_display()

    def _format_timestamp(self, utc_timestamp_str: str) -> str:
        """Convert UTC timestamp to local time for display."""
        try:
            # Parse the UTC timestamp
            if isinstance(utc_timestamp_str, str):
                utc_dt = datetime.fromisoformat(
                    utc_timestamp_str.replace("Z", "+00:00")
                )
            else:
                utc_dt = utc_timestamp_str

            # Convert to local time
            local_dt = utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

            # Format for display
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(utc_timestamp_str)

    def _update_pagination_display(self) -> None:
        """Update pagination button states and page info label"""

        if self.prev_button:
            if self.current_page <= 1:
                self.prev_button.configure(state="disabled")
            else:
                self.prev_button.configure(state="normal")

        if self.next_button:
            if self.current_page >= self.total_pages:
                self.next_button.configure(state="disabled")
            else:
                self.next_button.configure(state="normal")

        if self.page_info_label:
            self.page_info_label.configure(
                text=f"Page {self.current_page} of {self.total_pages} ({self.total_items} total items)"
            )

    def _apply_filter(self, period: str) -> None:
        """Apply time period filter and update button states."""
        self.current_filter = period
        self.current_page = 1  # Reset to first page when filter changes

        # Update filter button states immediately
        self._update_filter_buttons()

        # Apply the filter
        self.controller.apply_work_history_filter(period)

    def _update_filter_buttons(self) -> None:
        """Update the visual state of filter buttons based on current filter."""
        if hasattr(self, "filter_buttons"):
            for period_key, btn in self.filter_buttons.items():
                if period_key == self.current_filter:
                    # Selected button - use default theme color
                    btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                else:
                    # Unselected button - use gray
                    btn.configure(fg_color=("gray20", "gray30"))

    def _delete_work(self, item: Dict[str, Any]) -> None:
        """Delete a work history log entry (Admin only)."""
        history_id = item.get("id")
        if history_id:
            self.controller.delete_work_history(history_id)

    def _previous_page(self) -> None:
        """Navigate to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.controller.change_history_page(self.current_page)

    def _next_page(self) -> None:
        """Navigate to next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.controller.change_history_page(self.current_page)

    def _add_history_row(self, index: int, item: Dict[str, Any]) -> None:
        """Add a row to the history table with fixed column widths."""
        if self.table_body is None:
            return

        # Get current user role from controller
        user_role = self.controller.current_user.get("role", "Engineer")
        is_admin = user_role == "Admin"

        # Extract data with defaults
        history_id = item.get("id", "N/A")
        action_type = item.get("action_type", "Unknown")
        description = item.get("description", "-")
        timestamp = item.get("timestamp", "-")
        work_id = item.get("work_id", "-")
        equipment_name = item.get("equipment_name", "-")  # NEW: Equipment column

        # Table row frame - FIXED HEIGHT
        row_frame = ctk.CTkFrame(
            self.table_body,
            corner_radius=4,
            border_width=1,
            border_color=("gray80", "gray30"),
            height=60,  # Fixed height for all rows
        )
        row_frame.grid(row=index, column=0, columnspan=7, sticky="ew", pady=2)
        row_frame.pack_propagate(False)  # Prevent frame from resizing based on content

        # Configure columns with FIXED widths
        row_frame.grid_columnconfigure(0, weight=0, minsize=60)  # No.
        row_frame.grid_columnconfigure(1, weight=0, minsize=90)  # Work ID
        row_frame.grid_columnconfigure(2, weight=0, minsize=120)  # Equipment (NEW)
        row_frame.grid_columnconfigure(3, weight=0, minsize=140)  # Action Type
        row_frame.grid_columnconfigure(4, weight=1, minsize=200)  # Description
        row_frame.grid_columnconfigure(5, weight=0, minsize=150)  # Timestamp
        row_frame.grid_columnconfigure(
            6, weight=0, minsize=100
        )  # Actions (Delete only)

        # Column 0: No.
        no_label = ctk.CTkLabel(
            row_frame,
            text=str((self.current_page - 1) * self.per_page + index),
            font=("Segoe UI", 11),
            anchor="center",
        )
        no_label.grid(row=0, column=0, sticky="nsew", padx=8, pady=12)

        # Column 1: Work ID
        work_id_label = ctk.CTkLabel(
            row_frame,
            text=str(work_id),
            font=("Segoe UI", 10),
            text_color=("gray60", "gray80"),
            anchor="center",
        )
        work_id_label.grid(row=0, column=1, sticky="nsew", padx=8, pady=12)

        # Column 2: Equipment (NEW)
        equipment_label = ctk.CTkLabel(
            row_frame,
            text=str(equipment_name),
            font=("Segoe UI", 11, "bold"),
            anchor="center",
        )
        equipment_label.grid(row=0, column=2, sticky="nsew", padx=8, pady=12)

        # Column 3: Action Type
        action_label = ctk.CTkLabel(
            row_frame,
            text=action_type,
            font=("Segoe UI", 10),
            anchor="w",
        )
        action_label.grid(row=0, column=3, sticky="nsew", padx=8, pady=12)

        # Column 4: Description - truncate long text
        # Truncate description to fit in fixed width
        max_desc_length = 40
        truncated_desc = (
            description[:max_desc_length] + "..."
            if len(description) > max_desc_length
            else description
        )

        desc_label = ctk.CTkLabel(
            row_frame,
            text=truncated_desc,
            font=("Segoe UI", 10),
            text_color=("gray60", "gray80"),
            anchor="w",
        )
        desc_label.grid(row=0, column=4, sticky="nsew", padx=8, pady=12)

        # Column 5: Timestamp
        timestamp_display = self._format_timestamp(timestamp)
        time_label = ctk.CTkLabel(
            row_frame,
            text=timestamp_display,
            font=("Segoe UI", 10),
            text_color=("gray60", "gray80"),
            anchor="center",
        )
        time_label.grid(row=0, column=5, sticky="nsew", padx=8, pady=12)

        # Column 6: Actions (Delete button - ADMIN ONLY)
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=6, sticky="nsew", padx=8, pady=12)

        if is_admin:
            # Show delete button only for Admin
            delete_btn = ctk.CTkButton(
                actions_frame,
                text="Delete",
                width=80,
                height=32,
                font=("Segoe UI", 10),
                fg_color=("#e74c3c", "#c0392b"),
                hover_color=("#c0392b", "#a93226"),
                command=lambda i=item: self._delete_work(i),
            )
            delete_btn.pack(expand=True)
        else:
            # Show disabled state or empty for Engineers
            no_action_label = ctk.CTkLabel(
                actions_frame,
                text="-",
                font=("Segoe UI", 10),
                text_color=("gray60", "gray80"),
            )
            no_action_label.pack(expand=True)

    def show(self) -> None:
        """Display the Work History Menu interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with back button
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back to Main Menu",
            command=self.controller.show_main_menu,
            width=180,
            height=32,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        back_btn.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            header,
            text="AutoRBI",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.grid(row=0, column=1, sticky="e")

        # Main content area
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="Work History (Logs)",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="View system logs of all actions performed. Admin can delete logs.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # Filter buttons (no input fields)
        filter_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        filter_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))

        filter_label = ctk.CTkLabel(
            filter_section,
            text="Time period:",
            font=("Segoe UI", 10, "bold"),
        )
        filter_label.pack(side="left", padx=(0, 8))

        # Store filter buttons for later updates
        self.filter_buttons = {}

        filter_buttons_config = [
            ("All", "all"),
            ("Today", "today"),
            ("Last 7 days", "last_7_days"),
            ("Last month", "last_month"),
        ]

        for label, period_key in filter_buttons_config:
            is_selected = self.current_filter == period_key
            btn = ctk.CTkButton(
                filter_section,
                text=label,
                width=100,
                height=28,
                font=("Segoe UI", 9),
                fg_color=(
                    ["#3B8ED0", "#1F6AA5"] if is_selected else ("gray20", "gray30")
                ),
                command=lambda p=period_key: self._apply_filter(p),
            )
            btn.pack(side="left", padx=(0, 6))
            self.filter_buttons[period_key] = btn

        # Table container
        table_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_container.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 12))
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Table header with FIXED widths
        header_row = ctk.CTkFrame(
            table_container,
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("gray90", "gray20"),
            height=50,
        )
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        header_row.pack_propagate(False)

        # Configure header columns with FIXED widths (same as row columns)
        header_row.grid_columnconfigure(0, weight=0, minsize=60)  # No.
        header_row.grid_columnconfigure(1, weight=0, minsize=90)  # Work ID
        header_row.grid_columnconfigure(2, weight=0, minsize=120)  # Equipment (NEW)
        header_row.grid_columnconfigure(3, weight=0, minsize=140)  # Action Type
        header_row.grid_columnconfigure(4, weight=1, minsize=200)  # Description
        header_row.grid_columnconfigure(5, weight=0, minsize=150)  # Timestamp
        header_row.grid_columnconfigure(6, weight=0, minsize=100)  # Actions

        headers = [
            "No.",
            "Work ID",
            "Equipment",
            "Action Type",
            "Description",
            "Timestamp",
            "Actions",
        ]
        for col, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_row,
                text=header_text,
                font=("Segoe UI", 11, "bold"),
                anchor="center" if col in [0, 1, 2, 5, 6] else "w",
            )
            header_label.grid(row=0, column=col, sticky="nsew", padx=8, pady=10)

        # Scrollable history table body
        self.table_body = ctk.CTkScrollableFrame(
            table_container, fg_color="transparent"
        )
        self.table_body.grid(row=1, column=0, sticky="nsew")

        # Configure table body columns with FIXED widths (same as header)
        self.table_body.grid_columnconfigure(0, weight=0, minsize=60)  # No.
        self.table_body.grid_columnconfigure(1, weight=0, minsize=90)  # Work ID
        self.table_body.grid_columnconfigure(
            2, weight=0, minsize=120
        )  # Equipment (NEW)
        self.table_body.grid_columnconfigure(3, weight=0, minsize=140)  # Action Type
        self.table_body.grid_columnconfigure(4, weight=1, minsize=200)  # Description
        self.table_body.grid_columnconfigure(5, weight=0, minsize=150)  # Timestamp
        self.table_body.grid_columnconfigure(6, weight=0, minsize=100)  # Actions

        # Initially show hint
        hint_label = ctk.CTkLabel(
            self.table_body,
            text="Loading work history...",
            font=("Segoe UI", 11),
            text_color=("gray40", "gray75"),
            justify="left",
        )
        hint_label.grid(row=0, column=0, columnspan=7, sticky="w", pady=(8, 8))

        # Pagination controls
        pagination_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        pagination_frame.grid(row=4, column=0, sticky="ew", padx=24, pady=(8, 24))

        # Previous button
        self.prev_button = ctk.CTkButton(
            pagination_frame,
            text="← Previous",
            width=120,
            height=32,
            font=("Segoe UI", 10),
            command=self._previous_page,
            state="disabled",
        )
        self.prev_button.pack(side="left")

        # Page info
        self.page_info_label = ctk.CTkLabel(
            pagination_frame,
            text=f"Page {self.current_page} of {self.total_pages} ({self.total_items} total items)",
            font=("Segoe UI", 10),
        )
        self.page_info_label.pack(side="left", padx=20)

        # Next button
        self.next_button = ctk.CTkButton(
            pagination_frame,
            text="Next →",
            width=120,
            height=32,
            font=("Segoe UI", 10),
            command=self._next_page,
            state="disabled",
        )
        self.next_button.pack(side="left")
