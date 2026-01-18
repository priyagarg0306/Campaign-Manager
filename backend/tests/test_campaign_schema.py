"""
Tests for campaign schema validation.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
from marshmallow import ValidationError

from app.schemas.campaign_schema import (
    CampaignCreateSchema,
    CampaignUpdateSchema,
    validate_campaign_for_publish,
    CAMPAIGN_TYPE_REQUIREMENTS,
    BIDDING_STRATEGIES_BY_TYPE,
    ALL_BIDDING_STRATEGIES,
)


class TestCampaignCreateSchema:
    """Tests for CampaignCreateSchema."""

    def test_valid_campaign_data(self):
        """Test validation of valid campaign data."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
        }
        result = schema.load(data)
        assert result['name'] == 'Test Campaign'
        assert result['objective'] == 'SALES'

    def test_invalid_objective(self):
        """Test validation fails for invalid objective."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'INVALID_OBJECTIVE',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'objective' in exc_info.value.messages

    def test_invalid_campaign_type(self):
        """Test validation fails for invalid campaign type."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'campaign_type': 'INVALID_TYPE',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'campaign_type' in exc_info.value.messages

    def test_negative_budget(self):
        """Test validation fails for negative budget."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'daily_budget': -100,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'daily_budget' in exc_info.value.messages

    def test_past_start_date(self):
        """Test validation fails for past start date."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'daily_budget': 1000000,
            'start_date': (date.today() - timedelta(days=1)).isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'start_date' in exc_info.value.messages

    def test_end_date_before_start_date(self):
        """Test validation fails when end date is before start date."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=10)).isoformat(),
            'end_date': (date.today() + timedelta(days=5)).isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'end_date' in exc_info.value.messages

    def test_invalid_bidding_strategy_for_type(self):
        """Test validation fails for invalid bidding strategy for campaign type."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'campaign_type': 'SHOPPING',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
            'bidding_strategy': 'maximize_conversions',  # Not valid for SHOPPING
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'bidding_strategy' in exc_info.value.messages

    def test_target_cpa_required_for_strategy(self):
        """Test validation fails when target_cpa strategy is set but value is missing."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'campaign_type': 'DEMAND_GEN',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
            'bidding_strategy': 'target_cpa',
            # target_cpa is missing
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'target_cpa' in exc_info.value.messages

    def test_target_roas_required_for_strategy(self):
        """Test validation fails when target_roas strategy is set but value is missing."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'campaign_type': 'SHOPPING',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
            'bidding_strategy': 'target_roas',
            # target_roas is missing
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'target_roas' in exc_info.value.messages

    def test_valid_bidding_strategy_with_target_cpa(self):
        """Test validation passes with target_cpa strategy and value."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Test Campaign',
            'objective': 'SALES',
            'campaign_type': 'DEMAND_GEN',
            'daily_budget': 1000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
            'bidding_strategy': 'target_cpa',
            'target_cpa': 5000000,  # $5 in micros
        }
        result = schema.load(data)
        assert result['bidding_strategy'] == 'target_cpa'
        assert result['target_cpa'] == 5000000

    def test_valid_with_all_fields(self):
        """Test validation passes with all optional fields."""
        schema = CampaignCreateSchema()
        data = {
            'name': 'Full Campaign',
            'objective': 'LEADS',
            'campaign_type': 'DEMAND_GEN',
            'daily_budget': 5000000,
            'start_date': (date.today() + timedelta(days=1)).isoformat(),
            'end_date': (date.today() + timedelta(days=30)).isoformat(),
            'ad_group_name': 'Test Group',
            'ad_headline': 'Amazing Headline',
            'ad_description': 'Great description',
            'final_url': 'https://example.com',
            'headlines': ['Headline 1', 'Headline 2'],
            'descriptions': ['Description 1'],
            'business_name': 'Test Business',
            'images': {'landscape_url': 'https://example.com/img.jpg'},
        }
        result = schema.load(data)
        assert result['business_name'] == 'Test Business'
        assert len(result['headlines']) == 2


class TestCampaignUpdateSchema:
    """Tests for CampaignUpdateSchema."""

    def test_partial_update(self):
        """Test partial update with only some fields."""
        schema = CampaignUpdateSchema()
        data = {'name': 'Updated Name'}
        result = schema.load(data)
        assert result['name'] == 'Updated Name'

    def test_update_with_invalid_objective(self):
        """Test update fails with invalid objective."""
        schema = CampaignUpdateSchema()
        data = {'objective': 'INVALID'}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'objective' in exc_info.value.messages

    def test_update_dates_validation(self):
        """Test update validates date order."""
        schema = CampaignUpdateSchema()
        data = {
            'start_date': (date.today() + timedelta(days=10)).isoformat(),
            'end_date': (date.today() + timedelta(days=5)).isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'end_date' in exc_info.value.messages

    def test_update_past_end_date(self):
        """Test update fails with past end date."""
        schema = CampaignUpdateSchema()
        data = {
            'end_date': (date.today() - timedelta(days=1)).isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert 'end_date' in exc_info.value.messages


class TestValidateCampaignForPublish:
    """Tests for validate_campaign_for_publish function."""

    def test_demand_gen_valid(self):
        """Test valid DEMAND_GEN campaign."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = ['Headline 1']
        campaign.descriptions = ['Description 1']
        campaign.business_name = 'Test Business'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert len(errors) == 0

    def test_demand_gen_missing_headlines(self):
        """Test DEMAND_GEN campaign missing headlines."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = []
        campaign.descriptions = ['Description 1']
        campaign.business_name = 'Test Business'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('headline' in error.lower() for error in errors)

    def test_demand_gen_missing_business_name(self):
        """Test DEMAND_GEN campaign missing business name."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = ['Headline 1']
        campaign.descriptions = ['Description 1']
        campaign.business_name = None
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('business name' in error.lower() for error in errors)

    def test_demand_gen_missing_images(self):
        """Test DEMAND_GEN campaign missing images."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = ['Headline 1']
        campaign.descriptions = ['Description 1']
        campaign.business_name = 'Test Business'
        campaign.images = {}
        campaign.final_url = 'https://example.com'
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('image' in error.lower() for error in errors)

    def test_performance_max_valid(self):
        """Test valid PERFORMANCE_MAX campaign."""
        campaign = MagicMock()
        campaign.campaign_type = 'PERFORMANCE_MAX'
        campaign.headlines = ['H1', 'H2', 'H3']
        campaign.long_headline = 'Long headline for Performance Max'
        campaign.descriptions = ['Short desc', 'Longer description here']
        campaign.business_name = 'Test Business'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert len(errors) == 0

    def test_performance_max_missing_short_description(self):
        """Test PERFORMANCE_MAX campaign without short description."""
        campaign = MagicMock()
        campaign.campaign_type = 'PERFORMANCE_MAX'
        campaign.headlines = ['H1', 'H2', 'H3']
        campaign.long_headline = 'Long headline'
        campaign.descriptions = ['This description is much longer than sixty characters so it should fail validation']
        campaign.business_name = 'Test Business'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('60 characters' in error for error in errors)

    def test_search_campaign_valid(self):
        """Test valid SEARCH campaign."""
        campaign = MagicMock()
        campaign.campaign_type = 'SEARCH'
        campaign.headlines = ['H1', 'H2', 'H3']
        campaign.descriptions = ['D1', 'D2']
        campaign.keywords = ['keyword1', 'keyword2']
        campaign.final_url = 'https://example.com'
        campaign.business_name = None
        campaign.images = None
        campaign.long_headline = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert len(errors) == 0

    def test_search_campaign_duplicate_keywords(self):
        """Test SEARCH campaign with duplicate keywords."""
        campaign = MagicMock()
        campaign.campaign_type = 'SEARCH'
        campaign.headlines = ['H1', 'H2', 'H3']
        campaign.descriptions = ['D1', 'D2']
        campaign.keywords = ['keyword1', 'keyword1']  # Duplicate
        campaign.final_url = 'https://example.com'
        campaign.business_name = None
        campaign.images = None
        campaign.long_headline = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('duplicate' in error.lower() for error in errors)

    def test_video_campaign_blocked(self):
        """Test VIDEO campaign returns API restriction error."""
        campaign = MagicMock()
        campaign.campaign_type = 'VIDEO'
        campaign.headlines = None
        campaign.descriptions = None
        campaign.video_url = 'https://youtube.com/watch?v=test'
        campaign.keywords = None
        campaign.business_name = None
        campaign.images = None
        campaign.long_headline = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('cannot be created via' in error for error in errors)

    def test_shopping_campaign_valid(self):
        """Test valid SHOPPING campaign."""
        campaign = MagicMock()
        campaign.campaign_type = 'SHOPPING'
        campaign.merchant_center_id = '12345678'
        campaign.headlines = None
        campaign.descriptions = None
        campaign.keywords = None
        campaign.business_name = None
        campaign.images = None
        campaign.long_headline = None
        campaign.video_url = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert len(errors) == 0

    def test_shopping_campaign_missing_merchant_id(self):
        """Test SHOPPING campaign missing merchant center ID."""
        campaign = MagicMock()
        campaign.campaign_type = 'SHOPPING'
        campaign.merchant_center_id = None
        campaign.headlines = None
        campaign.descriptions = None
        campaign.keywords = None
        campaign.business_name = None
        campaign.images = None
        campaign.long_headline = None
        campaign.video_url = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('merchant center' in error.lower() for error in errors)

    def test_display_campaign_valid(self):
        """Test valid DISPLAY campaign."""
        campaign = MagicMock()
        campaign.campaign_type = 'DISPLAY'
        campaign.headlines = ['H1']
        campaign.long_headline = 'Long headline for display'
        campaign.descriptions = ['D1']
        campaign.business_name = 'Test Business'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert len(errors) == 0

    def test_invalid_bidding_strategy_for_type(self):
        """Test invalid bidding strategy for campaign type."""
        campaign = MagicMock()
        campaign.campaign_type = 'SHOPPING'
        campaign.merchant_center_id = '12345678'
        campaign.bidding_strategy = 'maximize_conversions'  # Not valid for SHOPPING
        campaign.headlines = None
        campaign.descriptions = None
        campaign.keywords = None
        campaign.business_name = None
        campaign.images = None
        campaign.long_headline = None
        campaign.video_url = None
        campaign.target_cpa = None
        campaign.target_roas = None

        errors = validate_campaign_for_publish(campaign)
        assert any('bidding strategy' in error.lower() for error in errors)

    def test_target_cpa_required_when_strategy_set(self):
        """Test target CPA value required when strategy is target_cpa."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = ['H1']
        campaign.descriptions = ['D1']
        campaign.business_name = 'Test'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.bidding_strategy = 'target_cpa'
        campaign.target_cpa = None  # Missing
        campaign.target_roas = None
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None

        errors = validate_campaign_for_publish(campaign)
        assert any('target cpa' in error.lower() for error in errors)

    def test_headline_exceeds_max_length(self):
        """Test headline exceeding max length."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = ['X' * 50]  # Exceeds 40 char limit
        campaign.descriptions = ['D1']
        campaign.business_name = 'Test'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None

        errors = validate_campaign_for_publish(campaign)
        assert any('40 characters' in error for error in errors)

    def test_too_many_headlines(self):
        """Test campaign with too many headlines."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = ['H' + str(i) for i in range(10)]  # Max is 5
        campaign.descriptions = ['D1']
        campaign.business_name = 'Test'
        campaign.images = {'landscape_url': 'https://example.com/img.jpg'}
        campaign.final_url = 'https://example.com'
        campaign.bidding_strategy = None
        campaign.target_cpa = None
        campaign.target_roas = None
        campaign.long_headline = None
        campaign.keywords = None
        campaign.video_url = None
        campaign.merchant_center_id = None

        errors = validate_campaign_for_publish(campaign)
        assert any('5 headlines' in error for error in errors)


class TestBiddingStrategiesByType:
    """Tests for BIDDING_STRATEGIES_BY_TYPE constant."""

    def test_all_campaign_types_defined(self):
        """Test all campaign types have bidding strategies defined."""
        expected_types = ['DEMAND_GEN', 'PERFORMANCE_MAX', 'SEARCH', 'DISPLAY', 'VIDEO', 'SHOPPING']
        for campaign_type in expected_types:
            assert campaign_type in BIDDING_STRATEGIES_BY_TYPE

    def test_strategies_are_valid(self):
        """Test all strategies are in ALL_BIDDING_STRATEGIES."""
        for campaign_type, strategies in BIDDING_STRATEGIES_BY_TYPE.items():
            for strategy in strategies:
                assert strategy in ALL_BIDDING_STRATEGIES, f"Invalid strategy {strategy} for {campaign_type}"


class TestCampaignTypeRequirements:
    """Tests for CAMPAIGN_TYPE_REQUIREMENTS constant."""

    def test_all_campaign_types_defined(self):
        """Test all campaign types have requirements defined."""
        expected_types = ['DEMAND_GEN', 'PERFORMANCE_MAX', 'SEARCH', 'DISPLAY', 'VIDEO', 'SHOPPING']
        for campaign_type in expected_types:
            assert campaign_type in CAMPAIGN_TYPE_REQUIREMENTS

    def test_demand_gen_has_required_fields(self):
        """Test DEMAND_GEN has all required field definitions."""
        reqs = CAMPAIGN_TYPE_REQUIREMENTS['DEMAND_GEN']
        assert 'headlines' in reqs
        assert 'descriptions' in reqs
        assert 'business_name' in reqs
        assert 'images' in reqs
        assert 'final_url' in reqs

    def test_search_has_keywords_requirement(self):
        """Test SEARCH has keywords requirement."""
        reqs = CAMPAIGN_TYPE_REQUIREMENTS['SEARCH']
        assert 'keywords' in reqs
        assert reqs['keywords']['required'] is True

    def test_video_api_restriction_flagged(self):
        """Test VIDEO type has API creation restriction."""
        reqs = CAMPAIGN_TYPE_REQUIREMENTS['VIDEO']
        assert reqs.get('api_creation_supported') is False
