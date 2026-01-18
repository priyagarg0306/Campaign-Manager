"""
Shared validation utilities.
"""
from uuid import UUID

__all__ = ['is_valid_uuid']


def is_valid_uuid(value: str) -> bool:
    """
    Validate UUID format.

    Args:
        value: String to validate as UUID

    Returns:
        True if value is a valid UUID v4 format
    """
    if not value or not isinstance(value, str):
        return False
    try:
        UUID(value, version=4)
        return True
    except (ValueError, AttributeError, TypeError):
        return False
