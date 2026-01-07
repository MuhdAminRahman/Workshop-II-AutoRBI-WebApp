from dataclasses import dataclass
from typing import Tuple, List


@dataclass(frozen=True)
class Fonts:
    """Font configurations"""

    TITLE = ("Segoe UI", 24, "bold")
    SECTION_TITLE = ("Segoe UI", 26, "bold")
    SECTION_LABEL = ("Segoe UI", 18, "bold")
    SUBTITLE = ("Segoe UI", 11)
    BUTTON = ("Segoe UI", 11)
    BUTTON_BOLD = ("Segoe UI", 11, "bold")
    SMALL = ("Segoe UI", 9)
    TINY = ("Segoe UI", 16)
    TABLE_HEADER = ("Segoe UI", 8, "bold")


@dataclass(frozen=True)
class Colors:
    """Color scheme"""

    PRIMARY = ("gray20", "gray30")
    BORDER = ("gray80", "gray25")
    SECTION_BG = ("gray90", "gray15")
    TABLE_HEADER_BG = ("#FFFF00", "#555500")
    TABLE_HEADER_TEXT = ("black", "yellow")
    TRANSPARENT = "transparent"
    WHITE_BLACK = ("white", "gray20")


@dataclass(frozen=True)
class Sizes:
    """Size constants"""

    BUTTON_HEIGHT = 36
    BUTTON_HEIGHT_SM = 32
    BUTTON_HEIGHT_XS = 28
    PADDING_OUTER = 32
    PADDING_SECTION = 24
    PADDING_INNER = 16
    CORNER_RADIUS = 18
    CORNER_RADIUS_SM = 12
    CORNER_RADIUS_XS = 8


@dataclass(frozen=True)
class Messages:
    """User-facing messages"""

    NO_FILES = "No files selected"
    NO_WORK = "Please select a work first."
    EXTRACTION_COMPLETE = "✅ All files extracted successfully."
    EXTRACTION_FAILED = "❌ Extraction failed"
    SAVE_SUCCESS = "Successfully saved {} equipment items to Excel!"
    SAVE_FAILED = "Failed to save data to Excel"
    NO_DATA = "No equipment data available. Please extract data first."
    POWERPOINT_SUCCESS = "PowerPoint created successfully!"
    POWERPOINT_FAILED = "Failed to create PowerPoint. Check logs for details."


class TableColumns:
    """Table column definitions"""

    COLUMNS: List[Tuple[str, int]] = [
        ("NO.", 40),
        ("EQUIPMENT NO.", 100),
        ("PMT NO.", 90),
        ("EQUIPMENT DESCRIPTION", 150),
        ("PARTS", 100),
        ("PHASE", 70),
        ("FLUID", 80),
        ("TYPE", 80),
        ("SPEC.", 80),
        ("GRADE", 70),
        ("INSULATION\n(yes/No)", 80),
        ("DESIGN\nTEMP. (°C)", 90),
        ("DESIGN\nPRESSURE\n(Mpa)", 90),
        ("OPERATING\nTEMP. (°C)", 90),
        ("OPERATING\nPRESSURE\n(Mpa)", 90),
    ]

    NUM_COLUMNS = len(COLUMNS)

    @classmethod
    def get_column_names(cls) -> List[str]:
        return [col[0] for col in cls.COLUMNS]

    @classmethod
    def get_column_widths(cls) -> List[int]:
        return [col[1] for col in cls.COLUMNS]
