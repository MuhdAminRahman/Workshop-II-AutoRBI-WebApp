"""Main entry point for AutoRBI application."""

import logging
from app import AutoRBIApp


def setup_logging():
    """Configure logging with no duplicate handlers"""
    # Get root logger
    logger = logging.getLogger()

    # Only configure if not already configured
    if not logger.hasHandlers():
        # Set logging level
        logger.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)


def main() -> None:
    """Run the AutoRBI application."""
    app = AutoRBIApp()
    app.mainloop()


if __name__ == "__main__":
    main()
