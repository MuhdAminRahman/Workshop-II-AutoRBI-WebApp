"""Settings view for AutoRBI application."""

import customtkinter as ctk
from tkinter import messagebox


class SettingsView:
    """Handles the Settings interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller

    def show(self) -> None:
        """Display the Settings interface."""
        # TODO: Backend - Load user preferences from database
        # TODO: Backend - Load theme, language, notification settings
        # TODO: Backend - Return saved user settings
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back",
            command=self.controller.show_main_menu,
            width=120,
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
            text="Settings",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.grid(row=0, column=1, sticky="e")

        # Main content
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=24, pady=24)

        # Appearance section
        appearance_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        appearance_frame.pack(fill="x", pady=(0, 24))

        section_title = ctk.CTkLabel(
            appearance_frame,
            text="Appearance",
            font=("Segoe UI", 16, "bold"),
        )
        section_title.pack(anchor="w", pady=(0, 12))

        theme_label = ctk.CTkLabel(
            appearance_frame,
            text="Theme:",
            font=("Segoe UI", 12),
        )
        theme_label.pack(anchor="w", pady=(0, 8))

        theme_var = ctk.StringVar(value="dark")
        theme_switch = ctk.CTkSegmentedButton(
            appearance_frame,
            values=["light", "dark", "system"],
            variable=theme_var,
            command=lambda v: self._change_theme(v),
        )
        theme_switch.pack(anchor="w", pady=(0, 16))

        # Notifications section
        notif_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        notif_frame.pack(fill="x", pady=(0, 24))

        notif_title = ctk.CTkLabel(
            notif_frame,
            text="Notifications",
            font=("Segoe UI", 16, "bold"),
        )
        notif_title.pack(anchor="w", pady=(0, 12))

        # Notification toggles
        notif_options = [
            ("Extraction completion alerts", True),
            ("Report generation notifications", True),
            ("System updates", True),
            ("Error warnings", True),
        ]

        for option_text, default in notif_options:
            option_frame = ctk.CTkFrame(notif_frame, fg_color="transparent")
            option_frame.pack(fill="x", pady=(0, 8))

            option_label = ctk.CTkLabel(
                option_frame,
                text=option_text,
                font=("Segoe UI", 11),
            )
            option_label.pack(side="left")

            option_switch = ctk.CTkSwitch(
                option_frame,
                text="",
                onvalue=True,
                offvalue=False,
            )
            option_switch.pack(side="right")
            option_switch.select() if default else option_switch.deselect()

        # Save button
        save_btn = ctk.CTkButton(
            scroll,
            text="Save Settings",
            command=lambda: messagebox.showinfo("Success", "Settings saved!"),
            height=40,
            font=("Segoe UI", 12, "bold"),
        )
        save_btn.pack(pady=(20, 0))

    def _change_theme(self, theme: str) -> None:
        """Change application theme."""
        # TODO: Backend - Save theme preference to database
        # TODO: Backend - Apply theme to all UI components
        # TODO: Backend - Return confirmation of theme change
        import customtkinter as ctk
        ctk.set_appearance_mode(theme)

