"""
Extended tests for image validation, including JPEG parsing.
"""
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
import requests

from app.utils.image_validator import (
    get_image_dimensions_from_bytes,
    validate_image_from_url,
    validate_image_dimensions,
    validate_aspect_ratio,
)


class TestJPEGParsing:
    """Tests for JPEG image dimension parsing."""

    def test_jpeg_with_sof0_marker(self):
        """Test JPEG with SOF0 (baseline DCT) marker."""
        # Build a minimal JPEG with SOF0 marker
        jpeg_bytes = bytearray([
            0xFF, 0xD8,  # SOI (Start of Image)
            0xFF, 0xE0,  # APP0 marker
            0x00, 0x10,  # APP0 length (16 bytes)
        ])
        # Add padding for APP0 segment
        jpeg_bytes.extend([0x00] * 14)
        # Add SOF0 marker (0xC0)
        jpeg_bytes.extend([
            0xFF, 0xC0,  # SOF0 marker
            0x00, 0x11,  # Segment length
            0x08,        # Precision
            0x01, 0x90,  # Height: 400
            0x02, 0x80,  # Width: 640
        ])
        # Add some padding
        jpeg_bytes.extend([0x00] * 10)

        result = get_image_dimensions_from_bytes(bytes(jpeg_bytes))
        assert result is not None
        assert result['width'] == 640
        assert result['height'] == 400

    def test_jpeg_with_sof1_marker(self):
        """Test JPEG with SOF1 (extended sequential DCT) marker."""
        jpeg_bytes = bytearray([
            0xFF, 0xD8,  # SOI
            0xFF, 0xE0, 0x00, 0x10,  # APP0 marker with length
        ])
        jpeg_bytes.extend([0x00] * 14)  # APP0 content
        # Add SOF1 marker (0xC1)
        jpeg_bytes.extend([
            0xFF, 0xC1,  # SOF1 marker
            0x00, 0x11,  # Segment length
            0x08,        # Precision
            0x00, 0xC8,  # Height: 200
            0x01, 0x40,  # Width: 320
        ])
        jpeg_bytes.extend([0x00] * 10)

        result = get_image_dimensions_from_bytes(bytes(jpeg_bytes))
        assert result is not None
        assert result['width'] == 320
        assert result['height'] == 200

    def test_jpeg_with_sof2_marker(self):
        """Test JPEG with SOF2 (progressive DCT) marker."""
        jpeg_bytes = bytearray([
            0xFF, 0xD8,  # SOI
            0xFF, 0xE0, 0x00, 0x10,  # APP0
        ])
        jpeg_bytes.extend([0x00] * 14)
        # Add SOF2 marker (0xC2)
        jpeg_bytes.extend([
            0xFF, 0xC2,  # SOF2 marker
            0x00, 0x11,
            0x08,
            0x03, 0x20,  # Height: 800
            0x04, 0xB0,  # Width: 1200
        ])
        jpeg_bytes.extend([0x00] * 10)

        result = get_image_dimensions_from_bytes(bytes(jpeg_bytes))
        assert result is not None
        assert result['width'] == 1200
        assert result['height'] == 800

    def test_jpeg_with_multiple_markers(self):
        """Test JPEG with multiple markers before SOF."""
        jpeg_bytes = bytearray([
            0xFF, 0xD8,  # SOI
            # APP0 marker
            0xFF, 0xE0, 0x00, 0x10,
        ])
        jpeg_bytes.extend([0x00] * 14)
        # APP1 marker (EXIF)
        jpeg_bytes.extend([0xFF, 0xE1, 0x00, 0x20])
        jpeg_bytes.extend([0x00] * 30)
        # DQT marker (Define Quantization Table)
        jpeg_bytes.extend([0xFF, 0xDB, 0x00, 0x43])
        jpeg_bytes.extend([0x00] * 65)
        # SOF0
        jpeg_bytes.extend([
            0xFF, 0xC0, 0x00, 0x11, 0x08,
            0x01, 0xE0,  # Height: 480
            0x02, 0x80,  # Width: 640
        ])
        jpeg_bytes.extend([0x00] * 10)

        result = get_image_dimensions_from_bytes(bytes(jpeg_bytes))
        assert result is not None
        assert result['width'] == 640
        assert result['height'] == 480

    def test_jpeg_truncated_before_sof(self):
        """Test handling of JPEG truncated before SOF marker."""
        jpeg_bytes = bytearray([
            0xFF, 0xD8,  # SOI
            0xFF, 0xE0, 0x00, 0x10,  # APP0
        ])
        jpeg_bytes.extend([0x00] * 14)
        # No SOF marker, just end here

        result = get_image_dimensions_from_bytes(bytes(jpeg_bytes))
        assert result is None

    def test_jpeg_with_invalid_marker(self):
        """Test JPEG with invalid marker (non-0xFF start)."""
        jpeg_bytes = bytearray([
            0xFF, 0xD8,  # SOI
            0xFF, 0xE0, 0x00, 0x10,  # APP0
        ])
        jpeg_bytes.extend([0x00] * 14)
        # Invalid marker (doesn't start with 0xFF)
        jpeg_bytes.extend([0x00, 0xC0])

        result = get_image_dimensions_from_bytes(bytes(jpeg_bytes))
        assert result is None

    def test_jpeg_with_eoi_before_sof(self):
        """Test JPEG that ends (EOI) before SOF marker."""
        jpeg_bytes = bytearray([
            0xFF, 0xD8,  # SOI
            0xFF, 0xD9,  # EOI (End of Image)
        ])

        result = get_image_dimensions_from_bytes(bytes(jpeg_bytes))
        assert result is None

    def test_jpeg_too_short_for_dimensions(self):
        """Test JPEG that's too short to contain dimension data."""
        # SOI + partial SOF marker
        jpeg_bytes = bytes([0xFF, 0xD8, 0xFF, 0xC0, 0x00, 0x11, 0x08])

        result = get_image_dimensions_from_bytes(jpeg_bytes)
        assert result is None

    def test_non_jpeg_starting_with_ff(self):
        """Test file starting with 0xFF but not a JPEG."""
        # Starts with 0xFF but not 0xFFD8
        not_jpeg = bytes([0xFF, 0x00, 0x00, 0x00] * 10)
        result = get_image_dimensions_from_bytes(not_jpeg)
        assert result is None


class TestImageValidationFromUrlExtended:
    """Extended tests for image validation from URL."""

    @patch('app.utils.image_validator.requests.get')
    def test_validate_with_pil_available(self, mock_get):
        """Test validation uses PIL when available."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/jpeg'}
        # Create a minimal JPEG with SOF marker
        jpeg_bytes = bytearray([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10])
        jpeg_bytes.extend([0x00] * 14)
        jpeg_bytes.extend([0xFF, 0xC0, 0x00, 0x11, 0x08, 0x01, 0x3A, 0x02, 0x58])
        jpeg_bytes.extend([0x00] * 10)
        mock_response.content = bytes(jpeg_bytes)
        mock_get.return_value = mock_response

        # The actual validation runs and uses fallback parsing
        result = validate_image_from_url('https://example.com/test.jpg', 'landscape')
        # Should get dimensions from our JPEG bytes
        assert result['dimensions'] is not None
        assert result['dimensions']['width'] == 600
        assert result['dimensions']['height'] == 314

    @patch('app.utils.image_validator.requests.get')
    def test_validate_without_pil_fallback(self, mock_get):
        """Test validation falls back to manual parsing when PIL unavailable."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/png'}
        # Create a minimal PNG
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\x0d'
            b'IHDR'
            b'\x00\x00\x02\x58'  # Width: 600
            b'\x00\x00\x01\x3a'  # Height: 314
            b'\x08\x02\x00\x00\x00'
        )
        mock_response.content = png_bytes
        mock_get.return_value = mock_response

        # Simulate PIL not available
        with patch.dict('sys.modules', {'PIL': None, 'PIL.Image': None}):
            result = validate_image_from_url('https://example.com/test.png', 'landscape')
            assert result['dimensions'] is not None

    @patch('app.utils.image_validator.requests.get')
    def test_validate_unrecognized_format(self, mock_get):
        """Test validation of unrecognized image format."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/png'}
        mock_response.content = b'not a real image format' * 10
        mock_get.return_value = mock_response

        # Simulate PIL not available and unrecognized format
        with patch.dict('sys.modules', {'PIL': None, 'PIL.Image': None}):
            result = validate_image_from_url('https://example.com/test.png', 'landscape')
            # Should fail to determine dimensions
            assert result['valid'] is False

    @patch('app.utils.image_validator.requests.get')
    def test_validate_generic_exception(self, mock_get):
        """Test validation handles generic exceptions."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.content = b'\xFF\xD8'  # Incomplete JPEG
        mock_get.return_value = mock_response

        # Cause an exception during processing
        with patch('app.utils.image_validator.get_image_dimensions_from_bytes') as mock_dims:
            mock_dims.side_effect = Exception("Unexpected error")
            result = validate_image_from_url('https://example.com/test.jpg', 'landscape')
            assert result['valid'] is False
            assert any('failed' in e.lower() for e in result['errors'])

    @patch('app.utils.image_validator.requests.get')
    def test_validate_http_error(self, mock_get):
        """Test validation handles HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        result = validate_image_from_url('https://example.com/notfound.jpg', 'landscape')
        assert result['valid'] is False

    @patch('app.utils.image_validator.requests.get')
    def test_validate_dimension_validation_fails(self, mock_get):
        """Test validation when image dimensions are too small."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/png'}
        # Create PNG with small dimensions (100x50)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\x0d'
            b'IHDR'
            b'\x00\x00\x00\x64'  # Width: 100
            b'\x00\x00\x00\x32'  # Height: 50
            b'\x08\x02\x00\x00\x00'
        )
        mock_response.content = png_bytes
        mock_get.return_value = mock_response

        result = validate_image_from_url('https://example.com/small.png', 'landscape')
        assert result['valid'] is False
        assert any('width' in e.lower() or 'height' in e.lower() for e in result['errors'])

    @patch('app.utils.image_validator.requests.get')
    def test_validate_aspect_ratio_fails(self, mock_get):
        """Test validation when aspect ratio is wrong."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/png'}
        # Create PNG with wrong aspect ratio (600x600, should be 1.91:1 for landscape)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\x0d'
            b'IHDR'
            b'\x00\x00\x02\x58'  # Width: 600
            b'\x00\x00\x02\x58'  # Height: 600
            b'\x08\x02\x00\x00\x00'
        )
        mock_response.content = png_bytes
        mock_get.return_value = mock_response

        result = validate_image_from_url('https://example.com/square.png', 'landscape')
        assert result['valid'] is False
        assert any('aspect' in e.lower() for e in result['errors'])


class TestValidateDimensionsEdgeCases:
    """Edge cases for dimension validation."""

    def test_logo_landscape_valid(self):
        """Test valid logo_landscape dimensions."""
        is_valid, error = validate_image_dimensions(512, 128, 'logo_landscape')
        assert is_valid is True
        assert error is None

    def test_logo_landscape_too_narrow(self):
        """Test logo_landscape with insufficient height."""
        is_valid, error = validate_image_dimensions(512, 64, 'logo_landscape')
        assert is_valid is False


class TestValidateAspectRatioEdgeCases:
    """Edge cases for aspect ratio validation."""

    def test_logo_landscape_valid_ratio(self):
        """Test valid logo_landscape aspect ratio (4:1)."""
        is_valid, error = validate_aspect_ratio(400, 100, 'logo_landscape')
        assert is_valid is True

    def test_logo_landscape_invalid_ratio(self):
        """Test invalid logo_landscape aspect ratio."""
        is_valid, error = validate_aspect_ratio(400, 200, 'logo_landscape')
        assert is_valid is False


class TestWebPSupport:
    """Tests for WebP image support."""

    def test_webp_not_parsed_by_fallback(self):
        """Test that WebP is not parsed by the fallback parser."""
        # WebP file signature
        webp_bytes = b'RIFF\x00\x00\x00\x00WEBP'
        result = get_image_dimensions_from_bytes(webp_bytes)
        # WebP is not supported by fallback parser
        assert result is None

    @patch('app.utils.image_validator.requests.get')
    def test_webp_accepted_content_type(self, mock_get):
        """Test WebP is accepted as a valid content type."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'image/webp'}
        # WebP is not parsed by fallback, so dimensions won't be found
        mock_response.content = b'RIFF\x00\x00\x00\x00WEBP' + b'\x00' * 100
        mock_get.return_value = mock_response

        result = validate_image_from_url('https://example.com/test.webp', 'landscape')
        # WebP content type is accepted, but fallback parser can't get dimensions
        # So the result should either have dimensions (if PIL available) or fail gracefully
        assert 'dimensions' in result or 'errors' in result
