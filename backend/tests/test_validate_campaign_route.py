"""
Tests for campaign validation endpoint.
"""
import json
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from app import db
from app.models.campaign import Campaign


class TestValidateCampaignEndpoint:
    """Tests for /api/campaigns/<id>/validate endpoint."""

    def test_validate_campaign_invalid_uuid(self, auth_client):
        """Test validation with invalid UUID format."""
        response = auth_client.post('/api/campaigns/invalid-id/validate')
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid campaign ID format' in data['error']

    def test_validate_campaign_not_found(self, auth_client):
        """Test validation for non-existent campaign."""
        response = auth_client.post('/api/campaigns/00000000-0000-0000-0000-000000000001/validate')
        assert response.status_code == 404
        data = response.get_json()
        assert 'Campaign not found' in data['error']

    def test_validate_demand_gen_campaign_valid(self, auth_client, app):
        """Test validation for valid DEMAND_GEN campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Valid Demand Gen',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline 1', 'Test Headline 2'],
                descriptions=['Test description that is long enough for requirements'],
                business_name='Test Business',
                images={'landscape_url': 'https://example.com/img.jpg'}
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'campaign_type' in data
        assert data['campaign_type'] == 'DEMAND_GEN'

    def test_validate_search_campaign_valid(self, auth_client, app):
        """Test validation for valid SEARCH campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Valid Search',
                objective='SALES',
                campaign_type='SEARCH',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Headline 1', 'Headline 2', 'Headline 3'],
                descriptions=['Description 1', 'Description 2'],
                keywords=['keyword1', 'keyword2']
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert 'requirements' in data

    def test_validate_video_campaign_warning(self, auth_client, app):
        """Test validation for VIDEO campaign shows warning about API creation."""
        with app.app_context():
            campaign = Campaign(
                name='Video Campaign',
                objective='SALES',
                campaign_type='VIDEO',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                video_url='https://youtube.com/watch?v=test',
                headlines=['Test Headline'],
                descriptions=['Test Description']
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        # VIDEO campaigns should have a warning about API creation
        assert 'warnings' in data or data['valid'] is False

    def test_validate_shopping_campaign_missing_merchant_id(self, auth_client, app):
        """Test validation for SHOPPING campaign without merchant ID."""
        with app.app_context():
            campaign = Campaign(
                name='Shopping Campaign',
                objective='SALES',
                campaign_type='SHOPPING',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is False
        # Should have error about missing merchant center ID
        assert len(data['errors']) > 0

    def test_validate_campaign_missing_required_fields(self, auth_client, app):
        """Test validation for campaign with missing required fields."""
        with app.app_context():
            campaign = Campaign(
                name='Incomplete Campaign',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
                # Missing: headlines, descriptions, business_name, images, final_url
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        assert data['valid'] is False
        assert len(data['errors']) > 0

    def test_validate_performance_max_campaign(self, auth_client, app):
        """Test validation for PERFORMANCE_MAX campaign."""
        with app.app_context():
            campaign = Campaign(
                name='PMax Campaign',
                objective='SALES',
                campaign_type='PERFORMANCE_MAX',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['H1', 'H2', 'H3'],
                long_headline='This is a long headline for Performance Max',
                descriptions=['Short desc', 'Longer description here'],
                business_name='Test Business',
                images={'landscape_url': 'https://example.com/img.jpg'}
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data
        assert data['campaign_type'] == 'PERFORMANCE_MAX'

    def test_validate_display_campaign(self, auth_client, app):
        """Test validation for DISPLAY campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Display Campaign',
                objective='SALES',
                campaign_type='DISPLAY',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['H1', 'H2', 'H3'],
                long_headline='Long headline for display ads',
                descriptions=['Short desc', 'Description 2'],
                images={'landscape_url': 'https://example.com/img.jpg'}
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        assert 'valid' in data

    def test_validate_campaign_response_has_requirements(self, auth_client, app):
        """Test that validation response includes requirements info."""
        with app.app_context():
            campaign = Campaign(
                name='Test Campaign',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        assert 'requirements' in data
        assert 'headlines' in data['requirements']
        assert 'descriptions' in data['requirements']

    def test_validate_campaign_removes_duplicate_errors(self, auth_client, app):
        """Test that duplicate errors are removed."""
        with app.app_context():
            campaign = Campaign(
                name='Test Campaign',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        # Check that there are no duplicate errors
        errors = data['errors']
        assert len(errors) == len(set(errors)), "Found duplicate errors in response"

    def test_validate_campaign_database_error(self, auth_client):
        """Test validation when database error occurs."""
        with patch('app.routes.campaigns.CampaignService.get_campaign_by_id') as mock_get:
            mock_get.side_effect = Exception("Database error")

            response = auth_client.post('/api/campaigns/00000000-0000-0000-0000-000000000001/validate')
            assert response.status_code == 500


class TestValidateCampaignErrorCodes:
    """Test error codes in validation responses."""

    def test_validation_error_has_code(self, auth_client, app):
        """Test that validation errors include error code."""
        with app.app_context():
            campaign = Campaign(
                name='Incomplete Campaign',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        if not data['valid']:
            assert 'code' in data
            assert data['code'] == 'VALIDATION_ERROR'

    def test_valid_campaign_has_no_code(self, auth_client, app):
        """Test that valid campaign has null error code."""
        with app.app_context():
            campaign = Campaign(
                name='Complete Campaign',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline 1', 'Test Headline 2'],
                descriptions=['Test description long enough'],
                business_name='Test Business',
                images={'landscape_url': 'https://example.com/img.jpg'}
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = auth_client.post(f'/api/campaigns/{campaign_id}/validate')
        assert response.status_code == 200
        data = response.get_json()
        # If valid, code should be null
        if data.get('valid'):
            assert data.get('code') is None
