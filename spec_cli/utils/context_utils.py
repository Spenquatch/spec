"""Context utilities for validating and analyzing SpecContext instances.

This module provides utilities for validating context immutability, generating
context hashes for equality comparison, and ensuring proper context construction.
"""

import hashlib
from dataclasses import fields, is_dataclass
from typing import Any


def validate_context_immutability(context: Any) -> bool:
    """Validate that a context instance is properly immutable.

    Args:
        context: Context instance to validate for immutability

    Returns:
        True if context is immutable (frozen dataclass), False otherwise

    Example:
        is_immutable = validate_context_immutability(spec_context)
        if not is_immutable:
            raise ContextValidationError("Context must be immutable")
    """
    if not is_dataclass(context):
        return False

    # Check if dataclass is frozen
    dataclass_params = getattr(context, "__dataclass_params__", None)
    if dataclass_params is None or not getattr(dataclass_params, "frozen", False):
        return False

    return True


def create_context_hash(context: Any) -> str:
    """Create deterministic hash for context instance.

    Args:
        context: Context instance to generate hash for

    Returns:
        SHA-256 hash string of context contents

    Raises:
        ValueError: If context is not a dataclass or hash generation fails

    Example:
        hash1 = create_context_hash(context1)
        hash2 = create_context_hash(context2)
        are_equal = hash1 == hash2
    """
    if not is_dataclass(context):
        raise ValueError("Context must be a dataclass")

    try:
        # Create consistent string representation
        field_values = []
        for field in fields(context):
            value = getattr(context, field.name)
            # Convert value to string representation
            if hasattr(value, "__class__"):
                # Include class name for type safety
                field_str = f"{field.name}:{value.__class__.__name__}:{str(value)}"
            else:
                field_str = f"{field.name}:{str(value)}"
            field_values.append(field_str)

        # Sort for consistent ordering
        field_values.sort()
        context_str = "|".join(field_values)

        # Generate SHA-256 hash
        hash_bytes = hashlib.sha256(context_str.encode("utf-8")).hexdigest()
        return hash_bytes

    except Exception as e:
        raise ValueError(f"Failed to generate context hash: {e}") from e
