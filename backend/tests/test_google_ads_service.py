"""
Tests for Google Ads Service.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta

from app.services.google_ads_service import GoogleAdsService


class TestGoogleAdsServiceConfiguration:
    """Tests for Google Ads service configuration."""

    def test_is_configured_without_credentials(self):
        """Test is_configured returns False when credentials are not set."""
        with patch.dict('os.environ', {}, clear=True):
            service = GoogleAdsService()
            service._client = None  # Reset client
            # Mock the client creation to return None
            with patch.object(service, '_get_client', return_value=None):
                assert service.is_configured() is False

    @patch('app.services.google_ads_service.GOOGLE_ADS_AVAILABLE', False)
    def test_is_configured_without_library(self):
        """Test is_configured returns False when library is not installed."""
        service = GoogleAdsService()
        service._client = None
        assert service.is_configured() is False


class TestGoogleAdsServiceMocked:
    """Tests for Google Ads service with mocked client."""

    @pytest.fixture
    def mock_google_ads_client(self):
        """Create a mock Google Ads client."""
        mock_client = MagicMock()

        # Mock enums
        mock_client.enums.CampaignStatusEnum.PAUSED = 'PAUSED'
        mock_client.enums.CampaignStatusEnum.ENABLED = 'ENABLED'
        mock_client.enums.BudgetDeliveryMethodEnum.STANDARD = 'STANDARD'
        mock_client.enums.AdvertisingChannelTypeEnum.DEMAND_GEN = 'DEMAND_GEN'
        mock_client.enums.AdvertisingChannelTypeEnum.DISPLAY = 'DISPLAY'
        mock_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CONVERSIONS = 'MAXIMIZE_CONVERSIONS'
        mock_client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CLICKS = 'MAXIMIZE_CLICKS'
        mock_client.enums.AdGroupStatusEnum.ENABLED = 'ENABLED'
        mock_client.enums.AdGroupTypeEnum.DISPLAY_STANDARD = 'DISPLAY_STANDARD'
        mock_client.enums.AdGroupAdStatusEnum.ENABLED = 'ENABLED'

        return mock_client

    @pytest.fixture
    def mock_campaign(self):
        """Create a mock campaign object."""
        campaign = MagicMock()
        campaign.name = 'Test Campaign'
        campaign.daily_budget = 10000000
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.start_date = date.today() + timedelta(days=1)
        campaign.end_date = date.today() + timedelta(days=30)
        campaign.ad_group_name = 'Test Ad Group'
        campaign.ad_headline = 'Test Headline'
        campaign.ad_description = 'Test description for the ad'
        campaign.final_url = 'https://example.com'
        # Required fields for DEMAND_GEN campaigns
        campaign.headlines = ['Test Headline']
        campaign.descriptions = ['Test description for the ad']
        campaign.business_name = 'Test Business'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None
        return campaign

    def test_create_campaign_budget(self, mock_google_ads_client):
        """Test campaign budget creation."""
        service = GoogleAdsService()
        service._client = mock_google_ads_client
        service._customer_id = '1234567890'

        # Mock budget service
        mock_budget_service = MagicMock()
        mock_budget_operation = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name='customers/123/campaignBudgets/456')]

        mock_google_ads_client.get_service.return_value = mock_budget_service
        mock_google_ads_client.get_type.return_value = mock_budget_operation
        mock_budget_service.mutate_campaign_budgets.return_value = mock_response

        result = service._create_campaign_budget('Test Budget', 10000000)

        assert result == 'customers/123/campaignBudgets/456'
        mock_budget_service.mutate_campaign_budgets.assert_called_once()

    def test_create_campaign(self, mock_google_ads_client):
        """Test campaign creation."""
        service = GoogleAdsService()
        service._client = mock_google_ads_client
        service._customer_id = '1234567890'

        # Mock campaign service
        mock_campaign_service = MagicMock()
        mock_campaign_operation = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name='customers/123/campaigns/789')]

        mock_google_ads_client.get_service.return_value = mock_campaign_service
        mock_google_ads_client.get_type.return_value = mock_campaign_operation
        mock_campaign_service.mutate_campaigns.return_value = mock_response

        result = service._create_campaign(
            'Test Campaign',
            'budget/resource',
            'DEMAND_GEN',
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=30)
        )

        assert result == 'customers/123/campaigns/789'
        mock_campaign_service.mutate_campaigns.assert_called_once()

    def test_create_ad_group(self, mock_google_ads_client):
        """Test ad group creation."""
        service = GoogleAdsService()
        service._client = mock_google_ads_client
        service._customer_id = '1234567890'

        # Mock ad group service
        mock_ad_group_service = MagicMock()
        mock_ad_group_operation = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name='customers/123/adGroups/101')]

        mock_google_ads_client.get_service.return_value = mock_ad_group_service
        mock_google_ads_client.get_type.return_value = mock_ad_group_operation
        mock_ad_group_service.mutate_ad_groups.return_value = mock_response

        result = service._create_ad_group('campaign/resource', 'Test Ad Group')

        assert result == 'customers/123/adGroups/101'
        mock_ad_group_service.mutate_ad_groups.assert_called_once()

    def test_publish_campaign_success(self, mock_google_ads_client, mock_campaign):
        """Test full campaign publishing flow."""
        service = GoogleAdsService()
        service._client = mock_google_ads_client
        service._customer_id = '1234567890'

        # Mock all services
        mock_service = MagicMock()

        def get_service_side_effect(name):
            return mock_service

        def get_type_side_effect(name):
            return MagicMock()

        mock_google_ads_client.get_service.side_effect = get_service_side_effect
        mock_google_ads_client.get_type.side_effect = get_type_side_effect

        # Mock responses
        mock_budget_response = MagicMock()
        mock_budget_response.results = [MagicMock(resource_name='customers/123/campaignBudgets/456')]

        mock_campaign_response = MagicMock()
        mock_campaign_response.results = [MagicMock(resource_name='customers/123/campaigns/789')]

        mock_ad_group_response = MagicMock()
        mock_ad_group_response.results = [MagicMock(resource_name='customers/123/adGroups/101')]

        mock_ad_response = MagicMock()
        mock_ad_response.results = [MagicMock(resource_name='customers/123/adGroupAds/202')]

        mock_asset_response = MagicMock()
        mock_asset_response.results = [MagicMock(resource_name='customers/123/assets/303')]

        mock_service.mutate_campaign_budgets.return_value = mock_budget_response
        mock_service.mutate_campaigns.return_value = mock_campaign_response
        mock_service.mutate_ad_groups.return_value = mock_ad_group_response
        mock_service.mutate_ad_group_ads.return_value = mock_ad_response
        mock_service.mutate_assets.return_value = mock_asset_response

        # Mock the image upload methods to return asset resource names
        with patch.object(service, '_upload_campaign_images') as mock_upload:
            mock_upload.return_value = {
                'landscape': 'customers/123/assets/landscape_123',
                'square': 'customers/123/assets/square_123',
            }

            result = service.publish_campaign(mock_campaign)

        assert result['success'] is True
        assert result['google_campaign_id'] == '789'
        assert result['google_ad_group_id'] == '101'
        assert result['google_ad_id'] == '202'

    def test_pause_campaign(self, mock_google_ads_client):
        """Test pausing a campaign."""
        service = GoogleAdsService()
        service._client = mock_google_ads_client
        service._customer_id = '1234567890'

        mock_campaign_service = MagicMock()
        mock_campaign_operation = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name='customers/123/campaigns/789')]

        mock_google_ads_client.get_service.return_value = mock_campaign_service
        mock_google_ads_client.get_type.return_value = mock_campaign_operation
        mock_campaign_service.campaign_path.return_value = 'customers/123/campaigns/789'
        mock_campaign_service.mutate_campaigns.return_value = mock_response

        result = service.pause_campaign('789')

        assert result is True
        mock_campaign_service.mutate_campaigns.assert_called_once()

    def test_enable_campaign(self, mock_google_ads_client):
        """Test enabling a campaign."""
        service = GoogleAdsService()
        service._client = mock_google_ads_client
        service._customer_id = '1234567890'

        mock_campaign_service = MagicMock()
        mock_campaign_operation = MagicMock()
        mock_response = MagicMock()
        mock_response.results = [MagicMock(resource_name='customers/123/campaigns/789')]

        mock_google_ads_client.get_service.return_value = mock_campaign_service
        mock_google_ads_client.get_type.return_value = mock_campaign_operation
        mock_campaign_service.campaign_path.return_value = 'customers/123/campaigns/789'
        mock_campaign_service.mutate_campaigns.return_value = mock_response

        result = service.enable_campaign('789')

        assert result is True
        mock_campaign_service.mutate_campaigns.assert_called_once()


class TestGoogleAdsServiceErrors:
    """Tests for Google Ads service error handling."""

    @patch.dict(os.environ, {
        'GOOGLE_ADS_DEVELOPER_TOKEN': '',
        'GOOGLE_ADS_CLIENT_ID': '',
        'GOOGLE_ADS_CLIENT_SECRET': '',
        'GOOGLE_ADS_REFRESH_TOKEN': '',
    }, clear=False)
    def test_publish_campaign_not_configured(self):
        """Test publishing when not configured raises exception."""
        service = GoogleAdsService()
        # Force reinitialization by clearing the client
        service._client = None

        mock_campaign = MagicMock()

        with pytest.raises(Exception) as excinfo:
            service.publish_campaign(mock_campaign)

        assert 'not configured' in str(excinfo.value).lower()

    @patch.dict(os.environ, {
        'GOOGLE_ADS_DEVELOPER_TOKEN': '',
        'GOOGLE_ADS_CLIENT_ID': '',
        'GOOGLE_ADS_CLIENT_SECRET': '',
        'GOOGLE_ADS_REFRESH_TOKEN': '',
    }, clear=False)
    def test_pause_campaign_not_configured(self):
        """Test pausing when not configured raises exception."""
        service = GoogleAdsService()
        service._client = None

        with pytest.raises(Exception) as excinfo:
            service.pause_campaign('123')

        assert 'not configured' in str(excinfo.value).lower()

    @patch.dict(os.environ, {
        'GOOGLE_ADS_DEVELOPER_TOKEN': '',
        'GOOGLE_ADS_CLIENT_ID': '',
        'GOOGLE_ADS_CLIENT_SECRET': '',
        'GOOGLE_ADS_REFRESH_TOKEN': '',
    }, clear=False)
    def test_enable_campaign_not_configured(self):
        """Test enabling when not configured raises exception."""
        service = GoogleAdsService()
        service._client = None

        with pytest.raises(Exception) as excinfo:
            service.enable_campaign('123')

        assert 'not configured' in str(excinfo.value).lower()
