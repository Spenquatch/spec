"""Test output normalization utilities for Rich vs plain text compatibility.

This module provides utilities to normalize CLI output formats for consistent
test validation, resolving compatibility issues between Rich formatting and
plain text output modes.
"""

import re
from typing import Any

from ...core.context_bridge import debug_logger


def normalize_output_for_testing(output: str, mode: str = "auto") -> str:
    """Normalize CLI output for consistent test validation.

    Args:
        output: Raw CLI output string (Rich-formatted or plain text)
        mode: Normalization mode - "rich", "plain", or "auto"

    Returns:
        Normalized output string suitable for test assertions

    Raises:
        ValueError: If mode is invalid
        TypeError: If output is not a string

    Example:
        >>> rich_output = "[bold]Project initialized[/bold]"
        >>> plain_output = normalize_output_for_testing(rich_output, "plain")
        >>> print(plain_output)
        "Project initialized"
    """
    if not isinstance(output, str):
        raise TypeError(f"Output must be a string, got {type(output)}")

    valid_modes = {"auto", "rich", "plain"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {valid_modes}")

    debug_logger.log(
        "DEBUG",
        "Normalizing CLI output",
        output_length=len(output),
        mode=mode,
        has_rich_markup=_has_rich_markup(output),
    )

    # Auto-detect format if mode is "auto" - for testing, convert to plain
    if mode == "auto":
        detected_mode = _detect_output_format(output)
        debug_logger.log(
            "DEBUG",
            "Auto-detected output format, normalizing to plain for testing",
            detected_mode=detected_mode,
        )
        mode = "plain"  # For testing, always normalize to plain text

    # Apply normalization based on target format and input content
    detected_format = _detect_output_format(output)

    if mode == "plain":
        # Convert to plain text regardless of input format
        if detected_format == "rich":
            normalized = _normalize_rich_output(output)
        else:
            normalized = _normalize_plain_output(output)
    else:  # mode == "rich"
        # Keep rich formatting or convert plain to rich (no-op)
        normalized = _normalize_plain_output(output)

    debug_logger.log(
        "INFO",
        "Output normalization completed",
        original_length=len(output),
        normalized_length=len(normalized),
        mode=mode,
    )

    return normalized


def extract_formatting_metadata(output: str) -> dict[str, Any]:
    """Extract formatting metadata from CLI output.

    Args:
        output: CLI output string

    Returns:
        Dictionary with formatting metadata

    Example:
        >>> metadata = extract_formatting_metadata("[bold]Text[/bold]")
        >>> print(metadata["has_rich_markup"])
        True
    """
    metadata = {
        "has_rich_markup": _has_rich_markup(output),
        "has_ansi_codes": _has_ansi_codes(output),
        "line_count": output.count("\n") + 1 if output else 0,
        "character_count": len(output),
        "detected_format": _detect_output_format(output),
    }

    # Extract Rich markup tags
    rich_tags = re.findall(r"\[[^\]]+\]", output) if _has_rich_markup(output) else []
    metadata["rich_tags"] = rich_tags
    metadata["rich_tag_count"] = len(rich_tags)

    # Extract ANSI escape sequences
    ansi_codes = (
        re.findall(r"\x1b\[[0-9;]*m", output) if _has_ansi_codes(output) else []
    )
    metadata["ansi_codes"] = ansi_codes
    metadata["ansi_code_count"] = len(ansi_codes)

    debug_logger.log(
        "DEBUG",
        "Extracted formatting metadata",
        metadata=metadata,
    )

    return metadata


def _detect_output_format(output: str) -> str:
    """Detect output format type (Rich markup or plain text).

    Args:
        output: CLI output string

    Returns:
        Format type: "rich" or "plain"
    """
    # Check for Rich markup patterns
    if _has_rich_markup(output):
        return "rich"

    # Check for ANSI escape sequences
    if _has_ansi_codes(output):
        return "rich"  # Treat ANSI as Rich-like formatting

    return "plain"


def _has_rich_markup(output: str) -> bool:
    """Check if output contains Rich markup tags.

    Args:
        output: Output string to check

    Returns:
        True if Rich markup is detected
    """
    # Pattern for Rich markup: [tag] or [/tag]
    rich_pattern = re.compile(r"\[[^\]]*\]")
    return bool(rich_pattern.search(output))


def _has_ansi_codes(output: str) -> bool:
    """Check if output contains ANSI escape sequences.

    Args:
        output: Output string to check

    Returns:
        True if ANSI codes are detected
    """
    # Pattern for ANSI escape sequences
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return bool(ansi_pattern.search(output))


def _normalize_rich_output(output: str) -> str:
    """Normalize Rich-formatted output to plain text.

    Args:
        output: Rich-formatted output string

    Returns:
        Plain text version of the output
    """
    # Remove Rich markup tags (e.g., [bold], [/bold], [red])
    normalized = re.sub(r"\[[^\]]*\]", "", output)

    # Remove ANSI escape sequences
    normalized = re.sub(r"\x1b\[[0-9;]*m", "", normalized)

    # Normalize whitespace
    normalized = _normalize_whitespace(normalized)

    debug_logger.log(
        "DEBUG",
        "Normalized Rich output",
        original_length=len(output),
        normalized_length=len(normalized),
    )

    return normalized


def _normalize_plain_output(output: str) -> str:
    """Normalize plain text output for consistent formatting.

    Args:
        output: Plain text output string

    Returns:
        Normalized plain text output
    """
    # Just normalize whitespace for plain text
    normalized = _normalize_whitespace(output)

    debug_logger.log(
        "DEBUG",
        "Normalized plain output",
        original_length=len(output),
        normalized_length=len(normalized),
    )

    return normalized


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text for consistent comparison.

    Args:
        text: Input text

    Returns:
        Text with normalized whitespace
    """
    # Replace multiple consecutive spaces with single space
    text = re.sub(r" +", " ", text)

    # Replace multiple consecutive newlines with single newline
    text = re.sub(r"\n+", "\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
