"""
Google Ads API v22 validation utilities.

This module provides validation functions for Google Ads campaign data
based on API requirements and constraints.
"""
from typing import List, Dict, Any, Optional

# Character limits and asset requirements per campaign type
GOOGLE_ADS_LIMITS = {
    'DEMAND_GEN': {
        'headline': 40,
        'description': 90,
        'min_headlines': 1,
        'max_headlines': 5,
        'min_descriptions': 1,
        'max_descriptions': 5,
        'business_name': 25,
    },
    'PERFORMANCE_MAX': {
        'headline': 30,
        'long_headline': 90,
        'description': 90,
        'short_description': 60,  # At least one description must be <= 60 chars
        'min_headlines': 3,
        'max_headlines': 15,
        'min_descriptions': 2,
        'max_descriptions': 5,
        'business_name': 25,
    },
    'SEARCH': {
        'headline': 30,
        'description': 90,
        'min_headlines': 3,  # RSA requires minimum 3 headlines
        'max_headlines': 15,
        'min_descriptions': 2,  # RSA requires minimum 2 descriptions
        'max_descriptions': 4,
    },
    'DISPLAY': {
        'headline': 30,
        'long_headline': 90,
        'description': 90,
        'min_headlines': 1,
        'max_headlines': 5,
        'min_descriptions': 1,
        'max_descriptions': 5,
        'business_name': 25,
    },
    'VIDEO': {
        'headline': 30,
        'description': 90,
        'min_headlines': 0,
        'max_headlines': 5,
        'min_descriptions': 0,
        'max_descriptions': 5,
        'api_creation_supported': False,  # VIDEO campaigns cannot be created via API
    },
    'SHOPPING': {
        'min_headlines': 0,
        'max_headlines': 0,
        'min_descriptions': 0,
        'max_descriptions': 0,
    },
}

# Image requirements for different asset types
IMAGE_REQUIREMENTS = {
    'landscape': {
        'ratio': 1.91,
        'ratio_tolerance': 0.02,  # Allow 2% tolerance
        'min_width': 600,
        'min_height': 314,
        'description': 'Landscape (1.91:1) - minimum 600x314 pixels',
    },
    'square': {
        'ratio': 1.0,
        'ratio_tolerance': 0.02,
        'min_width': 300,
        'min_height': 300,
        'description': 'Square (1:1) - minimum 300x300 pixels',
    },
    'logo': {
        'ratio': 1.0,
        'ratio_tolerance': 0.02,
        'min_width': 128,
        'min_height': 128,
        'description': 'Logo (1:1) - minimum 128x128 pixels',
    },
    'logo_landscape': {
        'ratio': 4.0,
        'ratio_tolerance': 0.02,
        'min_width': 512,
        'min_height': 128,
        'description': 'Logo Landscape (4:1) - minimum 512x128 pixels',
    },
}


def validate_search_rsa_requirements(
    headlines: Optional[List[str]],
    descriptions: Optional[List[str]]
) -> List[str]:
    """
    Validate Responsive Search Ad requirements for SEARCH campaigns.

    RSA requires:
    - Minimum 3 headlines (max 15)
    - Minimum 2 descriptions (max 4)
    - Headlines max 30 characters
    - Descriptions max 90 characters

    Args:
        headlines: List of headline strings
        descriptions: List of description strings

    Returns:
        List of validation error messages
    """
    errors = []
    limits = GOOGLE_ADS_LIMITS['SEARCH']

    # Validate headlines
    headline_list = headlines or []
    if len(headline_list) < limits['min_headlines']:
        errors.append(
            f"SEARCH campaigns require at least {limits['min_headlines']} headlines "
            f"(Responsive Search Ads minimum requirement)"
        )
    if len(headline_list) > limits['max_headlines']:
        errors.append(
            f"SEARCH campaigns allow at most {limits['max_headlines']} headlines"
        )
    for i, headline in enumerate(headline_list):
        if len(headline) > limits['headline']:
            errors.append(
                f"Headline {i + 1} exceeds {limits['headline']} characters"
            )

    # Validate descriptions
    desc_list = descriptions or []
    if len(desc_list) < limits['min_descriptions']:
        errors.append(
            f"SEARCH campaigns require at least {limits['min_descriptions']} descriptions "
            f"(Responsive Search Ads minimum requirement)"
        )
    if len(desc_list) > limits['max_descriptions']:
        errors.append(
            f"SEARCH campaigns allow at most {limits['max_descriptions']} descriptions"
        )
    for i, desc in enumerate(desc_list):
        if len(desc) > limits['description']:
            errors.append(
                f"Description {i + 1} exceeds {limits['description']} characters"
            )

    return errors


def validate_pmax_short_description(descriptions: Optional[List[str]]) -> List[str]:
    """
    Validate Performance Max short description requirement.

    Performance Max requires at least one description to be 60 characters or fewer.
    This is used as a "short description" in various placements.

    Args:
        descriptions: List of description strings

    Returns:
        List of validation error messages
    """
    if not descriptions:
        return []

    limits = GOOGLE_ADS_LIMITS['PERFORMANCE_MAX']
    short_max = limits['short_description']

    has_short = any(len(desc) <= short_max for desc in descriptions)

    if not has_short:
        return [
            f"Performance Max requires at least one description of {short_max} characters "
            f"or fewer (short description requirement)"
        ]

    return []


def validate_keyword_uniqueness(keywords: Optional[List[str]]) -> List[str]:
    """
    Validate keyword uniqueness within an ad group.

    Google Ads requires keywords to be unique by text within an ad group.
    Duplicate keywords will result in CRITERION_ALREADY_EXISTS error.

    Args:
        keywords: List of keyword strings

    Returns:
        List of validation error messages for duplicates
    """
    if not keywords:
        return []

    errors = []
    seen = set()

    for keyword in keywords:
        # Normalize keyword for comparison (case-insensitive, trimmed)
        normalized = keyword.strip().lower()

        if normalized in seen:
            errors.append(f"Duplicate keyword detected: '{keyword}'")
        else:
            seen.add(normalized)

    return errors


def check_video_campaign_restriction(campaign_type: str) -> List[str]:
    """
    Check if VIDEO campaign type can be created via the API.

    VIDEO campaigns cannot be created via the Google Ads API.
    Users must use the Google Ads UI or Google Ads Scripts instead.

    Args:
        campaign_type: The campaign type string

    Returns:
        List with warning/error message if VIDEO, empty list otherwise
    """
    if campaign_type == 'VIDEO':
        return [
            "VIDEO campaigns cannot be created via the Google Ads API. "
            "Please use Google Ads UI or Google Ads Scripts to create VIDEO campaigns."
        ]
    return []


def validate_headlines_for_type(
    campaign_type: str,
    headlines: Optional[List[str]]
) -> List[str]:
    """
    Validate headlines against campaign type requirements.

    Args:
        campaign_type: The campaign type (SEARCH, PERFORMANCE_MAX, etc.)
        headlines: List of headline strings

    Returns:
        List of validation error messages
    """
    limits = GOOGLE_ADS_LIMITS.get(campaign_type, {})
    if not limits:
        return []

    errors = []
    headline_list = headlines or []

    min_headlines = limits.get('min_headlines', 0)
    max_headlines = limits.get('max_headlines', 0)
    max_length = limits.get('headline', 30)

    if min_headlines > 0 and len(headline_list) < min_headlines:
        errors.append(
            f"{campaign_type} campaigns require at least {min_headlines} headline(s)"
        )

    if max_headlines > 0 and len(headline_list) > max_headlines:
        errors.append(
            f"{campaign_type} campaigns allow at most {max_headlines} headlines"
        )

    for i, headline in enumerate(headline_list):
        if len(headline) > max_length:
            errors.append(
                f"Headline {i + 1} exceeds {max_length} characters"
            )

    return errors


def validate_descriptions_for_type(
    campaign_type: str,
    descriptions: Optional[List[str]]
) -> List[str]:
    """
    Validate descriptions against campaign type requirements.

    Args:
        campaign_type: The campaign type (SEARCH, PERFORMANCE_MAX, etc.)
        descriptions: List of description strings

    Returns:
        List of validation error messages
    """
    limits = GOOGLE_ADS_LIMITS.get(campaign_type, {})
    if not limits:
        return []

    errors = []
    desc_list = descriptions or []

    min_descriptions = limits.get('min_descriptions', 0)
    max_descriptions = limits.get('max_descriptions', 0)
    max_length = limits.get('description', 90)

    if min_descriptions > 0 and len(desc_list) < min_descriptions:
        errors.append(
            f"{campaign_type} campaigns require at least {min_descriptions} description(s)"
        )

    if max_descriptions > 0 and len(desc_list) > max_descriptions:
        errors.append(
            f"{campaign_type} campaigns allow at most {max_descriptions} descriptions"
        )

    for i, desc in enumerate(desc_list):
        if len(desc) > max_length:
            errors.append(
                f"Description {i + 1} exceeds {max_length} characters"
            )

    return errors


def validate_campaign_for_google_ads(campaign) -> Dict[str, Any]:
    """
    Comprehensive validation of a campaign for Google Ads API submission.

    Args:
        campaign: Campaign model instance

    Returns:
        Dictionary with 'valid' boolean and 'errors' list
    """
    errors = []
    campaign_type = campaign.campaign_type

    # Check VIDEO campaign restriction
    errors.extend(check_video_campaign_restriction(campaign_type))

    # Validate headlines and descriptions based on campaign type
    if campaign_type == 'SEARCH':
        errors.extend(validate_search_rsa_requirements(
            campaign.headlines,
            campaign.descriptions
        ))
        errors.extend(validate_keyword_uniqueness(campaign.keywords))
    elif campaign_type == 'PERFORMANCE_MAX':
        errors.extend(validate_headlines_for_type(campaign_type, campaign.headlines))
        errors.extend(validate_descriptions_for_type(campaign_type, campaign.descriptions))
        errors.extend(validate_pmax_short_description(campaign.descriptions))
    else:
        errors.extend(validate_headlines_for_type(campaign_type, campaign.headlines))
        errors.extend(validate_descriptions_for_type(campaign_type, campaign.descriptions))

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def get_campaign_type_limits(campaign_type: str) -> Dict[str, Any]:
    """
    Get the validation limits for a specific campaign type.

    Args:
        campaign_type: The campaign type string

    Returns:
        Dictionary of limits for the campaign type
    """
    return GOOGLE_ADS_LIMITS.get(campaign_type, {})


def get_image_requirements(image_type: str) -> Dict[str, Any]:
    """
    Get the requirements for a specific image type.

    Args:
        image_type: The image type (landscape, square, logo, logo_landscape)

    Returns:
        Dictionary of requirements for the image type
    """
    return IMAGE_REQUIREMENTS.get(image_type, {})
