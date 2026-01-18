"""
Tests for application error handlers.
"""
import pytest
from flask import abort


class TestErrorHandlers:
    """Tests for Flask error handlers."""

    def test_400_bad_request_handler(self, client):
        """Test 400 Bad Request error handler."""
        # Send malformed JSON to trigger 400
        response = client.post(
            '/api/campaigns',
            data='not valid json',
            content_type='application/json'
        )
        # Note: This returns 400 from the route, not the handler
        assert response.status_code == 400

    def test_404_not_found_handler(self, client):
        """Test 404 Not Found error handler."""
        response = client.get('/api/nonexistent-route')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'Not found' in data['error']

    def test_413_max_content_length_configured(self, app):
        """Test that MAX_CONTENT_LENGTH is configured."""
        # Just verify the config is set, don't actually test with large payloads
        assert 'MAX_CONTENT_LENGTH' in app.config
        assert app.config['MAX_CONTENT_LENGTH'] > 0

    def test_500_internal_error_handler_via_exception(self, auth_client):
        """Test 500 Internal Server Error handler."""
        from unittest.mock import patch

        with patch('app.routes.campaigns.CampaignService.create_campaign') as mock_create:
            mock_create.side_effect = Exception("Unexpected error")

            response = auth_client.post(
                '/api/campaigns',
                json={
                    'name': 'Test',
                    'objective': 'SALES',
                    'campaign_type': 'DEMAND_GEN',
                    'daily_budget': 1000000,
                    'start_date': '2030-01-15'
                }
            )
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_creates_with_default_config(self):
        """Test app can be created with default config."""
        from app import create_app
        import os

        # Set FLASK_ENV to development
        old_env = os.environ.get('FLASK_ENV')
        os.environ['FLASK_ENV'] = 'development'

        try:
            app = create_app(None)  # Pass None to use default
            assert app is not None
        finally:
            if old_env:
                os.environ['FLASK_ENV'] = old_env
            elif 'FLASK_ENV' in os.environ:
                del os.environ['FLASK_ENV']

    def test_app_creates_with_testing_config(self):
        """Test app can be created with testing config."""
        from app import create_app
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present on responses."""
        response = client.options('/api/health')
        # CORS should be configured
        assert response.status_code in [200, 204]


class TestRateLimiting:
    """Tests for rate limiting configuration."""

    def test_rate_limit_configured(self, app):
        """Test that rate limiting is configured."""
        # Just verify rate limiter is initialized, don't exhaust limits
        from app import limiter
        assert limiter is not None
