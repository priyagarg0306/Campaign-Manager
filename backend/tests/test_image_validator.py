"""
Tests for image validation utilities.
"""
import pytest
from unittest.mock import patch, MagicMock
import requests

from app.utils.image_validator import (
    validate_aspect_ratio,
    validate_image_dimensions,
    get_image_dimensions_from_bytes,
    validate_image_from_url,
    validate_campaign_images,
    get_image_requirements,
    suggest_image_type,
    IMAGE_REQUIREMENTS,
    SUPPORTED_MIME_TYPES,
)


class TestValidateAspectRatio:
    """Tests for validate_aspect_ratio function."""

    def test_valid_landscape_ratio(self):
        """Test valid landscape aspect ratio (1.91:1)."""
        is_valid, error = validate_aspect_ratio(1910, 1000, 'landscape')
        assert is_valid is True
        assert error is None

    def test_valid_square_ratio(self):
        """Test valid square aspect ratio (1:1)."""
        is_valid, error = validate_aspect_ratio(500, 500, 'square')
        assert is_valid is True
        assert error is None

    def test_valid_logo_ratio(self):
        """Test valid logo aspect ratio (1:1)."""
        is_valid, error = validate_aspect_ratio(256, 256, 'logo')
        assert is_valid is True
        assert error is None

    def test_valid_logo_landscape_ratio(self):
        """Test valid logo landscape aspect ratio (4:1)."""
        is_valid, error = validate_aspect_ratio(800, 200, 'logo_landscape')
        assert is_valid is True
        assert error is None

    def test_invalid_landscape_ratio(self):
        """Test invalid landscape aspect ratio."""
        is_valid, error = validate_aspect_ratio(500, 500, 'landscape')
        assert is_valid is False
        assert 'aspect ratio' in error.lower()

    def test_invalid_square_ratio(self):
        """Test invalid square aspect ratio."""
        is_valid, error = validate_aspect_ratio(800, 400, 'square')
        assert is_valid is False
        assert 'aspect ratio' in error.lower()

    def test_unknown_image_type(self):
        """Test with unknown image type."""
        is_valid, error = validate_aspect_ratio(500, 500, 'unknown_type')
        assert is_valid is False
        assert 'unknown image type' in error.lower()

    def test_zero_dimensions(self):
        """Test with zero dimensions."""
        is_valid, error = validate_aspect_ratio(0, 500, 'square')
        assert is_valid is False
        assert 'invalid' in error.lower()

    def test_negative_dimensions(self):
        """Test with negative dimensions."""
        is_valid, error = validate_aspect_ratio(-100, 500, 'square')
        assert is_valid is False
        assert 'invalid' in error.lower()


class TestValidateImageDimensions:
    """Tests for validate_image_dimensions function."""

    def test_valid_landscape_dimensions(self):
        """Test valid landscape dimensions (min 600x314)."""
        is_valid, error = validate_image_dimensions(800, 420, 'landscape')
        assert is_valid is True
        assert error is None

    def test_valid_square_dimensions(self):
        """Test valid square dimensions (min 300x300)."""
        is_valid, error = validate_image_dimensions(500, 500, 'square')
        assert is_valid is True
        assert error is None

    def test_valid_logo_dimensions(self):
        """Test valid logo dimensions (min 128x128)."""
        is_valid, error = validate_image_dimensions(256, 256, 'logo')
        assert is_valid is True
        assert error is None

    def test_width_too_small(self):
        """Test with width below minimum."""
        is_valid, error = validate_image_dimensions(400, 420, 'landscape')
        assert is_valid is False
        assert 'width' in error.lower()
        assert '600' in error

    def test_height_too_small(self):
        """Test with height below minimum."""
        is_valid, error = validate_image_dimensions(800, 200, 'landscape')
        assert is_valid is False
        assert 'height' in error.lower()
        assert '314' in error

    def test_unknown_image_type(self):
        """Test with unknown image type."""
        is_valid, error = validate_image_dimensions(500, 500, 'unknown_type')
        assert is_valid is False
        assert 'unknown image type' in error.lower()


class TestGetImageDimensionsFromBytes:
    """Tests for get_image_dimensions_from_bytes function."""

    def test_png_image(self):
        """Test getting dimensions from PNG bytes."""
        # Minimal valid PNG header with IHDR chunk
        # PNG signature + IHDR chunk header + width (100) + height (50)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'  # PNG signature
            b'\x00\x00\x00\x0d'  # IHDR chunk length (13)
            b'IHDR'  # IHDR chunk type
            b'\x00\x00\x00\x64'  # Width: 100
            b'\x00\x00\x00\x32'  # Height: 50
            b'\x08\x02'  # Bit depth, color type
            b'\x00\x00\x00'  # Compression, filter, interlace
        )
        result = get_image_dimensions_from_bytes(png_bytes)
        assert result is not None
        assert result['width'] == 100
        assert result['height'] == 50

    def test_gif_image(self):
        """Test getting dimensions from GIF bytes."""
        # GIF89a header with logical screen descriptor (min 24 bytes required)
        gif_bytes = (
            b'GIF89a'  # GIF signature (6 bytes)
            b'\x64\x00'  # Width: 100 (little-endian)
            b'\x32\x00'  # Height: 50 (little-endian)
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # Padding to 24 bytes
        )
        result = get_image_dimensions_from_bytes(gif_bytes)
        assert result is not None
        assert result['width'] == 100
        assert result['height'] == 50

    def test_gif87a_image(self):
        """Test getting dimensions from GIF87a bytes."""
        # GIF87a header (min 24 bytes required)
        gif_bytes = (
            b'GIF87a'  # GIF87a signature (6 bytes)
            b'\xc8\x00'  # Width: 200 (little-endian)
            b'\x64\x00'  # Height: 100 (little-endian)
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # Padding to 24 bytes
        )
        result = get_image_dimensions_from_bytes(gif_bytes)
        assert result is not None
        assert result['width'] == 200
        assert result['height'] == 100

    def test_too_short_bytes(self):
        """Test with bytes too short to determine dimensions."""
        result = get_image_dimensions_from_bytes(b'\x89PNG')
        assert result is None

    def test_invalid_format(self):
        """Test with invalid/unknown image format."""
        result = get_image_dimensions_from_bytes(b'Not a real image file')
        assert result is None


class TestValidateImageFromUrl:
    """Tests for validate_image_from_url function."""

    def test_empty_url(self):
        """Test with empty URL."""
        result = validate_image_from_url('', 'landscape')
        assert result['valid'] is False
        assert 'required' in result['errors'][0].lower()

    def test_unknown_image_type(self):
        """Test with unknown image type."""
        result = validate_image_from_url('https://example.com/image.jpg', 'unknown_type')
        assert result['valid'] is False
        assert 'unknown image type' in result['errors'][0].lower()

    @patch('app.utils.image_validator.requests.get')
    def test_valid_image(self, mock_get):
        """Test with valid image response."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/png'}
        # Create a minimal PNG
        mock_response.content = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\x0d'
            b'IHDR'
            b'\x00\x00\x02\x58'  # Width: 600
            b'\x00\x00\x01\x3a'  # Height: 314
            b'\x08\x02\x00\x00\x00'
        )
        mock_get.return_value = mock_response

        result = validate_image_from_url('https://example.com/image.png', 'landscape')
        assert result['dimensions'] is not None
        assert result['dimensions']['width'] == 600

    @patch('app.utils.image_validator.requests.get')
    def test_timeout_error(self, mock_get):
        """Test handling of timeout error."""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = validate_image_from_url('https://example.com/image.jpg', 'landscape')
        assert result['valid'] is False
        assert any('timed out' in error.lower() for error in result['errors'])

    @patch('app.utils.image_validator.requests.get')
    def test_request_error(self, mock_get):
        """Test handling of request error."""
        mock_get.side_effect = requests.exceptions.RequestException('Connection failed')

        result = validate_image_from_url('https://example.com/image.jpg', 'landscape')
        assert result['valid'] is False
        assert any('failed to download' in error.lower() for error in result['errors'])

    @patch('app.utils.image_validator.requests.get')
    def test_unsupported_format(self, mock_get):
        """Test with unsupported image format."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = validate_image_from_url('https://example.com/doc.pdf', 'landscape')
        assert result['valid'] is False
        assert any('unsupported' in error.lower() for error in result['errors'])

    @patch('app.utils.image_validator.requests.get')
    def test_file_size_too_large(self, mock_get):
        """Test with file size exceeding limit."""
        mock_response = MagicMock()
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': str(10 * 1024 * 1024)  # 10MB
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = validate_image_from_url('https://example.com/large.jpg', 'landscape')
        assert result['valid'] is False
        assert any('file size' in error.lower() for error in result['errors'])


class TestValidateCampaignImages:
    """Tests for validate_campaign_images function."""

    def test_empty_images(self):
        """Test with empty images dict."""
        result = validate_campaign_images(None)
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_no_urls_provided(self):
        """Test with empty images dict."""
        result = validate_campaign_images({})
        assert result['valid'] is True

    @patch('app.utils.image_validator.validate_image_from_url')
    def test_valid_landscape_image(self, mock_validate):
        """Test with valid landscape image."""
        mock_validate.return_value = {'valid': True, 'errors': [], 'dimensions': {'width': 800, 'height': 420}}

        result = validate_campaign_images({'landscape_url': 'https://example.com/landscape.jpg'})
        assert result['valid'] is True
        mock_validate.assert_called_once()

    @patch('app.utils.image_validator.validate_image_from_url')
    def test_invalid_image(self, mock_validate):
        """Test with invalid image."""
        mock_validate.return_value = {'valid': False, 'errors': ['Image too small']}

        result = validate_campaign_images({'landscape_url': 'https://example.com/small.jpg'})
        assert result['valid'] is False
        assert len(result['errors']) > 0

    @patch('app.utils.image_validator.validate_image_from_url')
    def test_multiple_images(self, mock_validate):
        """Test with multiple images."""
        mock_validate.return_value = {'valid': True, 'errors': []}

        images = {
            'landscape_url': 'https://example.com/landscape.jpg',
            'square_url': 'https://example.com/square.jpg',
            'logo_url': 'https://example.com/logo.jpg',
        }
        result = validate_campaign_images(images)

        assert mock_validate.call_count == 3
        assert result['valid'] is True


class TestGetImageRequirements:
    """Tests for get_image_requirements function."""

    def test_get_landscape_requirements(self):
        """Test getting landscape requirements."""
        requirements = get_image_requirements('landscape')
        assert requirements is not None
        assert 'ratio' in requirements
        assert 'min_width' in requirements
        assert 'min_height' in requirements

    def test_get_square_requirements(self):
        """Test getting square requirements."""
        requirements = get_image_requirements('square')
        assert requirements is not None
        assert requirements['ratio'] == 1.0

    def test_get_unknown_type(self):
        """Test getting requirements for unknown type."""
        requirements = get_image_requirements('unknown_type')
        assert requirements is None


class TestSuggestImageType:
    """Tests for suggest_image_type function."""

    def test_suggest_landscape(self):
        """Test suggesting landscape for 1.91:1 ratio."""
        suggestion = suggest_image_type(1910, 1000)
        assert suggestion == 'landscape'

    def test_suggest_square(self):
        """Test suggesting square for 1:1 ratio."""
        suggestion = suggest_image_type(500, 500)
        assert suggestion == 'square'

    def test_suggest_logo(self):
        """Test suggesting logo for small 1:1 image."""
        suggestion = suggest_image_type(150, 150)
        assert suggestion == 'logo'

    def test_suggest_logo_landscape(self):
        """Test suggesting logo_landscape for 4:1 ratio."""
        suggestion = suggest_image_type(600, 150)
        assert suggestion == 'logo_landscape'

    def test_no_suggestion_invalid_dimensions(self):
        """Test no suggestion for invalid dimensions."""
        suggestion = suggest_image_type(0, 0)
        assert suggestion is None

    def test_no_suggestion_negative_dimensions(self):
        """Test no suggestion for negative dimensions."""
        suggestion = suggest_image_type(-100, 100)
        assert suggestion is None

    def test_no_suggestion_unusual_ratio(self):
        """Test no suggestion for unusual ratio that doesn't match any type."""
        suggestion = suggest_image_type(100, 500)  # 0.2:1 ratio - doesn't match any
        assert suggestion is None


class TestImageRequirementsConstant:
    """Tests for IMAGE_REQUIREMENTS constant."""

    def test_requirements_not_empty(self):
        """Test that IMAGE_REQUIREMENTS is not empty."""
        assert len(IMAGE_REQUIREMENTS) > 0

    def test_all_image_types_have_required_fields(self):
        """Test that all image types have required fields."""
        required_fields = ['ratio', 'ratio_tolerance', 'min_width', 'min_height', 'max_file_size']
        for image_type, requirements in IMAGE_REQUIREMENTS.items():
            for field in required_fields:
                assert field in requirements, f"Missing {field} for {image_type}"


class TestSupportedMimeTypes:
    """Tests for SUPPORTED_MIME_TYPES constant."""

    def test_supported_types_not_empty(self):
        """Test that SUPPORTED_MIME_TYPES is not empty."""
        assert len(SUPPORTED_MIME_TYPES) > 0

    def test_common_image_types_supported(self):
        """Test that common image types are supported."""
        assert 'image/jpeg' in SUPPORTED_MIME_TYPES
        assert 'image/png' in SUPPORTED_MIME_TYPES
        assert 'image/gif' in SUPPORTED_MIME_TYPES
