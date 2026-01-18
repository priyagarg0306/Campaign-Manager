"""
Tests for Google Ads validators utilities.
"""
import pytest
from unittest.mock import MagicMock

from app.utils.google_ads_validators import (
    validate_search_rsa_requirements,
    validate_pmax_short_description,
    validate_keyword_uniqueness,
    check_video_campaign_restriction,
    validate_headlines_for_type,
    validate_descriptions_for_type,
    validate_campaign_for_google_ads,
    get_campaign_type_limits,
    get_image_requirements,
    GOOGLE_ADS_LIMITS,
    IMAGE_REQUIREMENTS,
)


class TestValidateSearchRsaRequirements:
    """Tests for validate_search_rsa_requirements function."""

    def test_valid_search_campaign(self):
        """Test valid SEARCH campaign with RSA requirements."""
        headlines = ['Headline 1', 'Headline 2', 'Headline 3']
        descriptions = ['Description 1', 'Description 2']
        errors = validate_search_rsa_requirements(headlines, descriptions)
        assert len(errors) == 0

    def test_too_few_headlines(self):
        """Test SEARCH campaign with too few headlines."""
        headlines = ['Headline 1', 'Headline 2']  # Need at least 3
        descriptions = ['Description 1', 'Description 2']
        errors = validate_search_rsa_requirements(headlines, descriptions)
        assert any('3 headlines' in error for error in errors)

    def test_too_few_descriptions(self):
        """Test SEARCH campaign with too few descriptions."""
        headlines = ['Headline 1', 'Headline 2', 'Headline 3']
        descriptions = ['Description 1']  # Need at least 2
        errors = validate_search_rsa_requirements(headlines, descriptions)
        assert any('2 descriptions' in error for error in errors)

    def test_headline_too_long(self):
        """Test SEARCH campaign with headline exceeding 30 characters."""
        headlines = ['Short', 'Medium headline', 'This headline is way too long for search campaigns']
        descriptions = ['Description 1', 'Description 2']
        errors = validate_search_rsa_requirements(headlines, descriptions)
        assert any('30 characters' in error for error in errors)

    def test_description_too_long(self):
        """Test SEARCH campaign with description exceeding 90 characters."""
        headlines = ['Headline 1', 'Headline 2', 'Headline 3']
        descriptions = [
            'Short description',
            'This description is intentionally made very long to exceed the ninety character limit for Google Ads SEARCH campaigns'
        ]
        errors = validate_search_rsa_requirements(headlines, descriptions)
        assert any('90 characters' in error for error in errors)

    def test_too_many_headlines(self):
        """Test SEARCH campaign with too many headlines."""
        headlines = [f'Headline {i}' for i in range(20)]  # Max is 15
        descriptions = ['Description 1', 'Description 2']
        errors = validate_search_rsa_requirements(headlines, descriptions)
        assert any('15 headlines' in error for error in errors)

    def test_too_many_descriptions(self):
        """Test SEARCH campaign with too many descriptions."""
        headlines = ['Headline 1', 'Headline 2', 'Headline 3']
        descriptions = [f'Description {i}' for i in range(6)]  # Max is 4
        errors = validate_search_rsa_requirements(headlines, descriptions)
        assert any('4 descriptions' in error for error in errors)

    def test_empty_headlines(self):
        """Test SEARCH campaign with empty headlines."""
        errors = validate_search_rsa_requirements(None, ['Desc 1', 'Desc 2'])
        assert any('headlines' in error.lower() for error in errors)

    def test_empty_descriptions(self):
        """Test SEARCH campaign with empty descriptions."""
        errors = validate_search_rsa_requirements(['H1', 'H2', 'H3'], None)
        assert any('descriptions' in error.lower() for error in errors)


class TestValidatePmaxShortDescription:
    """Tests for validate_pmax_short_description function."""

    def test_valid_with_short_description(self):
        """Test PMax with at least one short description."""
        descriptions = [
            'This is a longer description for Performance Max campaign assets.',
            'Short desc'  # This one is under 60 chars
        ]
        errors = validate_pmax_short_description(descriptions)
        assert len(errors) == 0

    def test_invalid_all_long_descriptions(self):
        """Test PMax with all descriptions over 60 characters."""
        descriptions = [
            'This description is intentionally long to exceed sixty characters.',
            'Another long description that also exceeds the sixty char limit easily.'
        ]
        errors = validate_pmax_short_description(descriptions)
        assert len(errors) == 1
        assert '60 characters' in errors[0]

    def test_empty_descriptions(self):
        """Test PMax with empty descriptions."""
        errors = validate_pmax_short_description([])
        assert len(errors) == 0  # Empty is allowed (caught elsewhere)

    def test_none_descriptions(self):
        """Test PMax with None descriptions."""
        errors = validate_pmax_short_description(None)
        assert len(errors) == 0

    def test_exactly_60_char_description(self):
        """Test description with exactly 60 characters."""
        descriptions = ['X' * 60]  # Exactly 60 chars should pass
        errors = validate_pmax_short_description(descriptions)
        assert len(errors) == 0


class TestValidateKeywordUniqueness:
    """Tests for validate_keyword_uniqueness function."""

    def test_unique_keywords(self):
        """Test with unique keywords."""
        keywords = ['buy shoes', 'red sneakers', 'athletic footwear']
        errors = validate_keyword_uniqueness(keywords)
        assert len(errors) == 0

    def test_duplicate_keywords_exact(self):
        """Test with exact duplicate keywords."""
        keywords = ['buy shoes', 'red sneakers', 'buy shoes']
        errors = validate_keyword_uniqueness(keywords)
        assert len(errors) == 1
        assert 'duplicate' in errors[0].lower()

    def test_duplicate_keywords_case_insensitive(self):
        """Test that duplicates are case-insensitive."""
        keywords = ['Buy Shoes', 'buy shoes', 'BUY SHOES']
        errors = validate_keyword_uniqueness(keywords)
        assert len(errors) == 2  # Two duplicates detected

    def test_duplicate_keywords_with_whitespace(self):
        """Test that duplicates ignore leading/trailing whitespace."""
        keywords = ['buy shoes', '  buy shoes  ', 'other keyword']
        errors = validate_keyword_uniqueness(keywords)
        assert len(errors) == 1

    def test_empty_keywords(self):
        """Test with empty keyword list."""
        errors = validate_keyword_uniqueness([])
        assert len(errors) == 0

    def test_none_keywords(self):
        """Test with None keywords."""
        errors = validate_keyword_uniqueness(None)
        assert len(errors) == 0


class TestCheckVideoCampaignRestriction:
    """Tests for check_video_campaign_restriction function."""

    def test_video_campaign_blocked(self):
        """Test that VIDEO campaigns return an error."""
        errors = check_video_campaign_restriction('VIDEO')
        assert len(errors) == 1
        assert 'cannot be created via the Google Ads API' in errors[0]

    def test_non_video_campaigns_allowed(self):
        """Test that other campaign types don't return errors."""
        for campaign_type in ['DEMAND_GEN', 'SEARCH', 'DISPLAY', 'SHOPPING', 'PERFORMANCE_MAX']:
            errors = check_video_campaign_restriction(campaign_type)
            assert len(errors) == 0


class TestValidateHeadlinesForType:
    """Tests for validate_headlines_for_type function."""

    def test_demand_gen_valid_headlines(self):
        """Test valid headlines for DEMAND_GEN campaign."""
        headlines = ['Headline 1', 'Headline 2']
        errors = validate_headlines_for_type('DEMAND_GEN', headlines)
        assert len(errors) == 0

    def test_demand_gen_headline_too_long(self):
        """Test DEMAND_GEN with headline exceeding 40 characters."""
        headlines = ['This headline is way too long for demand gen campaigns and exceeds forty characters']
        errors = validate_headlines_for_type('DEMAND_GEN', headlines)
        assert any('40 characters' in error for error in errors)

    def test_performance_max_valid_headlines(self):
        """Test valid headlines for PERFORMANCE_MAX campaign."""
        headlines = ['Short headline'] * 5
        errors = validate_headlines_for_type('PERFORMANCE_MAX', headlines)
        assert len(errors) == 0

    def test_performance_max_too_few_headlines(self):
        """Test PERFORMANCE_MAX with too few headlines."""
        headlines = ['Headline 1', 'Headline 2']  # Need at least 3
        errors = validate_headlines_for_type('PERFORMANCE_MAX', headlines)
        assert any('3' in error for error in errors)

    def test_unknown_campaign_type(self):
        """Test with unknown campaign type."""
        errors = validate_headlines_for_type('UNKNOWN_TYPE', ['Headline'])
        assert len(errors) == 0  # Unknown types return no errors

    def test_empty_headlines(self):
        """Test with empty headlines for type that requires them."""
        errors = validate_headlines_for_type('DEMAND_GEN', None)
        assert any('headline' in error.lower() for error in errors)


class TestValidateDescriptionsForType:
    """Tests for validate_descriptions_for_type function."""

    def test_demand_gen_valid_descriptions(self):
        """Test valid descriptions for DEMAND_GEN campaign."""
        descriptions = ['A nice description here']
        errors = validate_descriptions_for_type('DEMAND_GEN', descriptions)
        assert len(errors) == 0

    def test_demand_gen_description_too_long(self):
        """Test DEMAND_GEN with description exceeding 90 characters."""
        descriptions = ['X' * 100]
        errors = validate_descriptions_for_type('DEMAND_GEN', descriptions)
        assert any('90 characters' in error for error in errors)

    def test_performance_max_too_few_descriptions(self):
        """Test PERFORMANCE_MAX with too few descriptions."""
        descriptions = ['Only one description']  # Need at least 2
        errors = validate_descriptions_for_type('PERFORMANCE_MAX', descriptions)
        assert any('2' in error for error in errors)

    def test_display_valid_descriptions(self):
        """Test valid descriptions for DISPLAY campaign."""
        descriptions = ['Display ad description']
        errors = validate_descriptions_for_type('DISPLAY', descriptions)
        assert len(errors) == 0

    def test_shopping_no_description_required(self):
        """Test SHOPPING campaigns don't require descriptions."""
        errors = validate_descriptions_for_type('SHOPPING', None)
        assert len(errors) == 0

    def test_unknown_campaign_type(self):
        """Test with unknown campaign type."""
        errors = validate_descriptions_for_type('UNKNOWN', ['Desc'])
        assert len(errors) == 0


class TestValidateCampaignForGoogleAds:
    """Tests for validate_campaign_for_google_ads function."""

    def test_valid_demand_gen_campaign(self):
        """Test validation of valid DEMAND_GEN campaign."""
        campaign = MagicMock()
        campaign.campaign_type = 'DEMAND_GEN'
        campaign.headlines = ['Headline 1']
        campaign.descriptions = ['Description 1']
        campaign.keywords = None
        campaign.long_headline = None

        result = validate_campaign_for_google_ads(campaign)
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_video_campaign_blocked(self):
        """Test that VIDEO campaigns are blocked."""
        campaign = MagicMock()
        campaign.campaign_type = 'VIDEO'
        campaign.headlines = None
        campaign.descriptions = None
        campaign.keywords = None
        campaign.long_headline = None

        result = validate_campaign_for_google_ads(campaign)
        assert result['valid'] is False
        assert any('cannot be created' in error for error in result['errors'])

    def test_search_campaign_validation(self):
        """Test SEARCH campaign specific validation."""
        campaign = MagicMock()
        campaign.campaign_type = 'SEARCH'
        campaign.headlines = ['H1', 'H2', 'H3']
        campaign.descriptions = ['D1', 'D2']
        campaign.keywords = ['keyword1', 'keyword2']
        campaign.long_headline = None

        result = validate_campaign_for_google_ads(campaign)
        assert result['valid'] is True

    def test_pmax_campaign_validation(self):
        """Test PERFORMANCE_MAX campaign specific validation."""
        campaign = MagicMock()
        campaign.campaign_type = 'PERFORMANCE_MAX'
        campaign.headlines = ['H1', 'H2', 'H3']
        campaign.descriptions = ['Short desc', 'Another description that is much longer']
        campaign.keywords = None
        campaign.long_headline = None

        result = validate_campaign_for_google_ads(campaign)
        assert result['valid'] is True


class TestGetCampaignTypeLimits:
    """Tests for get_campaign_type_limits function."""

    def test_get_demand_gen_limits(self):
        """Test getting DEMAND_GEN limits."""
        limits = get_campaign_type_limits('DEMAND_GEN')
        assert limits['headline'] == 40
        assert limits['description'] == 90
        assert limits['min_headlines'] == 1
        assert limits['max_headlines'] == 5

    def test_get_search_limits(self):
        """Test getting SEARCH limits."""
        limits = get_campaign_type_limits('SEARCH')
        assert limits['headline'] == 30
        assert limits['min_headlines'] == 3
        assert limits['min_descriptions'] == 2

    def test_get_performance_max_limits(self):
        """Test getting PERFORMANCE_MAX limits."""
        limits = get_campaign_type_limits('PERFORMANCE_MAX')
        assert limits['headline'] == 30
        assert limits['long_headline'] == 90
        assert limits['short_description'] == 60
        assert limits['min_headlines'] == 3

    def test_get_unknown_type_limits(self):
        """Test getting limits for unknown type returns empty dict."""
        limits = get_campaign_type_limits('UNKNOWN_TYPE')
        assert limits == {}


class TestGetImageRequirements:
    """Tests for get_image_requirements function."""

    def test_get_landscape_requirements(self):
        """Test getting landscape image requirements."""
        requirements = get_image_requirements('landscape')
        assert requirements['ratio'] == 1.91
        assert requirements['min_width'] == 600
        assert requirements['min_height'] == 314

    def test_get_square_requirements(self):
        """Test getting square image requirements."""
        requirements = get_image_requirements('square')
        assert requirements['ratio'] == 1.0
        assert requirements['min_width'] == 300
        assert requirements['min_height'] == 300

    def test_get_logo_requirements(self):
        """Test getting logo requirements."""
        requirements = get_image_requirements('logo')
        assert requirements['ratio'] == 1.0
        assert requirements['min_width'] == 128
        assert requirements['min_height'] == 128

    def test_get_logo_landscape_requirements(self):
        """Test getting logo landscape requirements."""
        requirements = get_image_requirements('logo_landscape')
        assert requirements['ratio'] == 4.0
        assert requirements['min_width'] == 512
        assert requirements['min_height'] == 128

    def test_get_unknown_type_requirements(self):
        """Test getting requirements for unknown type returns empty dict."""
        requirements = get_image_requirements('unknown_type')
        assert requirements == {}


class TestGoogleAdsLimitsConstant:
    """Tests for GOOGLE_ADS_LIMITS constant."""

    def test_limits_not_empty(self):
        """Test that GOOGLE_ADS_LIMITS is not empty."""
        assert len(GOOGLE_ADS_LIMITS) > 0

    def test_all_campaign_types_defined(self):
        """Test that all campaign types have limits defined."""
        expected_types = ['DEMAND_GEN', 'PERFORMANCE_MAX', 'SEARCH', 'DISPLAY', 'VIDEO', 'SHOPPING']
        for campaign_type in expected_types:
            assert campaign_type in GOOGLE_ADS_LIMITS


class TestImageRequirementsConstant:
    """Tests for IMAGE_REQUIREMENTS constant."""

    def test_requirements_not_empty(self):
        """Test that IMAGE_REQUIREMENTS is not empty."""
        assert len(IMAGE_REQUIREMENTS) > 0

    def test_all_image_types_defined(self):
        """Test that all image types have requirements defined."""
        expected_types = ['landscape', 'square', 'logo', 'logo_landscape']
        for image_type in expected_types:
            assert image_type in IMAGE_REQUIREMENTS
