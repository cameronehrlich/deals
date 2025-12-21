"""Formatting utilities for display."""

from typing import Optional


def format_currency(value: Optional[float], decimals: int = 0) -> str:
    """Format a number as currency."""
    if value is None:
        return "N/A"
    if decimals == 0:
        return f"${value:,.0f}"
    return f"${value:,.{decimals}f}"


def format_percent(value: Optional[float], decimals: int = 1) -> str:
    """Format a decimal as percentage."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_number(value: Optional[float], decimals: int = 0) -> str:
    """Format a number with commas."""
    if value is None:
        return "N/A"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def format_score(score: Optional[float]) -> str:
    """Format a score out of 100."""
    if score is None:
        return "N/A"
    return f"{score:.1f}/100"


def format_days(days: Optional[int]) -> str:
    """Format days on market."""
    if days is None:
        return "N/A"
    if days == 1:
        return "1 day"
    return f"{days} days"
