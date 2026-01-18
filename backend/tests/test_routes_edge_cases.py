"""
Tests for route edge cases and error handling.
"""
import json
import pytest
from datetime import date, timedelta

from app import db
from app.models.campaign import Campaign
from app.routes.campaigns import sanitize_error_message


class TestSanitizeErrorMessage:
    """Tests for error message sanitization."""

    def test_sanitize_password_in_error(self):
        """Test that password errors are sanitized."""
        error = Exception("Connection failed: password=secret123")
        result = sanitize_error_message(error)
        assert 'secret' not in result.lower()
        assert result == 'An internal error occurred'

    def test_sanitize_token_in_error(self):
        """Test that token errors are sanitized."""
        error = Exception("Invalid token: abc123xyz")
        result = sanitize_error_message(error)
        assert result == 'An internal error occurred'

    def test_sanitize_connection_string(self):
        """Test that connection strings are sanitized."""
        error = Exception("Failed: postgresql://user:pass@localhost/db")
        result = sanitize_error_message(error)
        assert 'postgresql' not in result.lower()
        assert result == 'An internal error occurred'

    def test_safe_error_message(self):
        """Test that safe messages are not sanitized when include_details is True."""
        error = Exception("Campaign not found")
        result = sanitize_error_message(error, include_details=True)
        assert result == "Campaign not found"


class TestUpdateCampaignEdgeCases:
    """Tests for update campaign edge cases."""

    def test_update_campaign_invalid_id_format(self, client):
        """Test updating campaign with invalid ID format."""
        response = client.put(
            '/api/campaigns/not-a-valid-uuid',
            data=json.dumps({'name': 'New Name'}),
            content_type='application/json'
        )
        assert response.status_code == 400


class TestDeleteCampaignEdgeCases:
    """Tests for delete campaign edge cases."""

    def test_delete_campaign_invalid_id_format(self, client):
        """Test deleting campaign with invalid ID format."""
        response = client.delete('/api/campaigns/not-a-valid-uuid')
        assert response.status_code == 400


class TestPublishCampaignEdgeCases:
    """Tests for publish campaign edge cases."""

    def test_publish_campaign_invalid_id_format(self, client):
        """Test publishing campaign with invalid ID format."""
        response = client.post('/api/campaigns/not-a-valid-uuid/publish')
        assert response.status_code == 400

    def test_publish_already_published(self, client, app):
        """Test publishing an already published campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Published Campaign',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED',
                google_campaign_id='123456789'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = client.post(f'/api/campaigns/{campaign_id}/publish')
        assert response.status_code == 400
        data = response.get_json()
        assert 'already published' in data.get('error', '').lower()

    def test_publish_campaign_validation_error(self, client, app):
        """Test publishing campaign with validation errors."""
        with app.app_context():
            # Create campaign without required fields for publishing
            campaign = Campaign(
                name='',  # Empty name
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = client.post(f'/api/campaigns/{campaign_id}/publish')
        assert response.status_code == 400


class TestGetCampaignsEdgeCases:
    """Tests for get campaigns edge cases."""

    def test_get_campaigns_pagination(self, client, app):
        """Test getting campaigns with pagination."""
        with app.app_context():
            # Create multiple campaigns
            for i in range(25):
                campaign = Campaign(
                    name=f'Campaign {i}',
                    objective='SALES',
                    campaign_type='DEMAND_GEN',
                    daily_budget=1000000,
                    start_date=date.today() + timedelta(days=1),
                    status='DRAFT'
                )
                db.session.add(campaign)
            db.session.commit()

        response = client.get('/api/campaigns?page=1&per_page=10')
        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data
        assert data['pagination']['per_page'] == 10


class TestRouteValidation:
    """Tests for route input validation."""

    def test_is_valid_uuid_function(self):
        """Test the is_valid_uuid function directly."""
        from app.utils.validators import is_valid_uuid

        # Valid UUIDs
        assert is_valid_uuid('00000000-0000-0000-0000-000000000000') is True
        assert is_valid_uuid('a1b2c3d4-e5f6-4890-abcd-ef1234567890') is True

        # Invalid UUIDs
        assert is_valid_uuid('not-a-uuid') is False
        assert is_valid_uuid('') is False


class TestCreateCampaignValidation:
    """Tests for create campaign validation edge cases."""

    def test_create_campaign_with_special_characters(self, client, sample_campaign_data):
        """Test creating campaign with special characters in name."""
        sample_campaign_data['name'] = 'Test Campaign & Special!'
        response = client.post(
            '/api/campaigns',
            data=json.dumps(sample_campaign_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'Test Campaign & Special!'
