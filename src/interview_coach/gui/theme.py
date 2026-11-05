"""Visual design tokens. Each color is a (light mode, dark mode) pair."""

import customtkinter as ctk

Color = tuple[str, str]

BACKGROUND: Color = ("#F6F4EF", "#14181A")
SIDEBAR: Color = ("#ECE8DF", "#1B2022")
SURFACE: Color = ("#FFFFFF", "#22282B")
BORDER: Color = ("#DDD8CC", "#343B3F")
TEXT: Color = ("#1F2421", "#ECEFEA")
MUTED: Color = ("#5C625D", "#9BA5A0")
ACCENT: Color = ("#1F6F5C", "#27806A")
ACCENT_HOVER: Color = ("#185A4A", "#1F6A58")
ON_ACCENT: Color = ("#FFFFFF", "#FFFFFF")
ACCENT_TEXT: Color = ("#1F6F5C", "#5CC7AA")
DANGER: Color = ("#B93F2B", "#BE4733")
DANGER_HOVER: Color = ("#9C3222", "#A63C2A")
DANGER_TEXT: Color = ("#B93F2B", "#F08A76")
SECONDARY_HOVER: Color = ("#E2DDD1", "#2C3336")

RADIUS = 14
GAP = 16
SMALL_GAP = 8


def font(size: int = 14, *, bold: bool = False) -> ctk.CTkFont:
    """Create a font; it can only be called once the main window exists.

    Args:
        size: Font size in points.
        bold: Whether to use the bold weight.

    Returns:
        The font.
    """
    return ctk.CTkFont(size=size, weight="bold" if bold else "normal")


def secondary_button_style() -> dict[str, object]:
    """Get the options shared by low-emphasis buttons.

    Returns:
        Keyword arguments for ``CTkButton``.
    """
    return {
        "fg_color": "transparent",
        "hover_color": SECONDARY_HOVER,
        "text_color": TEXT,
        "text_color_disabled": MUTED,
        "border_width": 1,
        "border_color": BORDER,
    }
