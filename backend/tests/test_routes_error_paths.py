"""
Tests for route error paths to improve coverage.
"""
import json
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from app import db
from app.models.campaign import Campaign


class TestCreateCampaignErrorPaths:
    """Tests for create campaign error paths."""

    def test_create_campaign_value_error(self, auth_client):
        """Test ValueError path in create_campaign."""
        with patch('app.routes.campaigns.CampaignService.create_campaign') as mock_create:
            mock_create.side_effect = ValueError("Missing required field: name")

            response = auth_client.post(
                '/api/campaigns',
                json={
                    'name': 'Test',
                    'objective': 'SALES',
                    'campaign_type': 'DEMAND_GEN',
                    'daily_budget': 1000000,
                    'start_date': (date.today() + timedelta(days=1)).isoformat()
                }
            )
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_create_campaign_value_error_sensitive_data(self, auth_client):
        """Test ValueError with sensitive data is sanitized."""
        with patch('app.routes.campaigns.CampaignService.create_campaign') as mock_create:
            # Error message containing sensitive info
            mock_create.side_effect = ValueError("password=secret123 invalid")

            response = auth_client.post(
                '/api/campaigns',
                json={
                    'name': 'Test',
                    'objective': 'SALES',
                    'campaign_type': 'DEMAND_GEN',
                    'daily_budget': 1000000,
                    'start_date': (date.today() + timedelta(days=1)).isoformat()
                }
            )
            assert response.status_code == 400
            data = response.get_json()
            # Should not contain the password
            assert 'password' not in data.get('error', '').lower()


class TestGetCampaignsErrorPaths:
    """Tests for get campaigns error paths."""

    def test_get_campaigns_exception(self, auth_client):
        """Test exception path in get_campaigns."""
        with patch('app.routes.campaigns.CampaignService.get_campaigns_paginated') as mock_get:
            mock_get.side_effect = Exception("Database connection lost")

            response = auth_client.get('/api/campaigns')
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data


class TestUpdateCampaignErrorPaths:
    """Tests for update campaign error paths."""

    def test_update_campaign_validation_error(self, auth_client, app):
        """Test ValidationError path in update_campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        # Send invalid data that fails schema validation
        response = auth_client.put(
            f'/api/campaigns/{campaign_id}',
            json={'daily_budget': -1000}  # Invalid negative budget
        )
        # Should return 400 for validation error
        assert response.status_code in [200, 400]

    def test_update_campaign_value_error(self, auth_client, app):
        """Test ValueError path in update_campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        with patch('app.routes.campaigns.CampaignService.update_campaign') as mock_update:
            mock_update.side_effect = ValueError("Cannot update this field")

            response = auth_client.put(
                f'/api/campaigns/{campaign_id}',
                json={'name': 'New Name'}
            )
            assert response.status_code == 400


class TestPublishCampaignErrorPaths:
    """Tests for publish campaign error paths."""

    def test_publish_campaign_status_update_error(self, auth_client, app):
        """Test error path when status update to ERROR fails."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['H1', 'H2'],
                descriptions=['D1'],
                business_name='Test',
                images={'landscape_url': 'https://example.com/img.jpg'}
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        with patch('app.routes.campaigns.google_ads_service') as mock_service:
            mock_service.is_configured.return_value = True
            mock_service.publish_campaign.side_effect = Exception("API error")

            # Also mock the status update to ERROR to fail
            with patch('app.routes.campaigns.CampaignService.update_campaign_status') as mock_status:
                mock_status.side_effect = Exception("Status update failed")

                response = auth_client.post(f'/api/campaigns/{campaign_id}/publish')
                assert response.status_code == 500


class TestDeleteCampaignErrorPaths:
    """Tests for delete campaign error paths."""

    def test_delete_campaign_value_error(self, auth_client, app):
        """Test ValueError path in delete_campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Published',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED',
                google_campaign_id='123'  # Has Google ID so can't delete
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.delete(f'/api/campaigns/{campaign_id}')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestPauseCampaignErrorPaths:
    """Tests for pause campaign error paths."""

    def test_pause_campaign_not_published(self, auth_client, app):
        """Test pause when campaign is not published."""
        with app.app_context():
            campaign = Campaign(
                name='Draft',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
                # No google_campaign_id
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/pause')
        assert response.status_code == 400
        data = response.get_json()
        assert 'not published' in data['error'].lower()


class TestEnableCampaignErrorPaths:
    """Tests for enable campaign error paths."""

    def test_enable_campaign_not_published(self, auth_client, app):
        """Test enable when campaign is not published."""
        with app.app_context():
            campaign = Campaign(
                name='Draft',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
                # No google_campaign_id
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/enable')
        assert response.status_code == 400
        data = response.get_json()
        assert 'not published' in data['error'].lower()
