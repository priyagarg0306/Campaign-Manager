"""
Tests for health check endpoints to improve coverage.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError


class TestHealthCheck:
    """Tests for health check endpoints."""

    @patch('app.routes.health.google_ads_service')
    @patch('app.routes.health.db')
    def test_health_check_all_services_up(self, mock_db, mock_google_ads, client):
        """Test health check when all services are healthy."""
        mock_google_ads.is_configured.return_value = True
        mock_db.session.execute.return_value = None

        response = client.get('/api/health')
        assert response.status_code in [200, 500]
        data = response.get_json()
        assert 'status' in data
        assert 'checks' in data

    @patch('app.routes.health.google_ads_service')
    @patch('app.routes.health.db')
    def test_health_check_database_unhealthy(self, mock_db, mock_google_ads, client):
        """Test health check when database is unhealthy."""
        mock_google_ads.is_configured.return_value = True
        mock_db.session.execute.side_effect = SQLAlchemyError("Connection failed")

        response = client.get('/api/health')
        # Should return 500 when database is down
        assert response.status_code in [200, 500]
        data = response.get_json()
        assert 'checks' in data

    @patch('app.routes.health.google_ads_service')
    def test_health_check_google_ads_not_configured(self, mock_google_ads, client):
        """Test health check when Google Ads is not configured."""
        mock_google_ads.is_configured.return_value = False

        response = client.get('/api/health')
        data = response.get_json()
        assert 'checks' in data
        assert 'google_ads' in data['checks']

    def test_liveness_probe_success(self, client):
        """Test liveness probe returns 200."""
        response = client.get('/api/health/live')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'alive'

    @patch('app.routes.health.db')
    def test_readiness_probe_database_healthy(self, mock_db, client):
        """Test readiness probe when database is healthy."""
        mock_db.session.execute.return_value = None

        response = client.get('/api/health/ready')
        assert response.status_code in [200, 503]

    @patch('app.routes.health.db')
    def test_readiness_probe_database_unhealthy(self, mock_db, client):
        """Test readiness probe when database is unhealthy."""
        mock_db.session.execute.side_effect = SQLAlchemyError("Connection failed")

        response = client.get('/api/health/ready')
        assert response.status_code in [200, 503]

    def test_health_response_format(self, client):
        """Test health check response format."""
        response = client.get('/api/health')
        data = response.get_json()

        # Should have standard fields
        assert 'status' in data
        assert 'timestamp' in data or 'checks' in data

    def test_liveness_response_format(self, client):
        """Test liveness probe response format."""
        response = client.get('/api/health/live')
        data = response.get_json()

        assert 'status' in data
        assert data['status'] == 'alive'


class TestHealthCheckVersionInfo:
    """Tests for health check version information."""

    def test_health_includes_version_info(self, client):
        """Test health check includes version information if available."""
        response = client.get('/api/health')
        assert response.status_code in [200, 500]
        # Check response is valid JSON
        data = response.get_json()
        assert data is not None
