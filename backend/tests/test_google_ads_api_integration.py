"""
Integration tests for Google Ads API.

These tests require valid Google Ads API credentials to pass.
They test the actual API integration with Google Ads.

To run these tests:
1. Configure your Google Ads credentials in .env or environment variables
2. Run: pytest tests/test_google_ads_api_integration.py -v

Note: These tests create PAUSED campaigns in your test account.
"""
import os
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app import create_app, db
from app.models.campaign import Campaign
from app.services.google_ads_service import GoogleAdsService, google_ads_service


@pytest.fixture(scope='module')
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='module')
def service():
    """Get the Google Ads service instance."""
    return google_ads_service


class TestGoogleAdsApiConnection:
    """Tests for Google Ads API connection."""

    def test_service_is_configured(self, service):
        """Test that the service is properly configured."""
        assert service.is_configured() is True, "Google Ads service should be configured"

    def test_client_is_available(self, service):
        """Test that the Google Ads client is available."""
        assert service.client is not None, "Google Ads client should be available"

    def test_customer_id_is_set(self, service):
        """Test that customer ID is set."""
        assert service._customer_id is not None, "Customer ID should be set"
        assert len(service._customer_id) == 10, "Customer ID should be 10 digits"


class TestGoogleAdsApiDemandGenCampaign:
    """Integration tests for DEMAND_GEN campaign creation."""

    @pytest.fixture
    def demand_gen_campaign(self, app):
        """Create a DEMAND_GEN campaign for testing."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test DEMAND_GEN {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,  # $1 in micros
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=30),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline 1', 'Test Headline 2'],
                descriptions=['Test description for demand gen campaign'],
                business_name='Test Business',
                images={
                    'landscape_url': 'https://via.placeholder.com/1200x628.jpg',
                    'square_url': 'https://via.placeholder.com/1200x1200.jpg'
                },
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()
            yield campaign
            # Cleanup
            db.session.delete(campaign)
            db.session.commit()

    def test_publish_demand_gen_campaign(self, service, demand_gen_campaign, app):
        """Test publishing a DEMAND_GEN campaign to Google Ads."""
        with app.app_context():
            # Refresh campaign from database
            campaign = db.session.get(Campaign, demand_gen_campaign.id)

            result = service.publish_campaign(campaign)

            assert result['success'] is True, f"Campaign publish failed: {result.get('error')}"
            assert 'google_campaign_id' in result
            assert 'google_ad_group_id' in result
            assert result['google_campaign_id'] is not None


class TestGoogleAdsApiSearchCampaign:
    """Integration tests for SEARCH campaign creation."""

    @pytest.fixture
    def search_campaign(self, app):
        """Create a SEARCH campaign for testing."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test SEARCH {date.today().isoformat()}',
                objective='LEADS',
                campaign_type='SEARCH',
                daily_budget=1000000,  # $1 in micros
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=30),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Search Headline 1', 'Search Headline 2', 'Search Headline 3'],
                descriptions=['Search description 1', 'Search description 2'],
                keywords=['test keyword', 'example keyword', 'sample query'],
                bidding_strategy='maximize_clicks'
            )
            db.session.add(campaign)
            db.session.commit()
            yield campaign
            db.session.delete(campaign)
            db.session.commit()

    def test_publish_search_campaign(self, service, search_campaign, app):
        """Test publishing a SEARCH campaign to Google Ads."""
        with app.app_context():
            campaign = db.session.get(Campaign, search_campaign.id)

            result = service.publish_campaign(campaign)

            assert result['success'] is True, f"Campaign publish failed: {result.get('error')}"
            assert 'google_campaign_id' in result
            assert result['google_campaign_id'] is not None


class TestGoogleAdsApiDisplayCampaign:
    """Integration tests for DISPLAY campaign creation."""

    @pytest.fixture
    def display_campaign(self, app):
        """Create a DISPLAY campaign for testing."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test DISPLAY {date.today().isoformat()}',
                objective='WEBSITE_TRAFFIC',
                campaign_type='DISPLAY',
                daily_budget=1000000,  # $1 in micros
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=30),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Display Headline'],
                long_headline='This is a longer headline for display advertising',
                descriptions=['Display campaign description for testing'],
                business_name='Test Business',
                images={
                    'landscape_url': 'https://via.placeholder.com/1200x628.jpg',
                    'square_url': 'https://via.placeholder.com/1200x1200.jpg'
                },
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()
            yield campaign
            db.session.delete(campaign)
            db.session.commit()

    def test_publish_display_campaign(self, service, display_campaign, app):
        """Test publishing a DISPLAY campaign to Google Ads."""
        with app.app_context():
            campaign = db.session.get(Campaign, display_campaign.id)

            result = service.publish_campaign(campaign)

            assert result['success'] is True, f"Campaign publish failed: {result.get('error')}"
            assert 'google_campaign_id' in result


class TestGoogleAdsApiShoppingCampaign:
    """Integration tests for SHOPPING campaign creation."""

    @pytest.fixture
    def shopping_campaign(self, app):
        """Create a SHOPPING campaign for testing."""
        # Get merchant center ID from environment
        merchant_id = os.environ.get('GOOGLE_MERCHANT_CENTER_ID', '123456789')

        with app.app_context():
            campaign = Campaign(
                name=f'API Test SHOPPING {date.today().isoformat()}',
                objective='SALES',
                campaign_type='SHOPPING',
                daily_budget=1000000,  # $1 in micros
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=30),
                status='DRAFT',
                merchant_center_id=merchant_id,
                bidding_strategy='maximize_clicks'
            )
            db.session.add(campaign)
            db.session.commit()
            yield campaign
            db.session.delete(campaign)
            db.session.commit()

    def test_publish_shopping_campaign(self, service, shopping_campaign, app):
        """Test publishing a SHOPPING campaign to Google Ads."""
        with app.app_context():
            campaign = db.session.get(Campaign, shopping_campaign.id)

            result = service.publish_campaign(campaign)

            # Shopping campaigns may fail if Merchant Center is not linked
            if not result['success']:
                pytest.skip(f"Shopping campaign test skipped: {result.get('error')}")

            assert 'google_campaign_id' in result


class TestGoogleAdsApiPerformanceMaxCampaign:
    """Integration tests for PERFORMANCE_MAX campaign creation."""

    @pytest.fixture
    def pmax_campaign(self, app):
        """Create a PERFORMANCE_MAX campaign for testing."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test PMAX {date.today().isoformat()}',
                objective='SALES',
                campaign_type='PERFORMANCE_MAX',
                daily_budget=1000000,  # $1 in micros
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=30),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['PMax Headline 1', 'PMax Headline 2', 'PMax Headline 3'],
                long_headline='This is a longer headline for Performance Max campaign',
                descriptions=['Short desc', 'This is a longer description for Performance Max'],
                business_name='Test Business',
                images={
                    'landscape_url': 'https://via.placeholder.com/1200x628.jpg',
                    'square_url': 'https://via.placeholder.com/1200x1200.jpg',
                    'logo_url': 'https://via.placeholder.com/128x128.jpg'
                },
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()
            yield campaign
            db.session.delete(campaign)
            db.session.commit()

    def test_publish_pmax_campaign(self, service, pmax_campaign, app):
        """Test publishing a PERFORMANCE_MAX campaign to Google Ads."""
        with app.app_context():
            campaign = db.session.get(Campaign, pmax_campaign.id)

            result = service.publish_campaign(campaign)

            assert result['success'] is True, f"Campaign publish failed: {result.get('error')}"
            assert 'google_campaign_id' in result


class TestGoogleAdsApiVideoCampaign:
    """Integration tests for VIDEO campaign (expected to fail via API)."""

    @pytest.fixture
    def video_campaign(self, app):
        """Create a VIDEO campaign for testing."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test VIDEO {date.today().isoformat()}',
                objective='SALES',
                campaign_type='VIDEO',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                video_url='https://youtube.com/watch?v=dQw4w9WgXcQ',
                headlines=['Video Headline'],
                descriptions=['Video description'],
                bidding_strategy='target_cpm'
            )
            db.session.add(campaign)
            db.session.commit()
            yield campaign
            db.session.delete(campaign)
            db.session.commit()

    def test_video_campaign_api_restriction(self, service, video_campaign, app):
        """Test that VIDEO campaigns cannot be created via API."""
        with app.app_context():
            campaign = db.session.get(Campaign, video_campaign.id)

            # VIDEO campaigns should fail or return an error
            result = service.publish_campaign(campaign)

            # Either the validation prevents it or API returns error
            if result['success']:
                pytest.fail("VIDEO campaigns should not be creatable via API")


class TestGoogleAdsApiCampaignManagement:
    """Integration tests for campaign management (pause/enable)."""

    @pytest.fixture
    def published_campaign(self, app, service):
        """Create and publish a campaign for management testing."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test Management {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=30),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Management Test'],
                descriptions=['Campaign for pause/enable testing'],
                business_name='Test Business',
                images={'landscape_url': 'https://via.placeholder.com/1200x628.jpg'},
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()

            # Publish the campaign
            result = service.publish_campaign(campaign)
            if not result['success']:
                pytest.skip(f"Could not create test campaign: {result.get('error')}")

            campaign.status = 'PUBLISHED'
            campaign.google_campaign_id = result['google_campaign_id']
            campaign.google_ad_group_id = result.get('google_ad_group_id')
            campaign.google_ad_id = result.get('google_ad_id')
            db.session.commit()

            yield campaign

            # Cleanup
            db.session.delete(campaign)
            db.session.commit()

    def test_pause_campaign(self, service, published_campaign, app):
        """Test pausing a published campaign."""
        with app.app_context():
            campaign = db.session.get(Campaign, published_campaign.id)

            result = service.pause_campaign(campaign.google_campaign_id)

            assert result is True, "Campaign pause should succeed"

    def test_enable_campaign(self, service, published_campaign, app):
        """Test enabling a paused campaign."""
        with app.app_context():
            campaign = db.session.get(Campaign, published_campaign.id)

            # First pause it
            service.pause_campaign(campaign.google_campaign_id)

            # Then enable it
            result = service.enable_campaign(campaign.google_campaign_id)

            assert result is True, "Campaign enable should succeed"

    def test_pause_and_enable_cycle(self, service, published_campaign, app):
        """Test full pause and enable cycle."""
        with app.app_context():
            campaign = db.session.get(Campaign, published_campaign.id)
            google_id = campaign.google_campaign_id

            # Pause
            pause_result = service.pause_campaign(google_id)
            assert pause_result is True

            # Enable
            enable_result = service.enable_campaign(google_id)
            assert enable_result is True

            # Pause again
            pause_again = service.pause_campaign(google_id)
            assert pause_again is True


class TestGoogleAdsApiBiddingStrategies:
    """Integration tests for different bidding strategies."""

    def test_maximize_conversions_bidding(self, app, service):
        """Test campaign with maximize_conversions bidding."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test MaxConv {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline'],
                descriptions=['Test description'],
                business_name='Test Business',
                images={'landscape_url': 'https://via.placeholder.com/1200x628.jpg'},
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()

            result = service.publish_campaign(campaign)

            db.session.delete(campaign)
            db.session.commit()

            assert result['success'] is True, f"Failed: {result.get('error')}"

    def test_target_cpa_bidding(self, app, service):
        """Test campaign with target_cpa bidding."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test TargetCPA {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline'],
                descriptions=['Test description'],
                business_name='Test Business',
                images={'landscape_url': 'https://via.placeholder.com/1200x628.jpg'},
                bidding_strategy='target_cpa',
                target_cpa=5000000  # $5 target CPA
            )
            db.session.add(campaign)
            db.session.commit()

            result = service.publish_campaign(campaign)

            db.session.delete(campaign)
            db.session.commit()

            assert result['success'] is True, f"Failed: {result.get('error')}"

    def test_maximize_clicks_bidding(self, app, service):
        """Test campaign with maximize_clicks bidding."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test MaxClicks {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline'],
                descriptions=['Test description'],
                business_name='Test Business',
                images={'landscape_url': 'https://via.placeholder.com/1200x628.jpg'},
                bidding_strategy='maximize_clicks'
            )
            db.session.add(campaign)
            db.session.commit()

            result = service.publish_campaign(campaign)

            db.session.delete(campaign)
            db.session.commit()

            assert result['success'] is True, f"Failed: {result.get('error')}"


class TestGoogleAdsApiErrorHandling:
    """Integration tests for API error handling."""

    def test_invalid_customer_id_error(self, app, service):
        """Test error handling with invalid customer ID."""
        # Save original customer ID
        original_id = service._customer_id

        try:
            # Set invalid customer ID
            service._customer_id = '0000000000'

            campaign = MagicMock()
            campaign.name = 'Test'
            campaign.daily_budget = 1000000
            campaign.campaign_type = 'DEMAND_GEN'
            campaign.start_date = date.today() + timedelta(days=1)
            campaign.end_date = None
            campaign.bidding_strategy = None

            result = service.publish_campaign(campaign)

            # Should fail with error
            assert result['success'] is False or 'error' in result
        finally:
            # Restore original customer ID
            service._customer_id = original_id

    def test_missing_required_fields_error(self, app, service):
        """Test error handling when required fields are missing."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test Missing Fields {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                # Missing required fields: final_url, headlines, descriptions, business_name, images
            )
            db.session.add(campaign)
            db.session.commit()

            result = service.publish_campaign(campaign)

            db.session.delete(campaign)
            db.session.commit()

            # Should fail due to missing required fields
            assert result['success'] is False, "Should fail with missing required fields"


class TestGoogleAdsApiImageAssets:
    """Integration tests for image asset handling."""

    def test_campaign_with_all_image_types(self, app, service):
        """Test campaign with landscape, square, and logo images."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test All Images {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline'],
                descriptions=['Test description'],
                business_name='Test Business',
                images={
                    'landscape_url': 'https://via.placeholder.com/1200x628.jpg',
                    'square_url': 'https://via.placeholder.com/1200x1200.jpg',
                    'logo_url': 'https://via.placeholder.com/128x128.jpg'
                },
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()

            result = service.publish_campaign(campaign)

            db.session.delete(campaign)
            db.session.commit()

            assert result['success'] is True, f"Failed: {result.get('error')}"

    def test_campaign_with_landscape_only(self, app, service):
        """Test campaign with only landscape image."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test Landscape Only {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline'],
                descriptions=['Test description'],
                business_name='Test Business',
                images={
                    'landscape_url': 'https://via.placeholder.com/1200x628.jpg'
                },
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()

            result = service.publish_campaign(campaign)

            db.session.delete(campaign)
            db.session.commit()

            assert result['success'] is True, f"Failed: {result.get('error')}"

    def test_campaign_with_invalid_image_url(self, app, service):
        """Test campaign with invalid image URL."""
        with app.app_context():
            campaign = Campaign(
                name=f'API Test Invalid Image {date.today().isoformat()}',
                objective='SALES',
                campaign_type='DEMAND_GEN',
                daily_budget=1000000,
                start_date=date.today() + timedelta(days=1),
                status='DRAFT',
                final_url='https://example.com',
                headlines=['Test Headline'],
                descriptions=['Test description'],
                business_name='Test Business',
                images={
                    'landscape_url': 'https://invalid-domain-that-does-not-exist.com/image.jpg'
                },
                bidding_strategy='maximize_conversions'
            )
            db.session.add(campaign)
            db.session.commit()

            result = service.publish_campaign(campaign)

            db.session.delete(campaign)
            db.session.commit()

            # Should fail due to invalid image URL
            assert result['success'] is False, "Should fail with invalid image URL"
