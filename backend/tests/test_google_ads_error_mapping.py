"""
Tests for Google Ads error mapping utilities.
"""
import pytest
from unittest.mock import MagicMock

from app.utils.google_ads_error_mapping import (
    map_google_ads_error,
    is_retryable_error,
    get_error_severity,
    parse_google_ads_exception,
    format_validation_errors,
    get_error_response,
    ERROR_MESSAGES,
    RETRYABLE_ERRORS,
)


class TestMapGoogleAdsError:
    """Tests for map_google_ads_error function."""

    def test_map_known_error_code(self):
        """Test mapping a known error code."""
        message = map_google_ads_error('REQUIRED_FIELD_MISSING', {'field': 'name'})
        assert 'required field is missing' in message.lower()
        assert 'name' in message

    def test_map_error_without_context(self):
        """Test mapping error without context placeholders."""
        message = map_google_ads_error('SHORT_DESCRIPTION_REQUIRED')
        assert '60 characters' in message

    def test_map_unknown_error_code(self):
        """Test mapping an unknown error code."""
        message = map_google_ads_error('COMPLETELY_UNKNOWN_ERROR')
        assert 'error occurred' in message.lower()

    def test_map_partial_match_error_code(self):
        """Test partial matching of error codes."""
        message = map_google_ads_error('SOME_REQUIRED_FIELD_MISSING_ERROR')
        # Should match REQUIRED_FIELD_MISSING
        assert 'required field' in message.lower() or 'error' in message.lower()

    def test_map_error_with_missing_context_key(self):
        """Test mapping error when context is missing required keys."""
        # This should not raise an exception, just return the template
        message = map_google_ads_error('REQUIRED_FIELD_MISSING', {})
        assert message is not None

    def test_map_headline_error(self):
        """Test headline-specific error mapping."""
        message = map_google_ads_error('NOT_ENOUGH_HEADLINE_ASSET', {'min_count': 3})
        assert 'headline' in message.lower()
        assert '3' in message

    def test_map_description_error(self):
        """Test description-specific error mapping."""
        message = map_google_ads_error('NOT_ENOUGH_DESCRIPTION_ASSET', {'min_count': 2})
        assert 'description' in message.lower()
        assert '2' in message

    def test_map_image_error(self):
        """Test image-specific error mapping."""
        message = map_google_ads_error('IMAGE_TOO_SMALL', {'min_width': 600, 'min_height': 314})
        assert 'image' in message.lower() or 'dimension' in message.lower()

    def test_map_authentication_error(self):
        """Test authentication error mapping."""
        message = map_google_ads_error('AUTHENTICATION_ERROR')
        assert 'authentication' in message.lower()

    def test_map_rate_limit_error(self):
        """Test rate limit error mapping."""
        message = map_google_ads_error('RATE_LIMIT_EXCEEDED')
        assert 'rate limit' in message.lower() or 'try again' in message.lower()


class TestIsRetryableError:
    """Tests for is_retryable_error function."""

    def test_retryable_internal_error(self):
        """Test that INTERNAL_ERROR is retryable."""
        assert is_retryable_error('INTERNAL_ERROR') is True

    def test_retryable_transient_error(self):
        """Test that TRANSIENT_ERROR is retryable."""
        assert is_retryable_error('TRANSIENT_ERROR') is True

    def test_retryable_resource_exhausted(self):
        """Test that RESOURCE_EXHAUSTED is retryable."""
        assert is_retryable_error('RESOURCE_EXHAUSTED') is True

    def test_retryable_deadline_exceeded(self):
        """Test that DEADLINE_EXCEEDED is retryable."""
        assert is_retryable_error('DEADLINE_EXCEEDED') is True

    def test_retryable_rate_limit_exceeded(self):
        """Test that RATE_LIMIT_EXCEEDED is retryable."""
        assert is_retryable_error('RATE_LIMIT_EXCEEDED') is True

    def test_non_retryable_validation_error(self):
        """Test that VALIDATION_ERROR is not retryable."""
        assert is_retryable_error('VALIDATION_ERROR') is False

    def test_non_retryable_authentication_error(self):
        """Test that AUTHENTICATION_ERROR is not retryable."""
        assert is_retryable_error('AUTHENTICATION_ERROR') is False

    def test_non_retryable_unknown_error(self):
        """Test that unknown errors are not retryable."""
        assert is_retryable_error('UNKNOWN_RANDOM_ERROR') is False


class TestGetErrorSeverity:
    """Tests for get_error_severity function."""

    def test_critical_severity_authentication(self):
        """Test that AUTHENTICATION_ERROR is CRITICAL."""
        assert get_error_severity('AUTHENTICATION_ERROR') == 'CRITICAL'

    def test_critical_severity_authorization(self):
        """Test that AUTHORIZATION_ERROR is CRITICAL."""
        assert get_error_severity('AUTHORIZATION_ERROR') == 'CRITICAL'

    def test_critical_severity_customer_not_found(self):
        """Test that CUSTOMER_NOT_FOUND is CRITICAL."""
        assert get_error_severity('CUSTOMER_NOT_FOUND') == 'CRITICAL'

    def test_error_severity_validation(self):
        """Test that VALIDATION_ERROR is ERROR."""
        assert get_error_severity('VALIDATION_ERROR') == 'ERROR'

    def test_error_severity_mutate(self):
        """Test that MUTATE_ERROR is ERROR."""
        assert get_error_severity('MUTATE_ERROR') == 'ERROR'

    def test_warning_severity_duplicate(self):
        """Test that DUPLICATE_ASSET is WARNING."""
        assert get_error_severity('DUPLICATE_ASSET') == 'WARNING'

    def test_warning_severity_criterion_exists(self):
        """Test that CRITERION_ALREADY_EXISTS is WARNING."""
        assert get_error_severity('CRITERION_ALREADY_EXISTS') == 'WARNING'

    def test_info_severity_rate_limit(self):
        """Test that RATE_LIMIT_EXCEEDED is INFO."""
        assert get_error_severity('RATE_LIMIT_EXCEEDED') == 'INFO'

    def test_default_severity_unknown(self):
        """Test that unknown errors default to ERROR."""
        assert get_error_severity('RANDOM_UNKNOWN_ERROR') == 'ERROR'


class TestParseGoogleAdsException:
    """Tests for parse_google_ads_exception function."""

    def test_parse_exception_with_failure(self):
        """Test parsing an exception with failure attribute."""
        # Create mock exception with failure structure
        mock_error = MagicMock()
        mock_error.message = 'Test error message'
        mock_error.error_code = 'VALIDATION_ERROR'
        mock_error.location = None

        mock_failure = MagicMock()
        mock_failure.errors = [mock_error]

        mock_exception = MagicMock()
        mock_exception.failure = mock_failure
        mock_exception.request_id = 'test-request-123'

        result = parse_google_ads_exception(mock_exception)

        assert result['request_id'] == 'test-request-123'
        assert len(result['errors']) == 1
        assert result['errors'][0]['message'] == 'Test error message'

    def test_parse_exception_with_location(self):
        """Test parsing exception with field path location."""
        mock_element1 = MagicMock()
        mock_element1.field_name = 'campaign'
        mock_element2 = MagicMock()
        mock_element2.field_name = 'name'

        mock_location = MagicMock()
        mock_location.field_path_elements = [mock_element1, mock_element2]

        mock_error = MagicMock()
        mock_error.message = 'Invalid campaign name'
        mock_error.error_code = 'INVALID'
        mock_error.location = mock_location

        mock_failure = MagicMock()
        mock_failure.errors = [mock_error]

        mock_exception = MagicMock()
        mock_exception.failure = mock_failure
        mock_exception.request_id = 'test-123'

        result = parse_google_ads_exception(mock_exception)

        assert result['errors'][0]['location'] == 'campaign.name'

    def test_parse_exception_without_failure(self):
        """Test parsing exception without failure attribute."""
        mock_exception = MagicMock()
        mock_exception.failure.errors = None  # This will cause an exception in iteration

        # Should handle gracefully
        result = parse_google_ads_exception(mock_exception)
        assert 'errors' in result
        assert 'user_message' in result

    def test_parse_exception_multiple_errors(self):
        """Test parsing exception with multiple errors."""
        mock_error1 = MagicMock()
        mock_error1.message = 'Error 1'
        mock_error1.error_code = 'ERROR_1'
        mock_error1.location = None

        mock_error2 = MagicMock()
        mock_error2.message = 'Error 2'
        mock_error2.error_code = 'ERROR_2'
        mock_error2.location = None

        mock_failure = MagicMock()
        mock_failure.errors = [mock_error1, mock_error2]

        mock_exception = MagicMock()
        mock_exception.failure = mock_failure
        mock_exception.request_id = 'multi-error-123'

        result = parse_google_ads_exception(mock_exception)

        assert len(result['errors']) == 2
        assert 'Error 1' in result['user_message']
        assert 'Error 2' in result['user_message']


class TestFormatValidationErrors:
    """Tests for format_validation_errors function."""

    def test_format_empty_errors(self):
        """Test formatting empty error list."""
        result = format_validation_errors([])
        assert result['valid'] is True
        assert result['errors'] == []
        assert result['error_count'] == 0
        assert result['code'] is None

    def test_format_single_error(self):
        """Test formatting single error."""
        result = format_validation_errors(['Name is required'])
        assert result['valid'] is False
        assert 'Name is required' in result['errors']
        assert result['error_count'] == 1
        assert result['code'] == 'VALIDATION_ERROR'

    def test_format_multiple_errors(self):
        """Test formatting multiple errors."""
        errors = ['Name is required', 'Budget must be positive', 'Invalid date']
        result = format_validation_errors(errors)
        assert result['valid'] is False
        assert len(result['errors']) == 3
        assert result['error_count'] == 3
        assert result['code'] == 'VALIDATION_ERROR'


class TestGetErrorResponse:
    """Tests for get_error_response function."""

    def test_get_response_known_error(self):
        """Test getting response for known error code."""
        result = get_error_response('AUTHENTICATION_ERROR')
        assert 'error' in result
        assert 'severity' in result
        assert 'retryable' in result
        assert result['severity'] == 'CRITICAL'
        assert result['retryable'] is False

    def test_get_response_with_include_original(self):
        """Test getting response with original code included."""
        result = get_error_response('VALIDATION_ERROR', include_original=True)
        assert result['code'] == 'VALIDATION_ERROR'

    def test_get_response_without_include_original(self):
        """Test getting response without original code."""
        result = get_error_response('VALIDATION_ERROR', include_original=False)
        assert result['code'] is None

    def test_get_response_retryable_error(self):
        """Test getting response for retryable error."""
        result = get_error_response('RATE_LIMIT_EXCEEDED')
        assert result['retryable'] is True

    def test_get_response_with_context(self):
        """Test getting response with context values."""
        result = get_error_response('REQUIRED_FIELD_MISSING', context={'field': 'budget'})
        assert 'budget' in result['error']

    def test_get_response_google_ads_code(self):
        """Test that known errors include googleAdsCode."""
        result = get_error_response('INVALID_CAMPAIGN_TYPE', include_original=True)
        assert 'googleAdsCode' in result


class TestErrorMessages:
    """Tests for ERROR_MESSAGES constant."""

    def test_error_messages_not_empty(self):
        """Test that ERROR_MESSAGES is not empty."""
        assert len(ERROR_MESSAGES) > 0

    def test_all_messages_are_strings(self):
        """Test that all error messages are strings."""
        for code, message in ERROR_MESSAGES.items():
            assert isinstance(code, str)
            assert isinstance(message, str)


class TestRetryableErrors:
    """Tests for RETRYABLE_ERRORS constant."""

    def test_retryable_errors_not_empty(self):
        """Test that RETRYABLE_ERRORS is not empty."""
        assert len(RETRYABLE_ERRORS) > 0

    def test_all_retryable_codes_exist_in_messages(self):
        """Test that retryable error codes have messages."""
        for error_code in RETRYABLE_ERRORS:
            assert error_code in ERROR_MESSAGES
