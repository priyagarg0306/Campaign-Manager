"""
Google Ads API error code mapping module.

This module maps Google Ads API error codes to user-friendly messages
and provides utilities for error handling.
"""
from typing import Dict, Any, Optional, List

# Map Google Ads API error codes to user-friendly messages
# Based on Google Ads API v22 error types
ERROR_MESSAGES: Dict[str, str] = {
    # Asset errors
    'REQUIRED_FIELD_MISSING': 'A required field is missing: {field}',
    'NOT_ENOUGH_HEADLINE_ASSET': 'At least {min_count} headlines are required',
    'NOT_ENOUGH_DESCRIPTION_ASSET': 'At least {min_count} descriptions are required',
    'SHORT_DESCRIPTION_REQUIRED': 'Performance Max requires at least one description of 60 characters or fewer',
    'ASSET_TEXT_TOO_LONG': 'Asset text exceeds the maximum length of {max_length} characters',
    'HEADLINE_TEXT_TOO_LONG': 'Headline exceeds the maximum length of 30 characters',
    'DESCRIPTION_TEXT_TOO_LONG': 'Description exceeds the maximum length of 90 characters',
    'DUPLICATE_ASSET': 'This asset already exists in the account',

    # Keyword errors
    'CRITERION_ALREADY_EXISTS': 'This keyword already exists in the ad group',
    'INVALID_KEYWORD_TEXT': 'Invalid keyword text: {keyword}',
    'KEYWORD_TEXT_TOO_LONG': 'Keyword exceeds the maximum length of 80 characters',
    'TOO_MANY_KEYWORDS': 'Too many keywords in ad group',

    # Image errors
    'ASPECT_RATIO_NOT_ALLOWED': 'Image aspect ratio must be {required_ratio}',
    'IMAGE_TOO_SMALL': 'Image dimensions too small. Minimum required: {min_width}x{min_height}',
    'IMAGE_TOO_LARGE': 'Image file size exceeds the maximum allowed',
    'INVALID_IMAGE_FORMAT': 'Invalid image format. Supported formats: JPEG, PNG, GIF',
    'IMAGE_ERROR': 'Failed to process image: {detail}',

    # Campaign errors
    'CAMPAIGN_TYPE_NOT_COMPATIBLE': 'Campaign type is not compatible with the selected settings',
    'CANNOT_CREATE_VIDEO_CAMPAIGN': 'VIDEO campaigns cannot be created via the Google Ads API. Please use Google Ads UI.',
    'INVALID_CAMPAIGN_TYPE': 'Invalid campaign type: {type}',
    'BUDGET_AMOUNT_TOO_LOW': 'Daily budget must be at least {min_amount}',
    'INVALID_DATE_RANGE': 'Invalid date range. End date must be after start date',
    'START_DATE_IN_PAST': 'Start date cannot be in the past',

    # Bidding errors
    'INVALID_BIDDING_STRATEGY': 'Invalid bidding strategy for this campaign type',
    'BIDDING_STRATEGY_NOT_SUPPORTED': 'Bidding strategy "{strategy}" is not supported for {campaign_type} campaigns',
    'TARGET_CPA_REQUIRED': 'Target CPA value is required for target_cpa bidding strategy',
    'TARGET_ROAS_REQUIRED': 'Target ROAS value is required for target_roas bidding strategy',
    'TARGET_CPA_TOO_LOW': 'Target CPA is too low. Minimum recommended: {min_cpa}',

    # Ad Group errors
    'AD_GROUP_TYPE_NOT_COMPATIBLE': 'Ad group type is not compatible with campaign type',
    'INVALID_AD_GROUP_NAME': 'Invalid ad group name',

    # Ad errors
    'AD_TYPE_NOT_COMPATIBLE': 'Ad type is not compatible with the ad group',
    'FINAL_URL_REQUIRED': 'Final URL is required for this campaign type',
    'INVALID_URL': 'Invalid URL format: {url}',
    'URL_NOT_ACCESSIBLE': 'The URL is not accessible or does not exist',

    # Shopping campaign errors
    'MERCHANT_CENTER_NOT_LINKED': 'Merchant Center account is not linked',
    'MERCHANT_CENTER_ID_REQUIRED': 'Merchant Center ID is required for Shopping campaigns',
    'INVALID_MERCHANT_CENTER_ID': 'Invalid Merchant Center ID: {id}',

    # Performance Max errors
    'PMAX_MISSING_REQUIRED_ASSETS': 'Performance Max campaigns require headlines, descriptions, and images',
    'PMAX_NOT_ENOUGH_HEADLINES': 'Performance Max requires at least 3 headlines',
    'PMAX_NOT_ENOUGH_DESCRIPTIONS': 'Performance Max requires at least 2 descriptions',
    'PMAX_SHORT_DESCRIPTION_REQUIRED': 'Performance Max requires at least one description of 60 characters or fewer',
    'PMAX_FINAL_URL_REQUIRED': 'Performance Max campaigns require a final URL',
    'PMAX_BUSINESS_NAME_REQUIRED': 'Performance Max campaigns require a business name',

    # Authentication/Authorization errors
    'AUTHENTICATION_ERROR': 'Authentication failed. Please check your credentials',
    'AUTHORIZATION_ERROR': 'You do not have permission to perform this action',
    'CUSTOMER_NOT_FOUND': 'Google Ads customer account not found',
    'INVALID_CUSTOMER_ID': 'Invalid Google Ads customer ID',

    # Rate limiting and transient errors
    'RATE_LIMIT_EXCEEDED': 'API rate limit exceeded. Please try again later',
    'INTERNAL_ERROR': 'An internal error occurred. Please try again',
    'TRANSIENT_ERROR': 'A temporary error occurred. Please try again',
    'RESOURCE_EXHAUSTED': 'API quota exhausted. Please try again later',
    'DEADLINE_EXCEEDED': 'Request timed out. Please try again',

    # General errors
    'UNKNOWN_ERROR': 'An unexpected error occurred: {detail}',
    'VALIDATION_ERROR': 'Validation failed: {detail}',
    'MUTATE_ERROR': 'Failed to create/update resource: {detail}',
}

# Error codes that can be retried
RETRYABLE_ERRORS: List[str] = [
    'INTERNAL_ERROR',
    'TRANSIENT_ERROR',
    'RESOURCE_EXHAUSTED',
    'DEADLINE_EXCEEDED',
    'RATE_LIMIT_EXCEEDED',
]

# Error severity levels
ERROR_SEVERITY = {
    'CRITICAL': ['AUTHENTICATION_ERROR', 'AUTHORIZATION_ERROR', 'CUSTOMER_NOT_FOUND'],
    'ERROR': ['VALIDATION_ERROR', 'MUTATE_ERROR', 'INVALID_CAMPAIGN_TYPE'],
    'WARNING': ['DUPLICATE_ASSET', 'CRITERION_ALREADY_EXISTS'],
    'INFO': ['RATE_LIMIT_EXCEEDED'],
}


def map_google_ads_error(
    error_code: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Map a Google Ads API error code to a user-friendly message.

    Args:
        error_code: The Google Ads error code string
        context: Optional dictionary with context values for message formatting

    Returns:
        User-friendly error message
    """
    context = context or {}

    # Try to find exact match
    message_template = ERROR_MESSAGES.get(error_code)

    if not message_template:
        # Try to find partial match
        for key, template in ERROR_MESSAGES.items():
            if key in error_code or error_code in key:
                message_template = template
                break

    if not message_template:
        message_template = ERROR_MESSAGES.get('UNKNOWN_ERROR', 'An error occurred: {detail}')
        context.setdefault('detail', error_code)

    # Format message with context
    try:
        return message_template.format(**context)
    except KeyError:
        # If formatting fails, return template as-is
        return message_template


def is_retryable_error(error_code: str) -> bool:
    """
    Check if an error is retryable.

    Args:
        error_code: The Google Ads error code string

    Returns:
        True if the error can be retried
    """
    return error_code in RETRYABLE_ERRORS


def get_error_severity(error_code: str) -> str:
    """
    Get the severity level of an error.

    Args:
        error_code: The Google Ads error code string

    Returns:
        Severity level string (CRITICAL, ERROR, WARNING, INFO)
    """
    for severity, codes in ERROR_SEVERITY.items():
        if error_code in codes:
            return severity
    return 'ERROR'


def parse_google_ads_exception(exception) -> Dict[str, Any]:
    """
    Parse a Google Ads API exception into a structured format.

    Args:
        exception: GoogleAdsException instance

    Returns:
        Dictionary with parsed error information
    """
    errors = []
    error_codes = []

    try:
        for error in exception.failure.errors:
            error_info = {
                'message': error.message,
                'error_code': str(error.error_code) if hasattr(error, 'error_code') else 'UNKNOWN',
                'location': None,
            }

            # Extract field path if available
            if error.location:
                field_paths = []
                for element in error.location.field_path_elements:
                    field_paths.append(element.field_name)
                error_info['location'] = '.'.join(field_paths)

            errors.append(error_info)

            # Try to extract the specific error code
            if hasattr(error, 'error_code'):
                error_code_str = str(error.error_code)
                # Extract the actual error type from the proto
                for attr in dir(error.error_code):
                    if not attr.startswith('_'):
                        val = getattr(error.error_code, attr)
                        if val and val != 0:
                            error_codes.append(attr.upper())

    except Exception:
        errors.append({
            'message': str(exception),
            'error_code': 'UNKNOWN',
            'location': None
        })

    return {
        'request_id': getattr(exception, 'request_id', None),
        'errors': errors,
        'error_codes': error_codes,
        'is_retryable': any(is_retryable_error(code) for code in error_codes),
        'user_message': '; '.join(e['message'] for e in errors) if errors else str(exception),
    }


def format_validation_errors(errors: List[str]) -> Dict[str, Any]:
    """
    Format a list of validation errors into a standardized response.

    Args:
        errors: List of error message strings

    Returns:
        Dictionary with structured error information
    """
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'error_count': len(errors),
        'code': 'VALIDATION_ERROR' if errors else None,
    }


def get_error_response(
    error_code: str,
    context: Optional[Dict[str, Any]] = None,
    include_original: bool = False
) -> Dict[str, Any]:
    """
    Get a standardized error response for API responses.

    Args:
        error_code: The error code
        context: Optional context for message formatting
        include_original: Whether to include the original error code

    Returns:
        Dictionary suitable for API error response
    """
    user_message = map_google_ads_error(error_code, context)
    severity = get_error_severity(error_code)
    retryable = is_retryable_error(error_code)

    response = {
        'error': user_message,
        'code': error_code if include_original else None,
        'severity': severity,
        'retryable': retryable,
    }

    # Add Google Ads specific code if relevant
    if error_code in ERROR_MESSAGES:
        response['googleAdsCode'] = error_code

    return response
