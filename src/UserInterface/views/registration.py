"""Registration view for AutoRBI application (CustomTkinter)."""

from tkinter import messagebox

import customtkinter as ctk


from AutoRBI_Database.validation_rules import (
    UsernameRules,
    PasswordRules,
    FullNameRules,
    get_username_validation_error,
    get_password_validation_error,
    get_fullname_validation_error,
)

class RegistrationView:
    """Handles the registration interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller

    def show(self) -> None:
        """Display the registration interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Background container with gradient-like effect
        bg_frame = ctk.CTkFrame(
            self.parent,
            corner_radius=0,
            fg_color=("gray95", "gray10"),
        )
        bg_frame.pack(expand=True, fill="both")

        # Center container for glass card
        center_container = ctk.CTkFrame(bg_frame, fg_color="transparent")
        center_container.pack(expand=True, fill="both")
        center_container.grid_rowconfigure(0, weight=1)
        center_container.grid_columnconfigure(0, weight=1)

        # Glass morphism card - SQUARE shape with blur effect
        glass_card = ctk.CTkFrame(
            center_container,
            corner_radius=20,
            border_width=2,
            width=520,  # Square width (slightly larger for registration form)
            height=520,  # Square height (same as width for perfect square)
            # Glass effect: light colors for light mode, darker semi-transparent for dark mode
            fg_color=("#F0F0F0", "#2B2B2B"),
            border_color=("#E0E0E0", "#404040"),
        )
        glass_card.grid(row=0, column=0, padx=50, pady=40, sticky="")
        # Prevent the card from resizing - maintain square shape
        glass_card.grid_propagate(False)
        glass_card.grid_rowconfigure(0, weight=1)
        glass_card.grid_columnconfigure(0, weight=1)

        # Scrollable content inside glass card
        content = ctk.CTkScrollableFrame(
            glass_card,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray40"),
            scrollbar_button_hover_color=("gray60", "gray50"),
        )
        content.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)
        content.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            content,
            text="Create New Account",
            font=("Segoe UI", 28, "bold"),
            text_color=("gray20", "gray95"),
        )
        title_label.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        subtitle_label = ctk.CTkLabel(
            content,
            text="Fill in your details to create an account.",
            font=("Segoe UI", 12),
            text_color=("gray40", "gray75"),
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 32), sticky="ew")

        fields = ctk.CTkFrame(content, fg_color="transparent")
        fields.grid(row=2, column=0, sticky="ew")
        fields.grid_columnconfigure(0, weight=1)

        # Full Name field
        fullname_label = ctk.CTkLabel(
            fields,
            text="Full Name",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        fullname_label.pack(anchor="w", pady=(0, 8))

        fullname_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Enter your full name",
            font=("Segoe UI", 12),
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        fullname_entry.pack(fill="x", pady=(0, 16))
        fullname_entry.focus()

        # Username field
        username_label = ctk.CTkLabel(
            fields,
            text="Username",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        username_label.pack(anchor="w", pady=(0, 8))

        username_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Choose a username",
            font=("Segoe UI", 12),
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        username_entry.pack(fill="x", pady=(0, 16))

        # Password field
        password_label = ctk.CTkLabel(
            fields,
            text="Password",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        password_label.pack(anchor="w", pady=(0, 8))

        password_entry = ctk.CTkEntry(
            fields,
            placeholder_text="At least 6 characters",
            font=("Segoe UI", 12),
            show="*",
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        password_entry.pack(fill="x", pady=(0, 16))

        # Confirm Password field
        confirm_label = ctk.CTkLabel(
            fields,
            text="Confirm Password",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        confirm_label.pack(anchor="w", pady=(0, 8))

        confirm_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Re-enter your password",
            font=("Segoe UI", 12),
            show="*",
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        confirm_entry.pack(fill="x", pady=(0, 24))

        # Register button
        def handle_register() -> None:
            """
            Handle registration button click with comprehensive validation and error handling.

            This method implements:
            - 6. Input Validation: Multi-layer validation with specific feedback
            - 7. User-Friendly Messages: Clear, actionable error messages
            - 8. Error Context: Field-specific error handling

            Flow:
            1. Get and clean input values
            2. Validate all fields at UI level
            3. Call backend registration
            4. Handle response based on error_type
            5. Provide appropriate feedback
            """
            # Get input values
            fullname = fullname_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()

            # ==================================================================
            # LAYER 1: UI-LEVEL VALIDATION 
            # Using centralized rules from validation_rules.py
            # ==================================================================

            # Validate full name using centralized validation
            fullname_error = get_fullname_validation_error(fullname)
            if fullname_error:
                messagebox.showwarning("Invalid Full Name", fullname_error)
                fullname_entry.focus()
                fullname_entry.select_range(0, "end")
                return

            # Validate username using centralized validation
            username_error = get_username_validation_error(username)
            if username_error:
                messagebox.showwarning("Invalid Username", username_error)
                username_entry.focus()
                username_entry.select_range(0, "end")
                return

            # Validate password using centralized validation
            password_error = get_password_validation_error(password)
            if password_error:
                messagebox.showwarning("Invalid Password", password_error)
                password_entry.delete(0, "end")
                confirm_entry.delete(0, "end")
                password_entry.focus()
                return

            # Check if passwords match (this is UI-only, not a backend rule)
            if password != confirm:
                messagebox.showerror(
                    "Passwords Don't Match",
                    PasswordRules.ERRORS["mismatch"] + "\n"
                    "Please ensure both password fields are identical.",
                )
                # Clear both password fields for security
                password_entry.delete(0, "end")
                confirm_entry.delete(0, "end")
                password_entry.focus()
                return

            # Optional: Check for password strength (warning only, not blocking)
            # This is controlled by PasswordRules flags - if REQUIRE_DIGIT/LETTER are False,
            # we just warn the user but let them continue
            has_digit = any(char.isdigit() for char in password)
            has_letter = any(char.isalpha() for char in password)

            if not (has_digit and has_letter):
                # This is a warning, not blocking - user can choose to continue
                response = messagebox.askyesno(
                    "Weak Password",
                    "Your password should contain both letters and numbers for better security.\n\n"
                    "Do you want to continue with this password?",
                )
                if not response:
                    password_entry.focus()
                    password_entry.select_range(0, "end")
                    return

            # Clean inputs for backend call
            fullname_clean = fullname.strip()
            username_clean = username.strip()

            # ==================================================================
            # LAYER 2: BACKEND REGISTRATION
            # ==================================================================
            try:
                # Call backend registration via the app controller
                result = self.controller.register_user(
                    full_name=fullname_clean,
                    username=username_clean,
                    password=password,
                )

                # ==============================================================
                # LAYER 3: HANDLE RESPONSE BASED ON RESULT
                # ==============================================================
                if result.get("success"):
                    # SUCCESS - Show success message and return to login
                    messagebox.showinfo(
                        "Registration Successful",
                        result.get(
                            "message",
                            "Registration successful! You can now login with your credentials.",
                        ),
                    )

                    # Navigate to login screen
                    self.controller.show_login()

                else:
                    # FAILURE - Handle based on error_type
                    error_type = result.get("error_type", "unknown")
                    message = result.get("message", "Registration failed")

                    # Different handling for different error types
                    if error_type == "validation":
                        messagebox.showwarning("Validation Error", message)

                        # Focus on the problematic field if specified
                        field = result.get("field", "")
                        if field == "username":
                            username_entry.focus()
                            username_entry.select_range(0, "end")
                        elif field == "password":
                            password_entry.delete(0, "end")
                            confirm_entry.delete(0, "end")
                            password_entry.focus()
                        elif field in ("fullname", "full_name"):
                            fullname_entry.focus()
                            fullname_entry.select_range(0, "end")

                    elif error_type == "account_exists":
                        # Username already taken
                        messagebox.showerror(
                            "Username Taken",
                            message + "\n\nPlease try a different username.",
                        )
                        # Clear username and focus for retry
                        username_entry.delete(0, "end")
                        username_entry.focus()

                    elif error_type == "system":
                        # System error (database, network, etc.)
                        messagebox.showerror(
                            "Registration Error",
                            f"{message}\n\n"
                            "This is a temporary issue. Please try again in a few moments.\n"
                            "If the problem persists, contact support.",
                        )

                    else:
                        # Unknown error type - generic handling
                        messagebox.showerror(
                            "Registration Failed",
                            f"{message}\n\n"
                            "Please try again or contact support if this continues.",
                        )

            except Exception as e:
                # Catch-all for any unexpected UI-level errors
                messagebox.showerror(
                    "Unexpected Error",
                    "An unexpected error occurred during registration.\n"
                    "Please try again or contact support.",
                )
                # Basic logging
                print(f"UI Error in registration: {e}")
                

        # Primary button with glass effect
        register_btn = ctk.CTkButton(
            fields,
            text="Create account",
            command=handle_register,
            height=46,
            font=("Segoe UI", 13, "bold"),
            corner_radius=12,
            border_width=1,
            border_color=("#6496FF", "#6496FF"),
        )
        register_btn.pack(fill="x", pady=(0, 12))

        # Back to login button
        back_btn = ctk.CTkButton(
            fields,
            text="Back to login",
            command=self.controller.show_login,
            height=36,
            font=("Segoe UI", 11),
            fg_color="transparent",
            text_color=("gray40", "gray70"),
            hover_color=("#E8E8E8", "#404040"),
            border_width=0,
        )
        back_btn.pack(fill="x", pady=(0, 0))

        # Bind Enter key to register
        confirm_entry.bind("<Return>", lambda _event: handle_register())