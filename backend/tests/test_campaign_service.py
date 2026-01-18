"""
Tests for CampaignService.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from app import db
from app.models.campaign import Campaign
from app.services.campaign_service import CampaignService


class TestCampaignServiceCreate:
    """Tests for CampaignService.create_campaign."""

    def test_create_campaign_success(self, app):
        """Test successful campaign creation."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                'objective': 'SALES',
                'daily_budget': 10000000,
                'start_date': date.today() + timedelta(days=1)
            }

            campaign = CampaignService.create_campaign(data)

            assert campaign.id is not None
            assert campaign.name == 'Test Campaign'
            assert campaign.objective == 'SALES'
            assert campaign.status == 'DRAFT'
            assert campaign.campaign_type == 'DEMAND_GEN'

    def test_create_campaign_with_all_fields(self, app):
        """Test campaign creation with all optional fields."""
        with app.app_context():
            data = {
                'name': 'Full Campaign',
                'objective': 'LEADS',
                'campaign_type': 'DISPLAY',
                'daily_budget': 5000000,
                'start_date': date.today() + timedelta(days=1),
                'end_date': date.today() + timedelta(days=30),
                'ad_group_name': 'My Ad Group',
                'ad_headline': 'Great Headline',
                'ad_description': 'Amazing description',
                'asset_url': 'https://example.com/image.jpg',
                'final_url': 'https://example.com'
            }

            campaign = CampaignService.create_campaign(data)

            assert campaign.campaign_type == 'DISPLAY'
            assert campaign.ad_group_name == 'My Ad Group'
            assert campaign.ad_headline == 'Great Headline'

    def test_create_campaign_missing_required_field(self, app):
        """Test campaign creation with missing required field."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                # missing objective, daily_budget, start_date
            }

            with pytest.raises(ValueError) as excinfo:
                CampaignService.create_campaign(data)

            assert 'Missing required field' in str(excinfo.value)

    def test_create_campaign_string_date(self, app):
        """Test campaign creation with string date."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                'objective': 'SALES',
                'daily_budget': 10000000,
                'start_date': (date.today() + timedelta(days=1)).isoformat()
            }

            campaign = CampaignService.create_campaign(data)
            assert campaign.start_date == date.today() + timedelta(days=1)


class TestCampaignServiceRead:
    """Tests for CampaignService read operations."""

    def test_get_all_campaigns(self, app, created_campaign):
        """Test getting all campaigns."""
        with app.app_context():
            campaigns = CampaignService.get_all_campaigns()
            assert len(campaigns) >= 1

    def test_get_campaign_by_id(self, app, created_campaign):
        """Test getting campaign by ID."""
        with app.app_context():
            campaign = CampaignService.get_campaign_by_id(created_campaign.id)
            assert campaign is not None
            assert campaign.id == created_campaign.id

    def test_get_campaign_by_id_not_found(self, app):
        """Test getting non-existent campaign."""
        with app.app_context():
            campaign = CampaignService.get_campaign_by_id('non-existent')
            assert campaign is None

    def test_get_campaigns_by_status(self, app, created_campaign):
        """Test getting campaigns by status."""
        with app.app_context():
            campaigns = CampaignService.get_campaigns_by_status('DRAFT')
            assert any(c.id == created_campaign.id for c in campaigns)

            campaigns = CampaignService.get_campaigns_by_status('PUBLISHED')
            assert not any(c.id == created_campaign.id for c in campaigns)


class TestCampaignServiceUpdate:
    """Tests for CampaignService update operations."""

    def test_update_campaign_success(self, app, created_campaign):
        """Test successful campaign update."""
        with app.app_context():
            data = {'name': 'Updated Name'}
            campaign = CampaignService.update_campaign(created_campaign.id, data)

            assert campaign is not None
            assert campaign.name == 'Updated Name'

    def test_update_campaign_not_found(self, app):
        """Test updating non-existent campaign."""
        with app.app_context():
            result = CampaignService.update_campaign('non-existent', {'name': 'New'})
            assert result is None

    def test_update_campaign_status(self, app, created_campaign):
        """Test updating campaign status."""
        with app.app_context():
            campaign = CampaignService.update_campaign_status(
                created_campaign.id,
                'PUBLISHED',
                'google-123',
                'adgroup-456'
            )

            assert campaign.status == 'PUBLISHED'
            assert campaign.google_campaign_id == 'google-123'
            assert campaign.google_ad_group_id == 'adgroup-456'


class TestCampaignServiceDelete:
    """Tests for CampaignService delete operations."""

    def test_delete_campaign_success(self, app):
        """Test successful campaign deletion."""
        with app.app_context():
            # Create a campaign to delete
            campaign = Campaign(
                name='To Delete',
                objective='SALES',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

            result = CampaignService.delete_campaign(campaign_id)
            assert result is True

            # Verify it's deleted
            deleted = CampaignService.get_campaign_by_id(campaign_id)
            assert deleted is None

    def test_delete_campaign_not_found(self, app):
        """Test deleting non-existent campaign."""
        with app.app_context():
            result = CampaignService.delete_campaign('non-existent')
            assert result is False

    def test_delete_published_campaign(self, app):
        """Test deleting a published campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Published',
                objective='SALES',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED',
                google_campaign_id='123456'
            )
            db.session.add(campaign)
            db.session.commit()

            with pytest.raises(ValueError) as excinfo:
                CampaignService.delete_campaign(campaign.id)

            assert 'published to Google Ads' in str(excinfo.value)


class TestCampaignServiceValidation:
    """Tests for CampaignService validation."""

    def test_validate_for_publish_success(self, app, created_campaign):
        """Test validation passes for valid campaign."""
        with app.app_context():
            errors = CampaignService.validate_for_publish(created_campaign)
            assert len(errors) == 0

    def test_validate_for_publish_missing_name(self, app):
        """Test validation fails for missing name."""
        with app.app_context():
            campaign = Campaign(
                objective='SALES',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )

            errors = CampaignService.validate_for_publish(campaign)
            assert 'Campaign name is required' in errors

    def test_validate_for_publish_already_published(self, app):
        """Test validation fails for already published campaign."""
        with app.app_context():
            campaign = Campaign(
                name='Published',
                objective='SALES',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED'
            )

            errors = CampaignService.validate_for_publish(campaign)
            assert 'Campaign is already published' in errors

    def test_validate_for_publish_past_start_date(self, app):
        """Test validation fails for past start date."""
        with app.app_context():
            campaign = Campaign(
                name='Past Campaign',
                objective='SALES',
                daily_budget=1000000,
                start_date=date.today() - timedelta(days=1),
                status='DRAFT'
            )

            errors = CampaignService.validate_for_publish(campaign)
            assert 'Start date cannot be in the past' in errors
