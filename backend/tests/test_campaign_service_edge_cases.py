"""
Tests for campaign service edge cases and error handling.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.campaign import Campaign, CampaignStatus
from app.services.campaign_service import CampaignService


class TestCampaignServiceCreation:
    """Tests for campaign creation edge cases."""

    def test_create_campaign_missing_name(self, app):
        """Test creation fails when name is missing."""
        with app.app_context():
            data = {
                'objective': 'SALES',
                'daily_budget': 1000000,
                'start_date': date.today() + timedelta(days=1)
            }
            with pytest.raises(ValueError) as exc_info:
                CampaignService.create_campaign(data)
            assert 'name' in str(exc_info.value)

    def test_create_campaign_missing_objective(self, app):
        """Test creation fails when objective is missing."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                'daily_budget': 1000000,
                'start_date': date.today() + timedelta(days=1)
            }
            with pytest.raises(ValueError) as exc_info:
                CampaignService.create_campaign(data)
            assert 'objective' in str(exc_info.value)

    def test_create_campaign_missing_daily_budget(self, app):
        """Test creation fails when daily_budget is missing."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                'objective': 'SALES',
                'start_date': date.today() + timedelta(days=1)
            }
            with pytest.raises(ValueError) as exc_info:
                CampaignService.create_campaign(data)
            assert 'daily_budget' in str(exc_info.value)

    def test_create_campaign_missing_start_date(self, app):
        """Test creation fails when start_date is missing."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                'objective': 'SALES',
                'daily_budget': 1000000
            }
            with pytest.raises(ValueError) as exc_info:
                CampaignService.create_campaign(data)
            assert 'start_date' in str(exc_info.value)

    def test_create_campaign_with_string_dates(self, app):
        """Test creation with string dates (ISO format)."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                'objective': 'SALES',
                'daily_budget': 1000000,
                'start_date': (date.today() + timedelta(days=1)).isoformat(),
                'end_date': (date.today() + timedelta(days=30)).isoformat(),
                'campaign_type': 'DEMAND_GEN'
            }
            campaign = CampaignService.create_campaign(data)
            assert campaign.id is not None
            assert campaign.start_date is not None
            assert campaign.end_date is not None

    def test_create_campaign_database_error(self, app):
        """Test creation handles database errors properly."""
        with app.app_context():
            data = {
                'name': 'Test Campaign',
                'objective': 'SALES',
                'daily_budget': 1000000,
                'start_date': date.today() + timedelta(days=1)
            }
            with patch.object(db.session, 'commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError("Database error")
                with pytest.raises(SQLAlchemyError):
                    CampaignService.create_campaign(data)

    def test_create_campaign_with_all_fields(self, app):
        """Test creation with all possible fields."""
        with app.app_context():
            data = {
                'name': 'Complete Campaign',
                'owner_id': 'owner-123',
                'objective': 'SALES',
                'campaign_type': 'DEMAND_GEN',
                'daily_budget': 1000000,
                'start_date': date.today() + timedelta(days=1),
                'end_date': date.today() + timedelta(days=30),
                'bidding_strategy': 'maximize_conversions',
                'target_cpa': 500000,
                'target_roas': 2.5,
                'ad_group_name': 'Test Group',
                'ad_headline': 'Headline',
                'ad_description': 'Description',
                'asset_url': 'https://example.com/asset.jpg',
                'final_url': 'https://example.com',
                'headlines': ['H1', 'H2'],
                'long_headline': 'Long headline',
                'descriptions': ['D1', 'D2'],
                'business_name': 'Test Business',
                'images': {'landscape_url': 'https://example.com/img.jpg'},
                'keywords': ['keyword1', 'keyword2'],
                'video_url': 'https://youtube.com/watch?v=test',
                'merchant_center_id': '123456789'
            }
            campaign = CampaignService.create_campaign(data)
            assert campaign.id is not None
            assert campaign.owner_id == 'owner-123'
            assert campaign.bidding_strategy == 'maximize_conversions'
            assert campaign.merchant_center_id == '123456789'


class TestCampaignServicePagination:
    """Tests for campaign pagination edge cases."""

    def test_get_campaigns_paginated_with_owner_filter(self, app):
        """Test pagination with owner filter."""
        with app.app_context():
            # Create campaigns with different owners
            for i, owner in enumerate(['owner1', 'owner2', 'owner1']):
                campaign = Campaign(
                    name=f'Campaign {i}',
                    owner_id=owner,
                    objective='SALES',
                    campaign_type='DEMAND_GEN',
                    daily_budget=1000000,
                    start_date=date.today() + timedelta(days=1),
                    status='DRAFT'
                )
                db.session.add(campaign)
            db.session.commit()

            result = CampaignService.get_campaigns_paginated(owner_id='owner1')
            # Should only return owner1's campaigns
            for campaign in result['campaigns']:
                assert campaign.owner_id == 'owner1'

    def test_get_campaigns_paginated_negative_page(self, app):
        """Test pagination with negative page number (should default to 1)."""
        with app.app_context():
            result = CampaignService.get_campaigns_paginated(page=-1)
            assert result['page'] == 1

    def test_get_campaigns_paginated_zero_per_page(self, app):
        """Test pagination with zero per_page (should default to 1)."""
        with app.app_context():
            result = CampaignService.get_campaigns_paginated(per_page=0)
            assert result['per_page'] == 1

    def test_get_campaigns_paginated_excessive_per_page(self, app):
        """Test pagination caps per_page at 100."""
        with app.app_context():
            result = CampaignService.get_campaigns_paginated(per_page=1000)
            assert result['per_page'] == 100


class TestCampaignServiceUpdate:
    """Tests for campaign update edge cases."""

    def test_update_campaign_with_string_dates(self, app):
        """Test update with string dates."""
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

            update_data = {
                'start_date': (date.today() + timedelta(days=5)).isoformat(),
                'end_date': (date.today() + timedelta(days=35)).isoformat()
            }
            updated = CampaignService.update_campaign(campaign_id, update_data)
            assert updated.start_date == date.today() + timedelta(days=5)
            assert updated.end_date == date.today() + timedelta(days=35)

    def test_update_campaign_published_restricted_fields(self, app):
        """Test that restricted fields cannot be updated on published campaigns."""
        with app.app_context():
            campaign = Campaign(
                name='Published',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

            # Try to update objective (restricted)
            with pytest.raises(ValueError) as exc_info:
                CampaignService.update_campaign(campaign_id, {'objective': 'LEADS'})
            assert 'objective' in str(exc_info.value)

    def test_update_campaign_published_campaign_type_restricted(self, app):
        """Test that campaign_type cannot be changed on published campaigns."""
        with app.app_context():
            campaign = Campaign(
                name='Published',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

            with pytest.raises(ValueError) as exc_info:
                CampaignService.update_campaign(campaign_id, {'campaign_type': 'SEARCH'})
            assert 'campaign_type' in str(exc_info.value)

    def test_update_campaign_published_start_date_restricted(self, app):
        """Test that start_date cannot be changed on published campaigns."""
        with app.app_context():
            campaign = Campaign(
                name='Published',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED'
            )
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

            with pytest.raises(ValueError) as exc_info:
                CampaignService.update_campaign(
                    campaign_id,
                    {'start_date': date.today() + timedelta(days=10)}
                )
            assert 'start_date' in str(exc_info.value)

    def test_update_campaign_with_preloaded_campaign(self, app):
        """Test update with pre-loaded campaign object."""
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

            # Update with pre-loaded campaign
            updated = CampaignService.update_campaign(
                campaign.id,
                {'name': 'Updated Name'},
                campaign=campaign
            )
            assert updated.name == 'Updated Name'

    def test_update_campaign_database_error(self, app):
        """Test update handles database errors."""
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

            with patch.object(db.session, 'commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError("Database error")
                with pytest.raises(SQLAlchemyError):
                    CampaignService.update_campaign(campaign_id, {'name': 'New Name'})


class TestCampaignServiceStatusUpdate:
    """Tests for campaign status update edge cases."""

    def test_update_status_not_found(self, app):
        """Test status update for non-existent campaign."""
        with app.app_context():
            result = CampaignService.update_campaign_status(
                '00000000-0000-0000-0000-000000000001',
                'PUBLISHED'
            )
            assert result is None

    def test_update_status_database_error(self, app):
        """Test status update handles database errors."""
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

            with patch.object(db.session, 'commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError("Database error")
                with pytest.raises(SQLAlchemyError):
                    CampaignService.update_campaign_status(campaign_id, 'PUBLISHED')


class TestCampaignServiceDelete:
    """Tests for campaign delete edge cases."""

    def test_delete_campaign_with_google_id(self, app):
        """Test that campaigns with Google IDs cannot be deleted."""
        with app.app_context():
            campaign = Campaign(
                name='Published',
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

            with pytest.raises(ValueError) as exc_info:
                CampaignService.delete_campaign(campaign_id)
            assert 'published' in str(exc_info.value).lower()

    def test_delete_campaign_with_preloaded_campaign(self, app):
        """Test delete with pre-loaded campaign object."""
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

            result = CampaignService.delete_campaign(campaign.id, campaign=campaign)
            assert result is True

    def test_delete_campaign_database_error(self, app):
        """Test delete handles database errors."""
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

            with patch.object(db.session, 'commit') as mock_commit:
                mock_commit.side_effect = SQLAlchemyError("Database error")
                with pytest.raises(SQLAlchemyError):
                    CampaignService.delete_campaign(campaign_id)


class TestCampaignServiceValidation:
    """Tests for campaign validation edge cases."""

    def test_validate_for_publish_missing_name(self, app):
        """Test validation catches missing name."""
        with app.app_context():
            campaign = Campaign(
                name='',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            errors = CampaignService.validate_for_publish(campaign)
            assert any('name' in e.lower() for e in errors)

    def test_validate_for_publish_missing_objective(self, app):
        """Test validation catches missing objective."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            errors = CampaignService.validate_for_publish(campaign)
            assert any('objective' in e.lower() for e in errors)

    def test_validate_for_publish_invalid_budget(self, app):
        """Test validation catches invalid budget."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=0,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT'
            )
            errors = CampaignService.validate_for_publish(campaign)
            assert any('budget' in e.lower() for e in errors)

    def test_validate_for_publish_past_start_date(self, app):
        """Test validation catches past start date."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() - timedelta(days=1),
                status='DRAFT'
            )
            errors = CampaignService.validate_for_publish(campaign)
            assert any('past' in e.lower() for e in errors)

    def test_validate_for_publish_end_before_start(self, app):
        """Test validation catches end date before start date."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=5),
                status='DRAFT'
            )
            errors = CampaignService.validate_for_publish(campaign)
            assert any('end date' in e.lower() for e in errors)

    def test_validate_for_publish_already_published(self, app):
        """Test validation catches already published campaigns."""
        with app.app_context():
            campaign = Campaign(
                name='Test',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='PUBLISHED'
            )
            errors = CampaignService.validate_for_publish(campaign)
            assert any('already published' in e.lower() for e in errors)


class TestCampaignServiceGetByStatus:
    """Tests for getting campaigns by status."""

    def test_get_campaigns_by_status(self, app):
        """Test getting campaigns filtered by status."""
        with app.app_context():
            # Create campaigns with different statuses
            for status in ['DRAFT', 'PUBLISHED', 'DRAFT']:
                campaign = Campaign(
                    name=f'Campaign {status}',
                    objective='SALES',
                    campaign_type='DEMAND_GEN',
                    daily_budget=1000000,
                    start_date=date.today() + timedelta(days=1),
                    status=status
                )
                db.session.add(campaign)
            db.session.commit()

            drafts = CampaignService.get_campaigns_by_status('DRAFT')
            assert len(drafts) >= 2
            for c in drafts:
                assert c.status == 'DRAFT'


class TestCampaignServiceGetAll:
    """Tests for getting all campaigns."""

    def test_get_all_campaigns_with_custom_limit(self, app):
        """Test getting all campaigns with custom limit."""
        with app.app_context():
            for i in range(5):
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

            campaigns = CampaignService.get_all_campaigns(limit=3)
            assert len(campaigns) <= 3
