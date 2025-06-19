"""
Terminal-inspired theme based on the HTML mockup
Professional monospace aesthetic with black background and terminal-style interface
"""

from .terminal_theme_complete import get_complete_terminal_theme, get_console_color_map, format_console_message

def get_terminal_theme() -> str:
    """
    Get comprehensive terminal theme stylesheet for PyQt6
    Based on the HTML mockup with complete functionality preservation
    """
    return get_complete_terminal_theme()


def get_terminal_theme_with_system_stats() -> str:
    """
    Get terminal theme with enhanced system stats display functionality
    """
    return get_complete_terminal_theme()


def get_terminal_console_colors() -> dict:
    """
    Get color mapping for console log levels
    """
    return get_console_color_map()