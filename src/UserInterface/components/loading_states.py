"""Loading states and progress indicators for AutoRBI application."""

from typing import Optional
import customtkinter as ctk


class LoadingOverlay:
    """Full-screen loading overlay with spinner."""

    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self.overlay: Optional[ctk.CTkFrame] = None
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.status_label: Optional[ctk.CTkLabel] = None

    def show(self, message: str = "Loading...", show_progress: bool = False) -> None:
        """Show loading overlay - disabled to prevent background issues.
        
        TODO: Backend - Can optionally enable overlay for long-running operations
        TODO: Backend - Send progress updates via update_progress() method
        """
        # Overlay disabled - just keep references for compatibility
        pass

    def update_progress(self, value: float, message: Optional[str] = None) -> None:
        """Update progress bar (0.0 to 1.0)."""
        # No-op since overlay is disabled
        pass

    def hide(self) -> None:
        """Hide loading overlay."""
        # No-op since overlay is disabled
        pass


class SkeletonLoader:
    """Skeleton screen loader for content placeholders."""

    @staticmethod
    def create_skeleton_card(parent: ctk.CTkFrame, width: int = 300, height: int = 100) -> ctk.CTkFrame:
        """Create a skeleton loading card."""
        skeleton = ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("gray90", "gray20"),
            width=width,
            height=height,
        )
        
        # Animated shimmer effect (simulated with gradient-like appearance)
        shimmer = ctk.CTkFrame(
            skeleton,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            width=width - 20,
            height=20,
        )
        shimmer.place(relx=0.5, rely=0.3, anchor="center")
        
        shimmer2 = ctk.CTkFrame(
            skeleton,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            width=width - 40,
            height=16,
        )
        shimmer2.place(relx=0.5, rely=0.5, anchor="center")
        
        return skeleton

