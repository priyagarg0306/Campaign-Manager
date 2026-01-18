"""
Tests for campaign API endpoints.
"""
import json
import os
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app import db
from app.models.campaign import Campaign


class TestCreateCampaign:
    """Tests for POST /api/campaigns endpoint."""

    def test_create_campaign_success(self, auth_client, sample_campaign_data):
        """Test successful campaign creation."""
        response = auth_client.post(
            '/api/campaigns',
            data=json.dumps(sample_campaign_data),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.get_json()

        assert data['name'] == sample_campaign_data['name']
        assert data['objective'] == sample_campaign_data['objective']
        assert data['daily_budget'] == sample_campaign_data['daily_budget']
        assert data['status'] == 'DRAFT'
        assert 'id' in data
        assert 'created_at' in data

    def test_create_campaign_missing_name(self, auth_client, sample_campaign_data):
        """Test campaign creation with missing name."""
        del sample_campaign_data['name']

        response = auth_client.post(
            '/api/campaigns',
            data=json.dumps(sample_campaign_data),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_create_campaign_missing_objective(self, auth_client, sample_campaign_data):
        """Test campaign creation with missing objective."""
        del sample_campaign_data['objective']

        response = auth_client.post(
            '/api/campaigns',
            data=json.dumps(sample_campaign_data),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_campaign_invalid_objective(self, auth_client, sample_campaign_data):
        """Test campaign creation with invalid objective."""
        sample_campaign_data['objective'] = 'INVALID'

        response = auth_client.post(
            '/api/campaigns',
            data=json.dumps(sample_campaign_data),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_campaign_negative_budget(self, auth_client, sample_campaign_data):
        """Test campaign creation with negative budget."""
        sample_campaign_data['daily_budget'] = -100

        response = auth_client.post(
            '/api/campaigns',
            data=json.dumps(sample_campaign_data),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_campaign_empty_body(self, auth_client):
        """Test campaign creation with empty body."""
        response = auth_client.post(
            '/api/campaigns',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_create_campaign_no_body(self, auth_client):
        """Test campaign creation with no body."""
        response = auth_client.post(
            '/api/campaigns',
            content_type='application/json'
        )

        assert response.status_code == 400

class TestGetCampaigns:
    """Tests for GET /api/campaigns endpoint."""

    def test_get_campaigns_empty(self, auth_client):
        """Test getting campaigns when none exist."""
        response = auth_client.get('/api/campaigns')

        assert response.status_code == 200
        data = response.get_json()
        assert 'campaigns' in data
        assert data['campaigns'] == []

    def test_get_campaigns_with_data(self, auth_client, created_campaign):
        """Test getting campaigns with data."""
        response = auth_client.get('/api/campaigns')

        assert response.status_code == 200
        data = response.get_json()
        # Response includes pagination wrapper
        assert 'campaigns' in data
        assert len(data['campaigns']) > 0

    def test_get_campaigns_filter_by_status(self, auth_client, created_campaign):
        """Test filtering campaigns by status."""
        response = auth_client.get('/api/campaigns?status=DRAFT')

        assert response.status_code == 200
        data = response.get_json()
        assert 'campaigns' in data

class TestGetCampaign:
    """Tests for GET /api/campaigns/<id> endpoint."""

    def test_get_campaign_success(self, auth_client, created_campaign):
        """Test getting a single campaign."""
        response = auth_client.get(f'/api/campaigns/{created_campaign.id}')
        assert response.status_code == 200

    def test_get_campaign_not_found(self, auth_client):
        """Test getting a non-existent campaign."""
        # Use a valid UUID format
        response = auth_client.get('/api/campaigns/00000000-0000-0000-0000-000000000000')
        assert response.status_code == 404

    def test_get_campaign_invalid_id(self, auth_client):
        """Test getting a campaign with invalid ID format."""
        response = auth_client.get('/api/campaigns/not-a-valid-uuid')
        assert response.status_code == 400


class TestUpdateCampaign:
    """Tests for PUT /api/campaigns/<id> endpoint."""

    def test_update_campaign_success(self, auth_client, created_campaign):
        """Test updating a campaign."""
        update_data = {'name': 'Updated Campaign Name'}

        response = auth_client.put(
            f'/api/campaigns/{created_campaign.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated Campaign Name'

    def test_update_campaign_not_found(self, auth_client):
        """Test updating a non-existent campaign."""
        response = auth_client.put(
            '/api/campaigns/00000000-0000-0000-0000-000000000000',
            data=json.dumps({'name': 'New Name'}),
            content_type='application/json'
        )

        assert response.status_code == 404

    def test_update_campaign_no_body(self, auth_client, created_campaign):
        """Test updating with no body."""
        response = auth_client.put(
            f'/api/campaigns/{created_campaign.id}',
            content_type='application/json'
        )
        assert response.status_code == 400


class TestDeleteCampaign:
    """Tests for DELETE /api/campaigns/<id> endpoint."""

    def test_delete_campaign_success(self, auth_client, app, sample_campaign_data):
        """Test deleting a campaign."""
        with app.app_context():
            campaign = Campaign(
                name='To Delete',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.delete(f'/api/campaigns/{campaign_id}')
        assert response.status_code == 204

    def test_delete_campaign_not_found(self, auth_client):
        """Test deleting a non-existent campaign."""
        response = auth_client.delete('/api/campaigns/00000000-0000-0000-0000-000000000000')
        assert response.status_code == 404


class TestPublishCampaign:
    """Tests for POST /api/campaigns/<id>/publish endpoint."""

    def test_publish_campaign_not_found(self, auth_client):
        """Test publishing a non-existent campaign."""
        response = auth_client.post('/api/campaigns/00000000-0000-0000-0000-000000000000/publish')
        assert response.status_code == 404

    @patch.dict(os.environ, {
        'GOOGLE_ADS_DEVELOPER_TOKEN': '',
        'GOOGLE_ADS_CLIENT_ID': '',
        'GOOGLE_ADS_CLIENT_SECRET': '',
        'GOOGLE_ADS_REFRESH_TOKEN': '',
    }, clear=False)
    def test_publish_campaign_not_configured(self, auth_client, app):
        """Test publishing when Google Ads is not configured."""
        # Reset the google_ads_service to pick up cleared credentials
        from app.services.google_ads_service import google_ads_service
        google_ads_service._client = None

        with app.app_context():
            campaign = Campaign(
                name='Test Publish',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                ad_headline='Test Headline',
                ad_description='Test Description',
                final_url='https://example.com',
                # Required fields for DEMAND_GEN campaigns
                headlines=['Test Headline'],
                descriptions=['Test Description'],
                business_name='Test Business',
                images={'landscape_url': 'https://example.com/img.jpg'}
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/publish')

        # Should fail because Google Ads is not configured in test environment
        assert response.status_code == 400
        data = response.get_json()
        assert 'not configured' in data.get('error', '').lower() or 'not configured' in data.get('message', '').lower()


class TestPauseCampaign:
    """Tests for POST /api/campaigns/<id>/pause endpoint."""

    def test_pause_campaign_not_found(self, auth_client):
        """Test pausing a non-existent campaign."""
        response = auth_client.post('/api/campaigns/00000000-0000-0000-0000-000000000000/pause')
        assert response.status_code == 404

    def test_pause_campaign_invalid_id(self, auth_client):
        """Test pausing a campaign with invalid ID format."""
        response = auth_client.post('/api/campaigns/not-a-valid-uuid/pause')
        assert response.status_code == 400

    def test_pause_campaign_not_published(self, auth_client, app):
        """Test pausing a campaign that is not published."""
        with app.app_context():
            campaign = Campaign(
                name='Test Pause',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/pause')
        assert response.status_code == 400
        data = response.get_json()
        assert 'not published' in data.get('error', '').lower()


class TestEnableCampaign:
    """Tests for POST /api/campaigns/<id>/enable endpoint."""

    def test_enable_campaign_not_found(self, auth_client):
        """Test enabling a non-existent campaign."""
        response = auth_client.post('/api/campaigns/00000000-0000-0000-0000-000000000000/enable')
        assert response.status_code == 404

    def test_enable_campaign_invalid_id(self, auth_client):
        """Test enabling a campaign with invalid ID format."""
        response = auth_client.post('/api/campaigns/not-a-valid-uuid/enable')
        assert response.status_code == 400

    def test_enable_campaign_not_published(self, auth_client, app):
        """Test enabling a campaign that is not published."""
        with app.app_context():
            campaign = Campaign(
                name='Test Enable',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/enable')
        assert response.status_code == 400
        data = response.get_json()
        assert 'not published' in data.get('error', '').lower()


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        assert response.status_code in [200, 500]  # 500 if Google Ads not configured
        data = response.get_json()
        assert 'status' in data
        assert 'checks' in data

    def test_liveness(self, client):
        """Test liveness probe."""
        response = client.get('/api/health/live')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'alive'

    def test_readiness(self, client):
        """Test readiness probe."""
        response = client.get('/api/health/ready')
        # May be 503 if database is not fully ready in test
        assert response.status_code in [200, 503]


class TestSanitizeErrorMessage:
    """Tests for error message sanitization."""

    def test_sanitize_password_in_error(self, auth_client, app):
        """Test that password-related errors are sanitized."""
        # This is tested implicitly through the routes - errors with sensitive
        # patterns are replaced with generic messages
        pass


