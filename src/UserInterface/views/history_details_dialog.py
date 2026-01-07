"""History Details Dialog for displaying detailed work history information."""

import customtkinter as ctk
from typing import Dict, Any


class HistoryDetailsDialog(ctk.CTkToplevel):
    """Modal dialog showing detailed work history information."""

    def __init__(self, parent: ctk.CTk, details: Dict[str, Any]):
        super().__init__(parent)

        self.details = details

        # Configure window
        self.title("Work History Details")
        self.geometry("750x600")
        self.resizable(False, False)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # Center the dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (750 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (600 // 2)
        self.geometry(f"750x600+{x}+{y}")

        # Build UI
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the dialog UI"""

        # Header
        header = ctk.CTkFrame(
            self, corner_radius=0, height=60, fg_color=("#3498db", "#2980b9")
        )
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header,
            text="Work History Details",
            font=("Segoe UI", 20, "bold"),
            text_color="white",
        )
        title.pack(side="left", padx=24, pady=16)

        # Scrollable content area
        content = ctk.CTkScrollableFrame(self)
        content.pack(expand=True, fill="both", padx=24, pady=(24, 12))

        # Display all details
        self._add_detail_section(
            content,
            "Basic Information",
            [
                ("History ID", self.details.get("id")),
                ("Action Type", self.details.get("action_type")),
                ("Timestamp", self.details.get("timestamp")),
                ("Description", self.details.get("description")),
            ],
        )

        self._add_detail_section(
            content,
            "Work Information",
            [
                ("Work ID", self.details.get("work_id")),
                ("Work Name", self.details.get("work_name")),
                ("Work Status", self.details.get("work_status")),
            ],
        )

        self._add_detail_section(
            content,
            "User Information",
            [
                ("User ID", self.details.get("user_id")),
                ("Username", self.details.get("username")),
                ("Full Name", self.details.get("user_full_name")),
                ("Role", self.details.get("user_role")),
            ],
        )

        if self.details.get("equipment_id"):
            self._add_detail_section(
                content,
                "Equipment Information",
                [
                    ("Equipment ID", self.details.get("equipment_id")),
                    ("Equipment Number", self.details.get("equipment_no")),
                    ("PMT Number", self.details.get("pmt_no")),
                    ("Description", self.details.get("equipment_description")),
                ],
            )

        # Close button
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 24))

        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            width=140,
            height=40,
            font=("Segoe UI", 12),
            command=self.destroy,
        )
        close_btn.pack()

    def _add_detail_section(
        self, parent: ctk.CTkFrame, title: str, items: list
    ) -> None:
        """Add a section of detail items"""

        section_frame = ctk.CTkFrame(
            parent, corner_radius=8, border_width=1, border_color=("gray80", "gray30")
        )
        section_frame.pack(fill="x", pady=(0, 16))

        # Section title
        title_label = ctk.CTkLabel(
            section_frame, text=title, font=("Segoe UI", 15, "bold"), anchor="w"
        )
        title_label.pack(anchor="w", padx=20, pady=(16, 12))

        # Items
        for label, value in items:
            if value is not None and value != "":
                item_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
                item_frame.pack(fill="x", padx=20, pady=6)

                label_widget = ctk.CTkLabel(
                    item_frame,
                    text=f"{label}:",
                    font=("Segoe UI", 11, "bold"),
                    width=180,
                    anchor="w",
                )
                label_widget.pack(side="left")

                value_widget = ctk.CTkLabel(
                    item_frame,
                    text=str(value),
                    font=("Segoe UI", 11),
                    anchor="w",
                    wraplength=480,
                )
                value_widget.pack(side="left", padx=(8, 0), fill="x", expand=True)

        # Bottom padding
        padding = ctk.CTkLabel(section_frame, text="", height=12)
        padding.pack()
