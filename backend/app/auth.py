"""
Authentication utilities (simplified - no JWT authentication required).

This module provides basic utility functions. JWT authentication has been
removed as this is not a production application.
"""
from app.utils.validators import is_valid_uuid

__all__ = ['is_valid_uuid']

# Re-export is_valid_uuid for backward compatibility with any imports
