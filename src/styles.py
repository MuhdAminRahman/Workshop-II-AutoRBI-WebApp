"""Style configuration for AutoRBI CustomTkinter interface."""

import customtkinter as ctk


def configure_styles() -> None:
    """Configure global CustomTkinter appearance for the application."""
    # Appearance
    ctk.set_appearance_mode("dark")  # "light", "dark", or "system"
    ctk.set_default_color_theme("blue")  # built‑in: "blue", "green", "dark-blue"

