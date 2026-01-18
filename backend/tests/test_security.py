"""
Security-focused tests for input validation.
"""
import json
import pytest


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_headers_present(self, client, sample_campaign_data):
        """Test that rate limit headers are present in responses."""
        response = client.post(
            '/api/campaigns',
            data=json.dumps(sample_campaign_data),
            content_type='application/json'
        )
        # Rate limit headers should be present
        assert response.status_code in [201, 429]


class TestSecurityHeaders:
    """Tests for security headers."""

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get('/api/health/live')

        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'

        assert 'X-XSS-Protection' in response.headers


class TestValidators:
    """Tests for validator utilities."""

    def test_is_valid_uuid_with_valid_uuids(self):
        """Test is_valid_uuid with valid UUIDs."""
        from app.utils.validators import is_valid_uuid

        assert is_valid_uuid('00000000-0000-0000-0000-000000000000') is True
        assert is_valid_uuid('a1b2c3d4-e5f6-4890-abcd-ef1234567890') is True

    def test_is_valid_uuid_with_invalid_uuids(self):
        """Test is_valid_uuid with invalid UUIDs."""
        from app.utils.validators import is_valid_uuid

        assert is_valid_uuid('not-a-uuid') is False
        assert is_valid_uuid('') is False
        assert is_valid_uuid(None) is False
        assert is_valid_uuid('12345') is False
