"""
Tests for auth module.
"""
import pytest


class TestAuthModule:
    """Tests for auth module exports."""

    def test_is_valid_uuid_exported(self):
        """Test that is_valid_uuid is properly exported from auth module."""
        from app.auth import is_valid_uuid

        # Test valid UUIDs
        assert is_valid_uuid('12345678-1234-1234-1234-123456789012') is True
        assert is_valid_uuid('00000000-0000-0000-0000-000000000000') is True

        # Test invalid UUIDs
        assert is_valid_uuid('not-a-uuid') is False
        assert is_valid_uuid('12345') is False

    def test_auth_module_all_exports(self):
        """Test that __all__ contains expected exports."""
        from app import auth

        assert hasattr(auth, '__all__')
        assert 'is_valid_uuid' in auth.__all__

    def test_is_valid_uuid_function_identity(self):
        """Test that the exported function is the same as validators."""
        from app.auth import is_valid_uuid as auth_uuid
        from app.utils.validators import is_valid_uuid as validators_uuid

        # Should be the same function
        assert auth_uuid is validators_uuid

    def test_is_valid_uuid_with_various_inputs(self):
        """Test is_valid_uuid with various input types."""
        from app.auth import is_valid_uuid

        # Valid UUIDs in different formats
        assert is_valid_uuid('a1b2c3d4-e5f6-7890-abcd-ef1234567890') is True
        assert is_valid_uuid('A1B2C3D4-E5F6-7890-ABCD-EF1234567890') is True

        # Invalid inputs
        assert is_valid_uuid('') is False
        assert is_valid_uuid('   ') is False
        assert is_valid_uuid(None) is False
        assert is_valid_uuid(123) is False
